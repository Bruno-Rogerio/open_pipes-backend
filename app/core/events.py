from fastapi import FastAPI
from app.db.mongodb import MongoDB
import logging

async def connect_to_db(app: FastAPI):
    logging.info("Conectando ao MongoDB...")
    await MongoDB.connect_to_database()

async def close_db_connection(app: FastAPI):
    logging.info("Fechando conexão com MongoDB...")
    await MongoDB.close_database_connection()

def create_start_app_handler(app: FastAPI):
    async def start_app() -> None:
        await connect_to_db(app)
    return start_app

def create_stop_app_handler(app: FastAPI):
    async def stop_app() -> None:
        await close_db_connection(app)
    return stop_app
