# domain/models/target_file.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

@dataclass
class TargetFile:
    id: str
    target_id: str
    filter_id: str
    file_path: str
    file_size: Optional[int]
    in_minio: bool
    fits_metadata: Optional[Dict]
    created_at: datetime
    updated_at: datetime