# app/domain/value_objects/coordinates.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Coordinates:
    ra: str  # Right Ascension
    dec: str  # Declination
