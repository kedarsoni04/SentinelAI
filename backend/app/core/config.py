from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for type-safe configuration.
    """

    # Environment: development | production | testing
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./sentinel.db"

    # Rate Limiting (Phase 10)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 15
    RATE_LIMIT_AI_PER_MINUTE: int = 20

    # JWT
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS — comma-separated origins parsed into a list
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Video Processing & Storage (Phase 3)
    VIDEO_STORAGE_PATH: str = "./storage"
    MAX_VIDEO_SIZE_MB: int = 250
    SAMPLE_INTERVAL_SECONDS: float = 2.0
    MAX_FRAME_WIDTH: int = 1280
    THUMBNAIL_WIDTH: int = 320

    # YOLO Object Detection (Phase 4)
    YOLO_MODEL: str = "yolo11n.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.50
    YOLO_ALLOWED_CLASSES: str = "person,car,motorcycle,bus,truck,bicycle"
    YOLO_DEVICE: str = "auto"

    # Object Tracking & Temporal Intelligence (Phase 5)
    TRACKING_ENABLED: bool = True
    TRACKER_TYPE: str = "bytetrack"
    TRACK_HIGH_CONFIDENCE_THRESHOLD: float = 0.25
    TRACK_LOW_CONFIDENCE_THRESHOLD: float = 0.10
    TRACK_BUFFER_FRAMES: int = 30
    TRACK_MATCH_THRESHOLD: float = 0.80
    TRACK_DRAW_TRAJECTORY: bool = True
    TRACK_MAX_TRAJECTORY_POINTS: int = 30

    # Real-Time Monitoring & WebSocket (Phase 7)
    REALTIME_ENABLED: bool = True
    WEBSOCKET_ENABLED: bool = True
    REALTIME_HEARTBEAT_INTERVAL: int = 5
    REALTIME_RECONNECT_MAX_SECONDS: int = 30

    # AI Incident Intelligence (Phase 8)
    # Provider: "gemini" | "groq" | "mock"
    # Falls back to "mock" automatically if the selected provider's key is missing.
    AI_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.3
    AI_REQUEST_TIMEOUT_SECONDS: int = 30

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def uploads_path(self) -> str:
        import os
        path = os.path.join(self.VIDEO_STORAGE_PATH, "uploads")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def frames_path(self) -> str:
        import os
        path = os.path.join(self.VIDEO_STORAGE_PATH, "frames")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def annotated_path(self) -> str:
        import os
        path = os.path.join(self.VIDEO_STORAGE_PATH, "annotated")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def allowed_classes_list(self) -> List[str]:
        if not self.YOLO_ALLOWED_CLASSES or not self.YOLO_ALLOWED_CLASSES.strip():
            return []
        return [c.strip().lower() for c in self.YOLO_ALLOWED_CLASSES.split(",") if c.strip()]

    @property
    def sync_database_url(self) -> str:
        """
        Ensures PostgreSQL URLs use postgresql+psycopg2 driver for SQLAlchemy 2.x compatibility.
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() == "testing"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


import re

def mask_stream_url(url: Optional[str]) -> Optional[str]:
    """
    Mask credentials in stream URLs for safe logging and telemetry.
    Example: rtsp://admin:secret123@192.168.1.50:554 -> rtsp://admin:***@192.168.1.50:554
    """
    if not url:
        return url
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", url)


def validate_production_secrets(config: Settings) -> None:
    """
    Validates required secrets in production mode.
    Fails safely with clear errors rather than running with insecure defaults.
    """
    if not config.is_production:
        return

    insecure_secrets = {
        "change-this-secret-in-production",
        "change-this-to-a-random-secret-in-production",
        "secret",
        "changeme",
        "default",
        "",
    }

    if config.JWT_SECRET_KEY in insecure_secrets or len(config.JWT_SECRET_KEY) < 32:
        raise ValueError(
            "CRITICAL SECURITY CONFIGURATION ERROR: "
            "In production, JWT_SECRET_KEY must be a cryptographically strong secret "
            "with at least 32 characters. Generate one via: "
            "python -c 'import secrets; print(secrets.token_hex(32))'"
        )

    if "*" in config.cors_origins_list:
        raise ValueError(
            "CRITICAL SECURITY CONFIGURATION ERROR: "
            "CORS_ORIGINS cannot contain wildcard '*' in production when credentials are enabled. "
            "Specify exact domains, e.g. https://soc.yourdomain.com"
        )


settings = Settings()
validate_production_secrets(settings)

