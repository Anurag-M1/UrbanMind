"""UrbanMind backend configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed environment-backed settings for the UrbanMind backend."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    REDIS_URL: str = Field(default="redis://redis:6379")
    MQTT_HOST: str = Field(default="mqtt")
    MQTT_PORT: int = Field(default=1883)
    SIGNAL_CYCLE_DEFAULT_EW: int = Field(default=30)
    SIGNAL_CYCLE_DEFAULT_NS: int = Field(default=25)
    WEBSTER_RECALC_INTERVAL: int = Field(default=10)
    EMERGENCY_CORRIDOR_LENGTH: int = Field(default=5)
    EMERGENCY_CORRIDOR_DISTANCE: int = Field(default=800)
    CV_CONFIDENCE_THRESHOLD: float = Field(default=0.65)
    FAILSAFE_FIXED_TIMER_EW: int = Field(default=30)
    FAILSAFE_FIXED_TIMER_NS: int = Field(default=25)
    JWT_SECRET: str = Field(default="urbanmind-dev-secret")
    DEBUG: bool = Field(default=True)
    DEMO_MODE: bool = Field(default=True)
    FRONTEND_ORIGIN: str = Field(default="http://localhost:3000")
    API_PREFIX: str = Field(default="/api/v1")
    WEBSOCKET_PATH: str = Field(default="/ws/dashboard")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object for import-safe reuse."""

    return Settings()


settings = get_settings()
