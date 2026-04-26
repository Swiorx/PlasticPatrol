from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ADMIN_SECRET: str = "plasticpatrol-admin-reset-2024"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
