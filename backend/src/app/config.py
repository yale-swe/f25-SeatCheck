"""Application configuration.

Settings are loaded from environment variables or .env file.
Priority: Environment variables > .env file > defaults
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    For local development: Set values in .env file
    For production: Set as environment variables on hosting platform
    """

    # Database Configuration
    # Required: Must be set in .env or as environment variable
    # Example: postgresql://username@localhost:5432/seatcheck
    database_url: str = "postgresql://localhost/seatcheck"
    database_echo: bool = False  # Set to True to see SQL queries in logs

    # Application Settings
    app_title: str = "SeatCheck API"
    app_version: str = "0.1.0"
    debug: bool = True
    
    #cas auth
    cas_base_url: str = "https://secure.its.yale.edu/cas"
    cas_login_route: str = "/login"
    cas_logout_route: str = "/logout"
    frontend_url: str  = "http://localhost:3000"
    
    #session auth
    secret_key: str = "this is secret"
    session_cookie_name: str = "seatcheck_session"
    session_expire_minutes: int = 60 * 24 # 24 minutes
    environment: str = "development"
    
    # CORS Configuration
    # For local dev: Use "*" to allow all origins
    # For production: Set to specific frontend URL
    allowed_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()


def get_cors_origins() -> list[str]:
    """Parse CORS origins string into list.

    Returns:
        List of allowed origins. ["*"] if wildcard, otherwise comma-separated list.
    """
    if settings.allowed_origins == "*":
        return ["*"]
    return [origin.strip() for origin in settings.allowed_origins.split(",")]
