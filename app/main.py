from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, pipefy
from app.core.config import settings
from app.db.mongodb import MongoDB

try:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API para automação de cards no Pipefy",
        version=getattr(settings, 'VERSION', '1.0.0')  # Use um valor padrão se VERSION não existir
    )

    # Configuração CORS
    app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://open-pipes-backend.onrender.com",
        "https://openpipes.netlify.app"
    ],
    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    @app.on_event("startup")
    async def startup_db_client():
        await MongoDB.connect_to_database()

    @app.on_event("shutdown")
    async def shutdown_db_client():
        await MongoDB.close_database_connection()

    # Rotas
    app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
    app.include_router(pipefy.router, prefix=f"{settings.API_V1_STR}/pipefy", tags=["pipefy"])
 
    @app.get("/")
    async def root():
        return {"message": f"Bem-vindo à API {settings.PROJECT_NAME}"}

except Exception as e:
    print(f"Erro durante a inicialização: {e}")
    raise
