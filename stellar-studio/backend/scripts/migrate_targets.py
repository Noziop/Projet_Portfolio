# scripts/migrate_targets.py
import sys
import os
from pathlib import Path

# Ajout du chemin racine au PYTHONPATH
root_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(str(root_path))

import uuid
from sqlalchemy.sql import text
from app.db.session import SessionLocal
from app.domain.models.target import Target
from app.domain.value_objects.coordinates import Coordinates
from app.services.telescope_service import targets

def migrate_targets():
    session = SessionLocal()
    try:
        for telescope_id, targets_list in targets.items():
            print(f"Migrating {telescope_id} targets...")
            for target_data in targets_list:
                target = Target(
                    id=str(uuid.uuid4()),
                    name=target_data["name"],
                    description=target_data["description"],
                    telescope_id=telescope_id,
                    coordinates=Coordinates(
                        ra=target_data["coordinates"]["ra"],
                        dec=target_data["coordinates"]["dec"]
                    ),
                    object_type=target_data.get("object_type", "nebula")
                )
                stmt = text("""
                    INSERT INTO targets 
                    (id, name, description, telescope_id, coordinates_ra, coordinates_dec, object_type) 
                    VALUES (:id, :name, :description, :telescope_id, :coordinates_ra, :coordinates_dec, :object_type)
                """)
                session.execute(stmt, {
                    "id": target.id,
                    "name": target.name,
                    "description": target.description,
                    "telescope_id": target.telescope_id,
                    "coordinates_ra": target.coordinates.ra,
                    "coordinates_dec": target.coordinates.dec,
                    "object_type": target.object_type
                })
                print(f"Created target: {target.name}")
        session.commit()
    finally:
        session.close()

if __name__ == "__main__":
    migrate_targets()
