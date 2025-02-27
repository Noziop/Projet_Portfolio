from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class WebSocketEventType(Enum):
    # Événements de téléchargement
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_PROGRESS = "download_progress"
    DOWNLOAD_COMPLETED = "download_completed"
    DOWNLOAD_ERROR = "download_error"

    # Événements de processing
    PROCESSING_STARTED = "processing_started"
    PROCESSING_PROGRESS = "processing_progress"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_ERROR = "processing_error"

    # Événements de preview
    PREVIEW_CHANNEL = "preview_channel"
    PREVIEW_STF = "preview_stf"
    PREVIEW_FINAL = "preview_final"

class BaseEvent(BaseModel):
    type: WebSocketEventType
    timestamp: datetime = datetime.utcnow()

class DownloadEvent(BaseEvent):
    target_id: str
    filter_id: Optional[str] = None
    progress: Optional[float] = None
    file_name: Optional[str] = None
    error_message: Optional[str] = None

class ProcessingEvent(BaseEvent):
    job_id: str
    step: str
    progress: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class PreviewEvent(BaseEvent):
    job_id: str
    channel: Optional[str] = None  # Pour les previews par channel (H/O/O)
    preview_url: str
    metadata: Optional[Dict[str, Any]] = None

def create_download_started_event(target_id: str) -> Dict:
    return DownloadEvent(
        type=WebSocketEventType.DOWNLOAD_STARTED,
        target_id=target_id
    ).model_dump()

def create_download_progress_event(target_id: str, progress: float, file_name: str) -> Dict:
    return DownloadEvent(
        type=WebSocketEventType.DOWNLOAD_PROGRESS,
        target_id=target_id,
        progress=progress,
        file_name=file_name
    ).model_dump()

def create_processing_event(
    job_id: str,
    event_type: WebSocketEventType,
    step: str,
    progress: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict:
    return ProcessingEvent(
        type=event_type,
        job_id=job_id,
        step=step,
        progress=progress,
        details=details
    ).model_dump()

def create_preview_event(
    job_id: str,
    preview_url: str,
    channel: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict:
    return PreviewEvent(
        type=WebSocketEventType.PREVIEW_CHANNEL if channel else WebSocketEventType.PREVIEW_FINAL,
        job_id=job_id,
        channel=channel,
        preview_url=preview_url,
        metadata=metadata
    ).model_dump()
