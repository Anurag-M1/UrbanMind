from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379"
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    WEBSTER_INTERVAL: int = 10
    CORRIDOR_LENGTH: int = 5
    CONFIDENCE_THRESHOLD: float = 0.65
    UPLOAD_DIR: str = "./uploads"
    MAX_VIDEO_SIZE_MB: int = 200
    DEMO_MODE: bool = True
    API_CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:5173"]'

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.API_CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
