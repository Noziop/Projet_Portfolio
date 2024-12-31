# app/db/init_db.py
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User, UserLevel

def init_db(db: Session) -> None:
    user = db.query(User).filter(User.email == "admin@stellarstudio.com").first()
    if not user:
        user = User(
            email="admin@stellarstudio.com",
            username="admin",
            hashed_password=get_password_hash("stellarpass"),
            firstname="Admin",
            lastname="StellarStudio",
            level=UserLevel.ADVANCED,
            is_active=True
        )
        db.add(user)
        db.commit()
