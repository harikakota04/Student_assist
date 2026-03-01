from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "AI Teaching Assistant"
    groq_api_key: str = ""
    youtube_api_key: str = ""
    news_api_key: str = ""          # newsapi.org free key
    model_name: str = "all-MiniLM-L6-v2"
    llm_model: str = "llama3-8b-8192"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()