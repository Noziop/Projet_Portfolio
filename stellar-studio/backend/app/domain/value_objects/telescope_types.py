# app/domain/value_objects/telescope_types.py
from enum import Enum

class TelescopeStatus(Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    
    @classmethod
    def get_default(cls) -> "TelescopeStatus":
        return cls.OFFLINE
