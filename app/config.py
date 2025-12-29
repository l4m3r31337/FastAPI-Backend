from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    NATS_URL: str = "nats://localhost:4222"
    CBR_URL: str = "https://www.cbr-xml-daily.ru/daily_json.js"
    TASK_INTERVAL_SECONDS: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
