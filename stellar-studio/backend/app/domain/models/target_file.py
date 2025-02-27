# app/domain/models/target_file.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

@dataclass
class TargetFile:
    id: UUID
    target_id: UUID
    filter_id: UUID
    file_path: str
    mast_id: str
    file_size: Optional[int] = None
    is_downloaded: bool = False
    in_minio: bool = False
    fits_metadata: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None