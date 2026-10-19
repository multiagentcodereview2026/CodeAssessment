from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Explainable Multi-Agent AI Code Evaluator"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./codeassessment_v2.db"

    # Groq Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    # Rewrites can be large (the response includes the full source file), so
    # allow enough time for generation and retry transient provider failures.
    GROQ_TIMEOUT_SECONDS: int = 90
    GROQ_MAX_RETRIES: int = 2

    # Hybrid complexity review: AST may answer directly only when its
    # structural evidence is strong. Lower-confidence AST output is checked
    # independently by AI; a better-supported AI result can be used as a
    # guarded fallback rather than preserving a known weaker estimate.
    # Keep external source-code review opt-in. Enabling this setting authorizes
    # sending submitted source to the configured AI provider.
    COMPLEXITY_AI_REVIEW_ENABLED: bool = False
    COMPLEXITY_AST_DIRECT_CONFIDENCE: float = 0.90
    COMPLEXITY_AI_MIN_CONFIDENCE: float = 0.70
    COMPLEXITY_AI_REQUESTS_PER_MINUTE: int = 12
    COMPLEXITY_AI_MAX_CONCURRENCY: int = 2
    COMPLEXITY_AI_CACHE_TTL_SECONDS: int = 3600

    # Execution constraints
    DOCKER_EXECUTION_TIMEOUT: int = 5
    MAX_MEMORY_MB: int = 256

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
    )


settings = Settings()
