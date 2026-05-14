import json
import os

import numpy as np
import pandas as pd

LOW_HP_THRESHOLD = 0.30
HIGH_FRENZY_THRESHOLD = 5

# ------------------------------------
# Load skill metadata from new_skills.json
# ------------------------------------
_SKILLS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "new_skills.json"
)
_SKILL_META: dict = {}
if os.path.exists(_SKILLS_PATH):
    with open(_SKILLS_PATH, "r", encoding="utf-8") as _f:
        _raw = json.load(_f)

    # Build int-keyed lookup: id -> skill dict
    for _cls, _slist in _raw.get("skill_metadata", {}).items():
        for _sk in _slist:
            _SKILL_META[int(_sk["id"])] = _sk


def _get_skill(skill_id) -> dict:
    """Return skill dict for a given skill_id (int or float). Empty dict if not found."""
    if pd.isna(skill_id):
        return {}
    try:
        return _SKILL_META.get(int(skill_id), {})
    except (ValueError, TypeError):
        return {}


# ------------------------------
# Helper Functions
# ------------------------------
def safe_div(a, b):
    return a / b if b not in [0, None] and not pd.isna(b) else 0


def get_skill_prefix(skill_id):
    """Return class prefix (CE/EL/RV/OTHER) using player_skill_type from skill metadata."""
    sk = _get_skill(skill_id)
    if not sk:
        return "OTHER"
    pst = sk.get("player_skill_type", "").upper()
    if pst in ("CE", "EL", "RV"):
        return pst
    return "OTHER"


def get_skill_target_type(skill_target):
    if pd.isna(skill_target):
        return "Unknown"

    target = str(skill_target)

    if target.startswith("ALL"):
        return "AoE"

    return "Single"


def is_ce_weather_match(skill_id, weather):
    """Check if a CE skill matches the current weather, using metadata type lookup."""
    sk = _get_skill(skill_id)
    if not sk:
        return 0

    if sk.get("player_skill_type", "").lower() != "ce":
        return 0

    skill_type = sk.get("type", "")
    weather = str(weather).lower()

    if skill_type == "Atk":
        return int(weather == "sunny")

    if skill_type in ["Buff", "Debuff"]:
        return int(weather == "autumn")

    if skill_type == "Heal/Def":
        return int(weather == "rainy")

    return 0


# ------------------------------
# Feature Engineering
# ------------------------------
def build_features(raw_df):
    df = raw_df.copy()

    # ------------------------------
    # Basic Ratios
    # ------------------------------
    df["avg_hp_ratio"] = (df["caster_current_hp"] / df["caster_max_hp"]).fillna(0)

    df["actor_hp_ratio"] = df["avg_hp_ratio"]

    df["target_hp_percent"] = (df["target_current_hp"] / df["target_max_hp"]).fillna(0)

    df["damage_taken_ratio"] = df.apply(
        lambda r: safe_div(r["damage_recieve"], r["damage_dealt"]),
        axis=1,
    )

    df["blood_risk_ratio"] = (df["corrupt_blood_by_max_hp"] / 100).fillna(0)

    df["sp_used_percent"] = (
        df.groupby("session_id")["caster_current_sp"].pct_change().abs().fillna(0)
    )

    df["hp_used"] = (
        df.groupby(["session_id", "character_id"])["caster_current_hp"]
        .diff()
        .abs()
        .fillna(0)
    )

    df["hp_used_percent"] = (df["hp_used"] / df["caster_max_hp"]).fillna(0)

    # ------------------------------
    # Damage Features
    # ------------------------------
    dmg_stats = (
        df.groupby(["session_id", "character_id"])["damage_dealt"]
        .agg(["mean", "var", "max", "min", "sum"])
        .reset_index()
    )

    dmg_stats.columns = [
        "session_id",
        "character_id",
        "avg_damage",
        "damage_variance",
        "max_damage_single_hit",
        "min_damage",
        "damage_dealt_total",
    ]

    df = df.merge(dmg_stats, on=["session_id", "character_id"], how="left")

    df["damage_cv"] = df.apply(
        lambda r: safe_div(np.sqrt(r["damage_variance"]), r["avg_damage"]),
        axis=1,
    )

    df["damage_spike"] = df["max_damage_single_hit"] - df["avg_damage"]

    df["damage_spike_ratio"] = df.apply(
        lambda r: safe_div(r["damage_spike"], r["avg_damage"]),
        axis=1,
    )

    df["damage_max_min_ratio"] = df.apply(
        lambda r: safe_div(r["max_damage_single_hit"], r["min_damage"]),
        axis=1,
    )

    df["overkill_damage"] = (df["damage_dealt"] - df["target_current_hp"]).clip(lower=0)

    # ------------------------------
    # Frenzy Features
    # ------------------------------
    frenzy_stats = (
        df.groupby(["session_id", "character_id"])["current_frenzy_stack"]
        .agg(["mean", "max"])
        .reset_index()
    )

    frenzy_stats.columns = [
        "session_id",
        "character_id",
        "avg_frenzy",
        "max_frenzy",
    ]

    df = df.merge(frenzy_stats, on=["session_id", "character_id"], how="left")

    df["high_frenzy_turn"] = (
        df["current_frenzy_stack"] >= HIGH_FRENZY_THRESHOLD
    ).astype(int)

    frenzy_turn_ratio = (
        df.groupby(["session_id", "character_id"])["high_frenzy_turn"]
        .mean()
        .reset_index(name="high_frenzy_turn_ratio")
    )

    df = df.merge(
        frenzy_turn_ratio,
        on=["session_id", "character_id"],
        how="left",
    )

    # ------------------------------
    # Blood Features
    # ------------------------------
    blood_stats = (
        df.groupby(["session_id", "character_id"])["current_corrupt_blood_gain"]
        .mean()
        .reset_index(name="avg_corrupt_blood")
    )

    df = df.merge(
        blood_stats,
        on=["session_id", "character_id"],
        how="left",
    )

    df["current_corrupt_blood"] = df["current_corrupt_blood_gain"]

    # ------------------------------
    # HP Risk Features
    # ------------------------------
    df["low_hp_turn"] = (df["avg_hp_ratio"] <= LOW_HP_THRESHOLD).astype(int)

    low_hp_ratio = (
        df.groupby(["session_id", "character_id"])["low_hp_turn"]
        .mean()
        .reset_index(name="low_hp_turn_ratio")
    )

    df = df.merge(
        low_hp_ratio,
        on=["session_id", "character_id"],
        how="left",
    )

    # ------------------------------
    # Skill Usage Features
    # ------------------------------
    skill_count = (
        df.groupby(["session_id", "character_id"])["skill_id"]
        .nunique()
        .reset_index(name="unique_skills_used")
    )

    df = df.merge(skill_count, on=["session_id", "character_id"], how="left")

    entropy_rows = []

    for (sess, char), grp in df.groupby(["session_id", "character_id"]):
        probs = grp["skill_id"].value_counts(normalize=True)

        entropy = -(probs * np.log2(probs + 1e-9)).sum()
        most_used_ratio = probs.max()

        entropy_rows.append(
            {
                "session_id": sess,
                "character_id": char,
                "skill_entropy": entropy,
                "most_used_skill_ratio": most_used_ratio,
            }
        )

    entropy_df = pd.DataFrame(entropy_rows)

    df = df.merge(
        entropy_df,
        on=["session_id", "character_id"],
        how="left",
    )

    df["skill_prefix"] = df["skill_id"].apply(get_skill_prefix)

    df["ce_used"] = (df["skill_prefix"] == "CE").astype(int)
    df["el_used"] = (df["skill_prefix"] == "EL").astype(int)
    df["rv_used"] = (df["skill_prefix"] == "RV").astype(int)

    ce_skill_used = (
        df.groupby(["session_id", "character_id"])["ce_used"]
        .sum()
        .reset_index(name="ce_skill_used")
    )

    el_skill_used = (
        df.groupby(["session_id", "character_id"])["el_used"]
        .sum()
        .reset_index(name="el_skill_used")
    )

    rv_skill_used = (
        df.groupby(["session_id", "character_id"])["rv_used"]
        .sum()
        .reset_index(name="rv_skill_used")
    )

    df = df.merge(
        ce_skill_used,
        on=["session_id", "character_id"],
        how="left",
    )

    df = df.merge(
        el_skill_used,
        on=["session_id", "character_id"],
        how="left",
    )

    df = df.merge(
        rv_skill_used,
        on=["session_id", "character_id"],
        how="left",
    )

    # ------------------------------
    # Weather Features
    # ------------------------------
    df["ce_weather_match"] = df.apply(
        lambda r: is_ce_weather_match(r["skill_id"], r["weather"]),
        axis=1,
    )

    ce_weather_ratio = (
        df.groupby(["session_id", "character_id"])["ce_weather_match"]
        .mean()
        .reset_index(name="ce_weather_match_ratio")
    )

    df = df.merge(
        ce_weather_ratio,
        on=["session_id", "character_id"],
        how="left",
    )

    df["ce_weather_match_used"] = df["ce_weather_match"]

    # ------------------------------
    # Momentum Features
    # ------------------------------
    df["momentum_efficiency"] = df.apply(
        lambda r: safe_div(r["damage_dealt"], r["momentum_used"]),
        axis=1,
    )

    # ------------------------------
    # Heal Features
    # ------------------------------
    df["is_heal"] = (df["heal_amount"] > 0).astype(int)

    df["heal_ratio"] = df.apply(
        lambda r: safe_div(r["heal_amount"], r["damage_recieve"]),
        axis=1,
    )

    heal_receive = (
        df.groupby(["session_id", "skill_target"])["heal_amount"]
        .sum()
        .reset_index(name="heal_recieve")
    )

    heal_receive.rename(columns={"skill_target": "character_id"}, inplace=True)

    df = df.merge(
        heal_receive,
        on=["session_id", "character_id"],
        how="left",
    )

    df["heal_recieve"] = df["heal_recieve"].fillna(0)

    # ------------------------------
    # Kill / Critical Features
    # ------------------------------
    df["is_kill"] = ((df["target_current_hp"] - df["damage_dealt"]) <= 0).astype(int)

    df["kill_amount"] = df["is_kill"]

    crit_threshold = df["avg_damage"] + np.sqrt(df["damage_variance"].fillna(0))

    df["is_critical_damage"] = (df["damage_dealt"] >= crit_threshold).astype(int)

    # ------------------------------
    # Turn Features
    # ------------------------------
    df["early_turn"] = (df["turn_index"] <= 3).astype(int)

    # ------------------------------
    # Target Features
    # ------------------------------
    df["skill_target_type"] = df["skill_target"].apply(get_skill_target_type)

    # ------------------------------
    # Team Features
    # ------------------------------
    team_stats = (
        df.groupby("session_id")
        .agg(
            team_damage_dealt=("damage_dealt", "sum"),
            team_damage_recieve=("damage_recieve", "sum"),
            team_momentum_used=("momentum_used", "sum"),
            team_avg_frenzy=("current_frenzy_stack", "mean"),
            team_skill_entropy=("skill_entropy", "mean"),
        )
        .reset_index()
    )

    df = df.merge(team_stats, on="session_id", how="left")

    # ------------------------------
    # Carry Ratio
    # ------------------------------
    carry_stats = []

    for sess, grp in df.groupby("session_id"):
        total_damage = grp["damage_dealt"].sum()

        char_damage = grp.groupby("character_id")["damage_dealt"].sum().to_dict()

        carry_stats.append(
            {
                "session_id": sess,
                "char_1_carry_ratio": safe_div(
                    char_damage.get(1, 0),
                    total_damage,
                ),
                "char_2_carry_ratio": safe_div(
                    char_damage.get(2, 0),
                    total_damage,
                ),
            }
        )

    carry_df = pd.DataFrame(carry_stats)

    df = df.merge(carry_df, on="session_id", how="left")

    # ------------------------------
    # Session-Level Aggregation
    # ------------------------------
    aggregation_dict = {
        "damage_dealt": "sum",
        "damage_recieve": "sum",
        "avg_damage": "mean",
        "damage_variance": "mean",
        "damage_cv": "mean",
        "max_damage_single_hit": "max",
        "damage_spike": "mean",
        "damage_spike_ratio": "mean",
        "damage_max_min_ratio": "mean",
        "damage_taken_ratio": "mean",
        "overkill_damage": "sum",
        "avg_hp_ratio": "mean",
        "low_hp_turn": "sum",
        "low_hp_turn_ratio": "mean",
        "avg_frenzy": "mean",
        "max_frenzy": "max",
        "high_frenzy_turn": "sum",
        "high_frenzy_turn_ratio": "mean",
        "avg_corrupt_blood": "mean",
        "current_corrupt_blood": "max",
        "corrupt_blood_by_max_hp": "mean",
        "blood_risk_ratio": "mean",
        "unique_skills_used": "max",
        "skill_entropy": "mean",
        "most_used_skill_ratio": "mean",
        "ce_used": "sum",
        "el_used": "sum",
        "rv_used": "sum",
        "ce_skill_used": "max",
        "el_skill_used": "max",
        "rv_skill_used": "max",
        "ce_weather_match": "sum",
        "ce_weather_match_used": "sum",
        "ce_weather_match_ratio": "mean",
        "momentum_used": "sum",
        "momentum_efficiency": "mean",
        "heal_amount": "sum",
        "heal_recieve": "sum",
        "heal_ratio": "mean",
        "is_heal": "sum",
        "is_kill": "sum",
        "kill_amount": "sum",
        "is_critical_damage": "sum",
        "early_turn": "sum",
        "break_count": "sum",
        "break_damage": "sum",
        "target_debuff_count": "mean",
        "caster_current_sp": "mean",
        "sp_used_percent": "mean",
        "hp_used": "sum",
        "hp_used_percent": "mean",
        "target_hp_percent": "mean",
        "team_damage_dealt": "max",
        "team_damage_recieve": "max",
        "team_momentum_used": "max",
        "team_avg_frenzy": "max",
        "team_skill_entropy": "max",
        "char_1_carry_ratio": "max",
        "char_2_carry_ratio": "max",
    }

    existing_agg = {k: v for k, v in aggregation_dict.items() if k in df.columns}

    session_df = df.groupby("session_id").agg(existing_agg).reset_index()
    if "session_id" in session_df.columns:
        # Ensure JSON-serializable session IDs.
        session_df["session_id"] = session_df["session_id"].astype(str)

    # ------------------------------
    # Final Selected Features
    # ------------------------------
    final_features = [
        "session_id",
        "damage_dealt",
        "avg_damage",
        "damage_variance",
        "damage_cv",
        "max_damage_single_hit",
        "damage_spike",
        "damage_spike_ratio",
        "damage_max_min_ratio",
        "damage_taken_ratio",
        "overkill_damage",
        "avg_hp_ratio",
        "low_hp_turn",
        "low_hp_turn_ratio",
        "damage_recieve",
        "caster_current_hp",
        "actor_hp_ratio",
        "avg_frenzy",
        "max_frenzy",
        "high_frenzy_turn",
        "high_frenzy_turn_ratio",
        "avg_corrupt_blood",
        "current_corrupt_blood",
        "corrupt_blood_by_max_hp",
        "blood_risk_ratio",
        "unique_skills_used",
        "skill_entropy",
        "most_used_skill_ratio",
        "ce_used",
        "el_used",
        "rv_used",
        "ce_skill_used",
        "el_skill_used",
        "rv_skill_used",
        "ce_weather_match",
        "ce_weather_match_used",
        "ce_weather_match_ratio",
        "momentum_used",
        "momentum_efficiency",
        "heal_amount",
        "heal_recieve",
        "heal_ratio",
        "is_heal",
        "is_kill",
        "kill_amount",
        "is_critical_damage",
        "early_turn",
        "break_count",
        "break_damage",
        "target_debuff_count",
        "debuff_hit_ratio",
        "caster_current_sp",
        "sp_used_percent",
        "hp_used",
        "hp_used_percent",
        "target_hp_percent",
        "target_current_hp",
        "target_max_hp",
        "team_damage_dealt",
        "team_damage_recieve",
        "team_momentum_used",
        "team_avg_frenzy",
        "team_skill_entropy",
        "char_1_carry_ratio",
        "char_2_carry_ratio",
    ]

    final_features = [col for col in final_features if col in session_df.columns]

    return session_df[final_features]


# ------------------------------
# Main
# ------------------------------
def run_pipeline(
    input_csv="combat_data.csv",
    output_csv="processed_features.csv",
):
    raw_df = pd.read_csv(input_csv)

    processed_df = build_features(raw_df)
    processed_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    processed_df.fillna(0, inplace=True)
    processed_df.to_csv(output_csv, index=False)

    print(f"Saved processed features to: {output_csv}")
    print(f"Shape: {processed_df.shape}")


if __name__ == "__main__":
    run_pipeline()
