# app/domain/models/telescope.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Telescope:
    id: str
    name: str
    description: str
    aperture: str
    focal_length: str
    location: str
    instruments: List[str]
    api_endpoint: str
