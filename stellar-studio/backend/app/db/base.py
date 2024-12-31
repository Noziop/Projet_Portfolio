# app/db/base.py
from app.db.base_class import Base
from app.models.user import User
from app.models.telescope import SpaceTelescope
from app.models.workflow import Workflow
from app.models.processing import ProcessingJob

# Assurons-nous que tous les modèles sont importés avant la création des tables
__all__ = ["Base", "User", "SpaceTelescope", "Workflow", "ProcessingJob"]
