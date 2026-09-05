from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    database_url: str

    # SSO
    identity_issuer: str = "https://identity.folding-os.com"
    identity_client_id: str = "news"
    identity_client_secret: str = ""

    # AI
    ollama_base_url: str = ""
    ollama_model: str = "qwen3.5:4b-compress"

    ai_rate_limit_per_minute: int = 30
    feed_cache_ttl_seconds: int = 60


settings = Settings()
