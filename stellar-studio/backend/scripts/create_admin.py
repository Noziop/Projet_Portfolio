# scripts/create_admin.py
import sys
import os
from pathlib import Path
import uuid
from passlib.context import CryptContext

root_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(str(root_path))

from sqlalchemy.sql import text
from app.db.session import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    session = SessionLocal()
    try:
        # Vérifier si l'admin existe déjà
        admin_exists = session.execute(
            text("SELECT id FROM users WHERE email = 'admin@stellarstudio.com'")
        ).fetchone()
        
        if not admin_exists:
            # Créer l'admin
            admin_data = {
                "id": str(uuid.uuid4()),
                "email": "admin@stellarstudio.com",
                "username": "admin",
                "hashed_password": pwd_context.hash("stellarpass"),
                "role": "ADMIN",
                "level": "ADVANCED",
                "is_active": True
            }
            
            session.execute(
                text("""
                    INSERT INTO users 
                    (id, email, username, hashed_password, role, level, is_active) 
                    VALUES 
                    (:id, :email, :username, :hashed_password, :role, :level, :is_active)
                """),
                admin_data
            )
            session.commit()
            print("Administrateur créé avec succès !")
        else:
            print("L'administrateur existe déjà !")
            
    finally:
        session.close()

if __name__ == "__main__":
    create_admin()
