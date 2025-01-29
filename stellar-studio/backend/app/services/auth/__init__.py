# app/services/auth/__init__.py
from .service import AuthService

# Export uniquement le service principal pour simplifier l'utilisation
auth_service = AuthService()

__all__ = ['auth_service']
