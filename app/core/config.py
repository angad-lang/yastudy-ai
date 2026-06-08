from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MONGODB_URI: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "yastudy_knowledge"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
