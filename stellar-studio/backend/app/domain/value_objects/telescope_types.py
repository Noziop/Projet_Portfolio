#app/domain/value_objects/telescope_types.py
from enum import Enum

class TelescopeStatus(Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    MAINTENANCE = "maintenance"
