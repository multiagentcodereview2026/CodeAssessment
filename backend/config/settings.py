from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Explainable Multi-Agent AI Code Evaluator"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./codeassessment_v2.db"

    # Groq Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    # Rewrites can be large (the response includes the full source file), so
    # allow enough time for generation. Assessment completion must not wait on
    # a rate-limited optional provider: deterministic feedback is available as
    # a safe fallback, so retries are opt-in rather than the default.
    GROQ_TIMEOUT_SECONDS: int = 90
    # Provider-level automatic retries can multiply a burst of agent calls.
    # Requests are coordinated in agents.base instead, where rate-limit
    # backoff is visible and bounded.
    GROQ_MAX_RETRIES: int = 0
    GROQ_MIN_REQUEST_INTERVAL_SECONDS: float = 15.0
    GROQ_RATE_LIMIT_RETRIES: int = 1
    # AI is an optional, narrowly-scoped assistant. Automated assessment
    # stays deterministic unless an administrator explicitly enables an
    # additional capability in the environment.
    AI_ALLOWED_CAPABILITIES: str = "hints,revision,score_projection,supervisor,correctness,explainability,recommendation,similarity,complexity_review"
    # A guided learning step must feel interactive. If the optional provider
    # takes longer than this, deterministic evidence-based guidance is used.
    GUIDED_REVISION_TIMEOUT_SECONDS: int = 12
    # Projection generates a complete private draft and then judges it, so it
    # gets a bounded but separate budget. Guidance must still return if this
    # longer verification path is unavailable.
    # This must not be shorter than the provider timeout: otherwise a valid
    # private full-source draft can be cancelled before it reaches Docker.
    SCORE_PROJECTION_TIMEOUT_SECONDS: int = 95
    # A model draft can be syntactically valid yet miss an edge case. Try a
    # One draft per learner action prevents score projection from consuming
    # several large model completions in the same minute. A later explicit
    # retry is a new, independently judged attempt.
    SCORE_PROJECTION_MAX_DRAFT_ATTEMPTS: int = 1
    # A provider throttle is not a failed learner revision. Keep the public
    # projection pending and retry quietly in the background instead of
    # exposing an unavailable/guessed score.
    SCORE_PROJECTION_BACKGROUND_RETRIES: int = 5
    SCORE_PROJECTION_RETRY_DELAY_SECONDS: int = 120

    # Hybrid complexity review: AST may answer directly only when its
    # structural evidence is strong. Lower-confidence AST output is checked
    # independently by AI; a better-supported AI result can be used as a
    # guarded fallback rather than preserving a known weaker estimate.
    # Keep external source-code review opt-in. Enabling this setting authorizes
    # sending submitted source to the configured AI provider.
    COMPLEXITY_AI_REVIEW_ENABLED: bool = False
    # Structural AST evidence at 0.85 already includes concrete loop and
    # allocation facts. It should receive deterministic marks even when the
    # optional AI corroborator is unavailable.
    COMPLEXITY_AST_DIRECT_CONFIDENCE: float = 0.85
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
