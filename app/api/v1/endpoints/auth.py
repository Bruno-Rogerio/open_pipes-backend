from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Any
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import UserCreate, Token, UserInDB
from app.services.user_service import create_user, authenticate_user
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user, encrypt_token
from app.models.user import User
from app.db.mongodb import MongoDB
from fastapi import Body

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/register", response_model=UserInDB)
async def register(user: UserCreate) -> Any:
    try:
        return await create_user(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/save-pipefy-token")
async def save_pipefy_token(pipefy_token: str = Body(..., embed=True), current_user: User = Depends(get_current_user)):
    print(f"Received token: {pipefy_token}")  # Para debugging
    encrypted_token = encrypt_token(pipefy_token)
    result = await MongoDB.database.users.update_one(
        {"email": current_user.email},
        {"$set": {"pipefy_token": encrypted_token}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to save Pipefy token")
    return {"message": "Pipefy token saved successfully"}

@router.get("/check-pipefy-token")
async def check_pipefy_token(current_user: User = Depends(get_current_user)):
    user = await MongoDB.database.users.find_one({"email": current_user.email})
    has_token = "pipefy_token" in user and user["pipefy_token"] is not None
    return {"has_token": has_token}


