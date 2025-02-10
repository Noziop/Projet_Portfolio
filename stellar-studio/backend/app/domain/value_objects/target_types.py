# app/domain/value_objects/target_types.py
from enum import Enum

class ObjectType(str, Enum):
    NEBULA = "nebula"
    GALAXY = "galaxy"
    STAR_CLUSTER = "star_cluster"
    PLANETARY_NEBULA = "planetary_nebula"
