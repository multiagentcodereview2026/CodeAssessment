from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Explainable Multi-Agent AI Code Evaluator"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./evaluator.db"

    # Groq Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    # Rewrites can be large (the response includes the full source file), so
    # allow enough time for generation and retry transient provider failures.
    GROQ_TIMEOUT_SECONDS: int = 90
    GROQ_MAX_RETRIES: int = 2

    # Execution constraints
    DOCKER_EXECUTION_TIMEOUT: int = 5
    MAX_MEMORY_MB: int = 256

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
    )


settings = Settings()
