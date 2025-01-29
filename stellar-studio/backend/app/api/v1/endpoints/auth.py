# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from app.services.auth import auth_service
from app.schemas.user import UserCreate, User, Token, PasswordChange, UserUpdate
from app.api.deps import get_current_user, require_role
from app.domain.models.user import UserRole

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user_in: UserCreate):
    try:
        return await auth_service.register_new_user(user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        return await auth_service.authenticate(email=form_data.username, password=form_data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={"WWW-Authenticate": "Bearer"})

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    try:
        await auth_service.logout(current_user.id)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/change-password")
async def change_password(password_data: PasswordChange, current_user: User = Depends(get_current_user)):
    try:
        await auth_service.change_password(current_user.id, password_data.old_password, password_data.new_password)
        return {"message": "Password successfully changed"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/deactivate")
async def deactivate_account(current_user: User = Depends(get_current_user)):
    try:
        await auth_service.deactivate_account(current_user.id)
        return {"message": "Account successfully deactivated"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/me", response_model=User)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

# Nouvelles routes pour la gestion des utilisateurs par l'admin
@router.get("/users", response_model=List[User])
@require_role(UserRole.ADMIN)
async def list_users(current_user: User = Depends(get_current_user)):
    return await auth_service.list_all_users()

@router.get("/users/{user_id}", response_model=User)
@require_role(UserRole.ADMIN)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=User)
@require_role(UserRole.ADMIN)
async def update_user(user_id: str, user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    try:
        return await auth_service.update_user(user_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}")
@require_role(UserRole.ADMIN)
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    try:
        await auth_service.delete_user(user_id)
        return {"message": "User successfully deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
