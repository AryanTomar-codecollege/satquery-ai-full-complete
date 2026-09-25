import os
from dotenv import load_dotenv

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8001"))
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
KAGGLE_NGROK_URL = os.getenv("KAGGLE_NGROK_URL", "").strip()
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "180"))
MAX_FILES = int(os.getenv("MAX_FILES", "2"))
EARTHDIAL_MODEL = os.getenv("EARTHDIAL_MODEL", "EarthDial_4B_MS")
USE_LORA = os.getenv("USE_LORA", "false").lower() == "true"
LORA_PATH = os.getenv("LORA_PATH", "").strip()

def kaggle_url_configured() -> bool:
    if not KAGGLE_NGROK_URL:
        return False
    upper = KAGGLE_NGROK_URL.upper()
    return not any(x in upper for x in ("PUT_", "YOUR_", "EXAMPLE"))

OMNIROUTE_ENABLED = os.getenv("OMNIROUTE_ENABLED", "false").lower() == "true"
OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_BASE_URL", "").strip()
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "").strip()
OMNIROUTE_MODEL = os.getenv("OMNIROUTE_MODEL", "").strip()
OMNIROUTE_TIMEOUT = float(os.getenv("OMNIROUTE_TIMEOUT", "20"))

def omniroute_configured() -> bool:
    return (
        OMNIROUTE_ENABLED
        and bool(OMNIROUTE_BASE_URL)
        and bool(OMNIROUTE_API_KEY)
        and bool(OMNIROUTE_MODEL)
    )
