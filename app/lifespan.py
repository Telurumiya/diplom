from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.core import get_settings
from app.db.database import init_db
from app.db.redis import AsyncRedisClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    # Создание директории загрузки
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    yield

    await AsyncRedisClient.close()
