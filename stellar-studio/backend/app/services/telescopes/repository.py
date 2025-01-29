from sqlalchemy.orm import Session
from typing import List, Optional
from app.infrastructure.repositories.models.telescope import SpaceTelescope

class TelescopeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[SpaceTelescope]:
        return self.db.query(SpaceTelescope).all()

    def get_by_id(self, telescope_id: str) -> Optional[SpaceTelescope]:
        return self.db.query(SpaceTelescope).filter(SpaceTelescope.id == telescope_id).first()
