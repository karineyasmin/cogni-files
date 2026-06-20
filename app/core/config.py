from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application configurations and environment variables validator.
    Ensures strict typing for database connections, API keys, and model parameters.
    """

    # Application Metadata
    APP_NAME: str = "CogniFiles Backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", validation_alias="ENV")

    # Database Infrastructure (MongoDB)
    MONGO_URI: str = Field(
        default="mongodb://admin:secret_password@localhost:27017",
        validation_alias="MONGO_URI",
    )
    MONGO_DB_NAME: str = "cognifiles_db"

    # AI Platforms & LLM Orchestration
    # Usamos ... no default para dizer ao Pydantic que ele REALMENTE é obrigatório no .env
    GEMINI_API_KEY: str = Field(default=..., validation_alias="GEMINI_API_KEY")
    LOCAL_LLM_URL: str = Field(
        default="http://localhost:11434", validation_alias="LOCAL_LLM_URL"
    )
    LOCAL_MODEL_NAME: str = "llama3.2:1b"

    # Vector Storage Engine (ChromaDB)
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Now the static analyzer knows parameters will be loaded automatically
settings: Settings = Settings()
