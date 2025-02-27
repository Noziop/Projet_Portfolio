#app/api/v1/endpoints/ws/connection.py
from fastapi import APIRouter, WebSocket, Depends, Query
from uuid import UUID
from app.core.ws.manager import ConnectionManager
from app.api.deps import get_current_user, get_session_service  # Remplace get_session_manager
from app.domain.models.user import User

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: UUID,
    token: str = Query(...),
    current_user: User = Depends(get_current_user),  # Vérifie l'authentification
    session_service = Depends(get_session_service)  # Ajoute cette dépendance
):
    # Vérifie que l'utilisateur accède à sa propre connexion
    if current_user.id != user_id:
        await websocket.close(code=1008)  # Policy Violation
        return

    # Vérification de la session
    redis_session = await session_service.get_session(user_id)  # Utilise session_service
    if not redis_session:
        await websocket.close(code=1008)
        return

    try:
        # Accepte la connexion
        await manager.connect(user_id, websocket)
        
        try:
            while True:
                # Attend les messages du client
                data = await websocket.receive_json()
                
                # Traitement des messages client (si nécessaire)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
        except Exception as e:
            await manager.send_error(user_id, str(e))
            
    finally:
        # Déconnexion propre
        await manager.disconnect(user_id)
