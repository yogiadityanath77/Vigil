from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    # Public origin the crisis page is reachable at. The QR encodes
    # f"{base_url}/c/{slug}", so for a phone to scan-and-open this must be a
    # LAN-reachable address (e.g. http://192.168.1.20:8000), NOT localhost.
    # Default localhost is fine for same-machine browsing; override in .env to demo.
    base_url: str = "http://localhost:8000"

    model_config = {"env_file": ".env"}


settings = Settings()
