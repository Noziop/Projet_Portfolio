# app/domain/value_objects/observation_types.py
from enum import Enum

class InstrumentType(str, Enum):
    CAMERA = "CAMERA"
    SPECTROGRAPH = "SPECTROGRAPH"
    PHOTOMETER = "PHOTOMETER"
    
class FilterType(str, Enum):
    H_ALPHA = "H_ALPHA"
    OIII = "OIII"
    SII = "SII"
    RGB = "RGB"
    LUMINANCE = "L"
