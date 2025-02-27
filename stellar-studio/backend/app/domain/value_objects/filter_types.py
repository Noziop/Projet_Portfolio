#app/domain/value_objects/filter_types.py
from enum import Enum

class FilterType(str, Enum):
    NARROWBAND = "NARROWBAND"
    BROADBAND = "BROADBAND"
    PHOTOMETRIC = "PHOTOMETRIC"
    POLARIZING = "POLARIZING"
    OTHER = "OTHER"
