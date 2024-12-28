# test_db.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def test_connection():
    # Pega a URL do MongoDB das variáveis de ambiente
    mongodb_url = os.getenv("MONGODB_URL")
    
    try:
        # Tenta conectar ao MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        
        # Tenta fazer uma operação simples para verificar a conexão
        db = client.get_database("OpenPipes")
        await db.command("ping")
        
        print("Conexão com MongoDB estabelecida com sucesso!")
        
        # Fecha a conexão
        client.close()
        
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")

# Roda o teste
if __name__ == "__main__":
    asyncio.run(test_connection())
