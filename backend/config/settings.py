import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Explainable Multi-Agent AI Code Evaluator"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./evaluator.db"
    
    # Groq Configuration (Free Cloud AI)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Execution constraints
    DOCKER_EXECUTION_TIMEOUT: int = 5
    MAX_MEMORY_MB: int = 256
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
