from sqlalchemy import (
    Column, String, DateTime, Boolean, Enum, CheckConstraint, 
    event, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from app.db.base_class import Base
from app.domain.value_objects.user_types import UserLevel, UserRole
from datetime import datetime, timezone
import re

class User(Base):
    """Modèle SQLAlchemy pour les utilisateurs de la plateforme.
    
    Ce modèle gère les informations des utilisateurs, leurs authentifications,
    leurs rôles et leurs relations avec les différentes entités du système.
    """

    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('username', name='uq_user_username'),
        CheckConstraint(
            'length(username) >= 3',
            name='check_username_length'
        ),
        CheckConstraint(
            "email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name='check_email_format'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Authentification
    email = Column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Adresse email de l'utilisateur"
    )
    
    username = Column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Nom d'utilisateur"
    )
    
    hashed_password = Column(
        String(255), 
        nullable=False,
        comment="Mot de passe hashé"
    )

    # Colonnes - Informations personnelles
    firstname = Column(
        String(100), 
        nullable=True,
        comment="Prénom"
    )
    
    lastname = Column(
        String(100), 
        nullable=True,
        comment="Nom de famille"
    )

    # Colonnes - Rôle et niveau
    level = Column(
        Enum(UserLevel), 
        nullable=False, 
        default=UserLevel.BEGINNER,
        index=True,
        comment="Niveau d'expertise de l'utilisateur"
    )
    
    role = Column(
        Enum(UserRole), 
        nullable=False, 
        default=UserRole.USER,
        index=True,
        comment="Rôle de l'utilisateur dans le système"
    )

    # Colonnes - État
    last_login = Column(
        DateTime(timezone=True), 
        nullable=True, 
        index=True,
        comment="Date de dernière connexion"
    )
    
    is_active = Column(
        Boolean, 
        nullable=False, 
        default=True, 
        index=True,
        comment="Indique si le compte est actif"
    )

    # Relations
    tasks = relationship(
        "Task", 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    processing_jobs = relationship(
        "ProcessingJob", 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Validateurs
    @validates('email')
    def validate_email(self, key, email):
        """Valide le format de l'email."""
        if not email:
            raise ValueError("L'email est requis")
            
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Format d'email invalide")
            
        return email.lower()

    @validates('username')
    def validate_username(self, key, username):
        """Valide le nom d'utilisateur."""
        if not username or len(username.strip()) < 3:
            raise ValueError("Le nom d'utilisateur doit contenir au moins 3 caractères")
            
        pattern = r'^[A-Za-z0-9_-]+$'
        if not re.match(pattern, username):
            raise ValueError("Le nom d'utilisateur ne peut contenir que des lettres, chiffres, - et _")
            
        return username.strip()

    @validates('firstname', 'lastname')
    def validate_name(self, key, name):
        """Valide les noms et prénoms."""
        if name:
            name = name.strip()
            if len(name) > 100:
                raise ValueError(f"Le {key} ne peut pas dépasser 100 caractères")
            if not name.replace(' ', '').isalpha():
                raise ValueError(f"Le {key} ne peut contenir que des lettres")
        return name

    @validates('hashed_password')
    def validate_password(self, key, password):
        """Valide le hash du mot de passe."""
        if not password or len(password) < 60:  # Pour bcrypt
            raise ValueError("Le hash du mot de passe est invalide")
        return password

    def __repr__(self):
        return (
            f"<User("
            f"username='{self.username}', "
            f"email='{self.email}', "
            f"role={self.role.name})>"
        )

    # Méthodes utilitaires
    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur."""
        if self.firstname and self.lastname:
            return f"{self.firstname} {self.lastname}"
        return self.username

    def update_last_login(self):
        """Met à jour la date de dernière connexion."""
        self.last_login = datetime.now(timezone.utc)

    def promote_level(self):
        """Augmente le niveau de l'utilisateur."""
        level_order = list(UserLevel)
        current_index = level_order.index(self.level)
        if current_index < len(level_order) - 1:
            self.level = level_order[current_index + 1]

    def set_role(self, new_role: UserRole):
        """Change le rôle de l'utilisateur."""
        if not isinstance(new_role, UserRole):
            raise ValueError("Rôle invalide")
        self.role = new_role

    def deactivate(self):
        """Désactive le compte utilisateur."""
        self.is_active = False

    def activate(self):
        """Active le compte utilisateur."""
        self.is_active = True

# Event Listeners
@event.listens_for(User, 'before_insert')
def set_default_values(mapper, connection, target):
    """Définit les valeurs par défaut avant insertion."""
    if target.level is None:
        target.level = UserLevel.BEGINNER
    if target.role is None:
        target.role = UserRole.USER

@event.listens_for(User, 'before_update')
def validate_role_change(mapper, connection, target):
    """Vérifie les changements de rôle autorisés."""
    if hasattr(target, '_sa_instance_state'):
        if 'role' in target._sa_instance_state.committed_state:
            old_role = target._sa_instance_state.committed_state['role']
            new_role = target.role
            
            # Empêcher la rétrogradation des administrateurs
            if old_role == UserRole.ADMIN and new_role != UserRole.ADMIN:
                raise ValueError("Impossible de rétrograder un administrateur")

class UserError(Exception):
    """Exception personnalisée pour les erreurs liées aux utilisateurs."""
    pass
