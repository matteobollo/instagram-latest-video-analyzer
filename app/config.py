from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    apify_token: str
    apify_reel_actor_id: str = "apify/instagram-reel-scraper"
    apify_comments_actor_id: str = "apify/instagram-comment-scraper"
    whisper_model: str = "base"
    port: int = 8000
    log_level: str = "INFO"
    temp_dir: str = "/tmp/ig-video-analyzer"
    apify_max_reels: int = 10
    apify_max_comments: int = 100
    request_timeout_seconds: int = 120

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')


settings = Settings()
