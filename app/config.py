import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Pipefy Automation"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    MONGODB_URL: str
    SECRET_KEY: str
    DB_NAME: str
    ENCRYPTION_KEY: str
    
    # Configurações JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 dias
    
    # Configurações Pipefy
    PIPEFY_API_URL: str = "https://api.pipefy.com/graphql"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()

print("Debugging Settings:")
print(f"PROJECT_NAME: {settings.PROJECT_NAME}")
print(f"VERSION: {getattr(settings, 'VERSION', 'Not found')}")
print(f"API_V1_STR: {settings.API_V1_STR}")
print(f"Caminho do .env: {os.path.join(os.path.dirname(__file__), '..', '.env')}")
print(f"Diretório atual: {os.getcwd()}")
print("Todas as variáveis:")
for key, value in settings.dict().items():
    print(f"{key}: {value}")
