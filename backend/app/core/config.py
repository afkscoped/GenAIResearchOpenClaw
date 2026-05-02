from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PRISM Backend"
    app_env: str = "development"
    database_url: str = "sqlite:///./prism.db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    github_token: str | None = None
    huggingface_token: str | None = None
    news_rss_feeds: str = "https://www.technologyreview.com/feed/,https://venturebeat.com/category/ai/feed/"
    enable_llm: bool = False
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def rss_feed_list(self) -> List[str]:
        return [feed.strip() for feed in self.news_rss_feeds.split(",") if feed.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
