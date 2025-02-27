# app/infrastructure/repositories/models/base.py
from app.db.base_class import Base

# Import des modèles dans l'ordre des dépendances
# 1. Modèles indépendants (pas de ForeignKey)
from .user import User
from .telescope import SpaceTelescope
from .workflow import Workflow

# 2. Modèles avec une seule dépendance
from .filter import Filter  # Dépend de SpaceTelescope
from .target import Target  # Dépend de SpaceTelescope
from .preset import Preset  # Dépend de SpaceTelescope
from .task import Task     # Dépend de User

# 3. Modèles avec multiples dépendances
from .target_file import TargetFile         # Dépend de Target, Filter
from .observation import Observation         # Dépend de Target, SpaceTelescope
from .processing import ProcessingJob        # Dépend de User, SpaceTelescope, Workflow, Target, Preset, Task

# 4. Tables d'association
from .preset_filter import PresetFilter           # Dépend de Preset, Filter
from .preset_target_file import PresetTargetFile  # Dépend de Preset, TargetFile
from .target_preset import TargetPreset           # Dépend de Target, Preset

# Liste des modèles exportés
__all__ = (
    "Base",
    "User",
    "SpaceTelescope",
    "Workflow",
    "Filter",
    "Target",
    "Preset",
    "Task",
    "TargetFile",
    "Observation",
    "ProcessingJob",
    "PresetFilter",
    "PresetTargetFile",
    "TargetPreset",
)
