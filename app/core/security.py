from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.core.config import settings
from app.models.user import TokenData, UserInDB
from app.db.mongodb import MongoDB
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
fernet = Fernet(settings.ENCRYPTION_KEY)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info(f"Access token created for user: {data.get('sub')}")
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def encrypt_token(token: str) -> str:
    encrypted = fernet.encrypt(token.encode()).decode()
    logger.info("Token encrypted successfully")
    return encrypted

def decrypt_token(encrypted_token: str) -> str:
    decrypted = fernet.decrypt(encrypted_token.encode()).decode()
    logger.info("Token decrypted successfully")
    return decrypted

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token payload does not contain 'sub' claim")
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        logger.error(f"JWT decoding error: {str(e)}")
        raise credentials_exception
    user = await MongoDB.get_user_by_email(token_data.email)
    if user is None:
        logger.warning(f"User not found for email: {token_data.email}")
        raise credentials_exception
    logger.info(f"User authenticated: {token_data.email}")
    return UserInDB(**user)

# Adicione esta função para verificar se o token é válido
def is_token_valid(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        expiration = datetime.fromtimestamp(payload.get("exp"))
        if expiration > datetime.utcnow():
            logger.info(f"Token is valid for user: {payload.get('sub')}")
            return True
        else:
            logger.warning(f"Token has expired for user: {payload.get('sub')}")
            return False
    except JWTError as e:
        logger.error(f"Error validating token: {str(e)}")
        return False
