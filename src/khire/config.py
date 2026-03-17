from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://khire:khire@localhost:5432/khire"
    redis_url: str = "redis://localhost:6379/0"
    github_token: str = ""
    default_llm_model: str = "gpt-4o-mini"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
