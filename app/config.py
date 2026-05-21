from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://meme_user:meme_pass@localhost/meme_museum"

    REDIS_URL: str = "redis://localhost:6379/0"

    ELASTICSEARCH_URL: str = "http://localhost:9200"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    MEDIA_UPLOAD_PATH: str = "./uploads"
    MAX_FILE_SIZE: int = 20 * 1024 * 1024

    DEFAULT_PAGE_SIZE: int = 24
    MAX_PAGE_SIZE: int = 100

    model_config = {"env_file": ".env"}

@lru_cache()
def get_settings() -> Settings:
    return Settings()
