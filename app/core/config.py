import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Dubai Services & Deals Platform"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-development")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "postgresql://neondb_owner:[REDACTED]@ep-red-forest-atp4b3kl.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require")
    
    # Admin Credentials
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@servease.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_OTP_EMAIL: str = os.getenv("ADMIN_OTP_EMAIL", "shreyas.u.sondur@gmail.com")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    SERVER_HOST: str = "http://localhost:8000"
    FRONTEND_HOST: str = "http://localhost:3000"

    # SMTP Configuration
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True") == "True"
    SMTP_SSL: bool = os.getenv("SMTP_SSL", "False") == "True"
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_HOST: str | None = os.getenv("SMTP_HOST")
    SMTP_USER: str | None = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: str | None = os.getenv("EMAILS_FROM_EMAIL")
    EMAILS_TO_EMAIL: str | None = os.getenv("EMAILS_TO_EMAIL", "info@servizuae.com")

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
