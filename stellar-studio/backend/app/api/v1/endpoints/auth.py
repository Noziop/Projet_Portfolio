# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, User, Token, PasswordChange
from app.api.deps import get_current_user

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=User)
async def register(user_in: UserCreate):
    try:
        return await auth_service.register_new_user(user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        return await auth_service.authenticate(
            email=form_data.username,
            password=form_data.password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    try:
        await auth_service.logout(current_user.id)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    try:
        await auth_service.change_password(
            current_user.id,
            password_data.old_password,
            password_data.new_password
        )
        return {"message": "Password successfully changed"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/deactivate")
async def deactivate_account(current_user: User = Depends(get_current_user)):
    try:
        await auth_service.deactivate_account(current_user.id)
        return {"message": "Account successfully deactivated"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=User)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
