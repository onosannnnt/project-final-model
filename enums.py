from enum import Enum


class UserType(str, Enum):
    EL = "EL"
    RV = "RV"
    CE = "CE"


class WeatherType(str, Enum):
    SUNNY = "sunny"
    RAINY = "rainy"
    AUTUMN = "autumn"
