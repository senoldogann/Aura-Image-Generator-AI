import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # App Config
    API_TITLE: str = "AURA - AI Image Generator API"
    API_VERSION: str = "2.0.0"
    AUTHOR: str = "Senol Dogan"
    CONTACT_EMAIL: str = "contact@senoldogan.dev"
    WEBSITE: str = "https://www.senoldogan.dev"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    ARTIFACTS_DIR: str = os.path.join(BASE_DIR, "artifacts")
    
    # Logic
    EPHEMERAL_TTL: int = int(os.getenv("EPHEMERAL_TTL", 3600)) # 1 Hour
    MAX_QUEUE_SIZE: int = 1 # Strict Semaphore

settings = Settings()

# Ensure directories exist
os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
