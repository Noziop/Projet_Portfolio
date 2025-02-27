#app/domain/value_objects/target_types.py
from enum import Enum

class ObjectType(str, Enum):
    NEBULA = "nebula"
    GALAXY = "galaxy"
    STAR_CLUSTER = "star_cluster"
    PLANETARY_NEBULA = "planetary_nebula"

class TargetStatus(str, Enum):
    READY = "ready"
    NEEDS_DOWNLOAD = "needs_download"
    PROCESSING = "processing"
