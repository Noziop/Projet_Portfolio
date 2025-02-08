# domain/models/filter.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Filter:
    id: str
    name: str
    telescope_id: str
    wavelength: Optional[float]
    description: Optional[str]
