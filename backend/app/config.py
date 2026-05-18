"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "mysql+aiomysql://root:AIGuard2026@192.168.3.100:3306/aiguardrail"
    redis_url: str = "redis://192.168.3.100:6379/0"

    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production-aigaurd-2026"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Email
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = "noreply@example.com"
    smtp_password: str = "your-smtp-password"

    # App
    app_name: str = "AI Firewall"
    app_version: str = "1.0.0"
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Rate Limiting
    rate_limit_per_minute: int = 60
    api_key_rate_limit_per_minute: int = 100

    # Logging
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+aiomysql", "+pymysql")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
