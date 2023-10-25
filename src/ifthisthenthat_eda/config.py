from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    users_db_path: str = "user_db.json"
    worker_username: str = "worker"


settings = Settings()
