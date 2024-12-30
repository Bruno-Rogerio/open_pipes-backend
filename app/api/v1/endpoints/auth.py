from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Any
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, encrypt_token
from app.models.user import UserCreate, Token, UserInDB, User
from app.services.user_service import create_user, authenticate_user
from app.db.mongodb import MongoDB
from fastapi import Body
import logging

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

logger = logging.getLogger(__name__)

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.email} requested their information")
    return current_user

@router.post("/register", response_model=UserInDB)
async def register(user: UserCreate) -> Any:
    logger.info(f"Attempting to register new user with email: {user.email}")
    try:
        new_user = await create_user(user)
        logger.info(f"User {user.email} registered successfully")
        return new_user
    except ValueError as e:
        logger.error(f"Failed to register user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    logger.info(f"Login attempt for user: {form_data.username}")
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    logger.info(f"User {form_data.username} logged in successfully")
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/save-pipefy-token")
async def save_pipefy_token(pipefy_token: str = Body(..., embed=True), current_user: User = Depends(get_current_user)):
    logger.info(f"Attempting to save Pipefy token for user: {current_user.email}")
    encrypted_token = encrypt_token(pipefy_token)
    result = await MongoDB.database.users.update_one(
        {"email": current_user.email},
        {"$set": {"pipefy_token": encrypted_token}}
    )
    if result.modified_count == 0:
        logger.error(f"Failed to save Pipefy token for user: {current_user.email}")
        raise HTTPException(status_code=400, detail="Failed to save Pipefy token")
    logger.info(f"Pipefy token saved successfully for user: {current_user.email}")
    return {"message": "Pipefy token saved successfully"}

@router.get("/check-pipefy-token")
async def check_pipefy_token(current_user: User = Depends(get_current_user)):
    logger.info(f"Checking Pipefy token for user: {current_user.email}")
    user = await MongoDB.database.users.find_one({"email": current_user.email})
    has_token = "pipefy_token" in user and user["pipefy_token"] is not None
    logger.info(f"Pipefy token status for user {current_user.email}: {'Present' if has_token else 'Not present'}")
    return {"has_token": has_token}

# Adicione esta função para verificar o status da autenticação
@router.get("/check-auth")
async def check_auth(current_user: User = Depends(get_current_user)):
    logger.info(f"Checking authentication status for user: {current_user.email}")
    return {"authenticated": True, "user": current_user.email}
