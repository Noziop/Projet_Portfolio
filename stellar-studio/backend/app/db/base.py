# app/db/base.py
from app.db.base_class import Base
from app.infrastructure.repositories.models.user import User
from app.infrastructure.repositories.models.telescope import SpaceTelescope
from app.infrastructure.repositories.models.workflow import Workflow
from app.infrastructure.repositories.models.processing import ProcessingJob


# Assurons-nous que tous les modèles sont importés avant la création des tables
__all__ = ["Base", "User", "SpaceTelescope", "Workflow", "ProcessingJob"]
