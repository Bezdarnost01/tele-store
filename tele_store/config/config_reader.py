from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config class"""

    BOT_TOKEN: str
    ADMINS: list[int]
    DATABASE_URL: str
    ITEMS_PER_PAGE: int
    ORDERS_PER_PAGE: int
    CATEGORIES_PER_PAGE: int
    PRODUCTS_PER_PAGE: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()
