from enum import Enum
from typing import List

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def get_default(cls) -> "ProcessingStatus":
        """État par défaut d'un nouveau job"""
        return cls.PENDING

    @classmethod
    def get_final_states(cls) -> set["ProcessingStatus"]:
        """États qui ne peuvent plus changer"""
        return {cls.COMPLETED, cls.FAILED}

    def is_final(self) -> bool:
        """Indique si l'état est final"""
        return self in self.get_final_states()

    def can_transition_to(self, new_status: "ProcessingStatus") -> bool:
        """Vérifie si la transition vers le nouvel état est valide"""
        if self.is_final():
            return False
        
        valid_transitions = {
            ProcessingStatus.PENDING: {ProcessingStatus.PROCESSING, ProcessingStatus.FAILED},
            ProcessingStatus.PROCESSING: {ProcessingStatus.COMPLETED, ProcessingStatus.FAILED}
        }
        
        return new_status in valid_transitions.get(self, set())

class ProcessingStepType(str, Enum):
    CALIBRATION = "calibration"
    STACKING = "stacking"
    STRETCHING = "stretching"
    COLOR_BALANCE = "color_balance"
    NOISE_REDUCTION = "noise_reduction"
    SHARPENING = "sharpening"
    DECONVOLUTION = "deconvolution"

    @classmethod
    def get_default_sequence(cls) -> List["ProcessingStepType"]:
        """Retourne la séquence standard de traitement"""
        return [
            cls.CALIBRATION,
            cls.STACKING,
            cls.STRETCHING,
            cls.COLOR_BALANCE,
            cls.NOISE_REDUCTION,
            cls.SHARPENING
        ]

    def requires_raw_data(self) -> bool:
        """Indique si l'étape nécessite les données brutes"""
        return self in {cls.CALIBRATION, cls.STACKING}

    def is_optional(self) -> bool:
        """Indique si l'étape est optionnelle"""
        return self in {cls.DECONVOLUTION, cls.SHARPENING}