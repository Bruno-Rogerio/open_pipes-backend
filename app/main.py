from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, pipefy
from app.core.config import settings
from app.db.mongodb import MongoDB
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("Connecting to database...")
        await MongoDB.connect_to_database()
        logger.info("Connected to database successfully")

    @app.on_event("shutdown")
    async def shutdown_db_client():
        logger.info("Closing database connection...")
        await MongoDB.close_database_connection()
        logger.info("Database connection closed")

    # Rotas
    app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
    app.include_router(pipefy.router, prefix=f"{settings.API_V1_STR}/pipefy", tags=["pipefy"])

    @app.get("/")
    async def root():
        return {"message": f"Bem-vindo à API {settings.PROJECT_NAME}"}

    logger.info(f"API {settings.PROJECT_NAME} initialized successfully")

except Exception as e:
    logger.error(f"Erro durante a inicialização: {e}", exc_info=True)
    raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
