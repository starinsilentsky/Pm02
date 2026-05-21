from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.config import get_settings
from app.database import engine, Base
from app.routers import gallery, chronology, auth, search
from app.services.redis_cache import redis_client

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.MEDIA_UPLOAD_PATH, exist_ok=True)
    yield
    await engine.dispose()
    await redis_client.aclose()

app = FastAPI(
    title="Мем-музей API",
    description="Бэкенд для музея-архива интернет-мемов",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://meme-museum.ru"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.MEDIA_UPLOAD_PATH), name="uploads")

app.include_router(auth.router)
app.include_router(gallery.router)
app.include_router(chronology.router)
app.include_router(search.router)

app.mount("/static", StaticFiles(directory="frontend"), name="frontend")

@app.get("/ui", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "meme-museum-backend"}
