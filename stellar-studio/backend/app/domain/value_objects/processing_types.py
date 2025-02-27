#app/domain/value_objects/processing_types.py
from enum import Enum

class ProcessingStepType(str, Enum):
    CALIBRATION = "CALIBRATION"
    STACKING = "STACKING"
    STRETCHING = "STRETCHING"
    COLOR_BALANCE = "COLOR_BALANCE"
    NOISE_REDUCTION = "NOISE_REDUCTION"
    SHARPENING = "SHARPENING"
    DECONVOLUTION = "DECONVOLUTION"

class ProcessingStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"