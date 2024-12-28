from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OpenPipes"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 dias
    MONGODB_URL: str
    DB_NAME: str
    ENCRYPTION_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
