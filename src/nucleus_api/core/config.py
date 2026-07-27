from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configuration settings for the application.
    """

    # Add your configuration fields here
    app_name: str = "Nucleus API"
    environment: str = "development"
    log_level: str = "INFO"

    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str

    redis_url: str
    
    class Config:
        env_file = ".env"

settings = Settings()