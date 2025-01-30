# app/schemas/task.py
from pydantic import BaseModel

class DownloadRequest(BaseModel):
    telescope: str
    object_name: str
