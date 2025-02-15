from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Link Shortener"
    database_url: str
    shortcut_length: int = (
        10  # Adding SHORTCUT_LENGTH env variable will override this default value
    )

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()
