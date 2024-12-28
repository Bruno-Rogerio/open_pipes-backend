from app.db.mongodb import MongoDB
from app.models.user import UserInDB, UserCreate
from app.core.security import get_password_hash, verify_password

async def get_user_by_email(email: str):
    return await MongoDB.get_user_by_email(email)

async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return UserInDB(**user)

async def create_user(user: UserCreate):
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise ValueError("Email already registered")
    
    hashed_password = get_password_hash(user.password)
    user_in_db = UserInDB(**user.dict(), hashed_password=hashed_password)
    
    result = await MongoDB.database.users.insert_one(user_in_db.dict(by_alias=True))
    user_in_db.id = result.inserted_id
    return user_in_db
