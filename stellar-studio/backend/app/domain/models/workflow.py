# app/domain/models/workflow.py
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class ProcessingStepType(Enum):
    CALIBRATION = "calibration"
    STACKING = "stacking"
    STRETCHING = "stretching"
    COLOR_BALANCE = "color_balance"
    NOISE_REDUCTION = "noise_reduction"
    SHARPENING = "sharpening"
    DECONVOLUTION = "deconvolution"

@dataclass
class ProcessingStep:
    type: ProcessingStepType
    order: int
    parameters: Dict[str, Any]
    description: str

@dataclass
class Workflow:
    id: str
    name: str
    description: str
    steps: List[ProcessingStep]
    is_default: bool
    target_type: str  # Type d'objet céleste (nébuleuse, galaxie, etc.)
    required_filters: List[str]  # Filtres nécessaires pour ce workflow
