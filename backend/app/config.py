import os
from pathlib import Path

APP_ENV = os.getenv("APP_ENV", "development")
DATA_MODE = os.getenv("DATA_MODE", "demo").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/oi_profile.db")
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "")
API_KEY = os.getenv("API_KEY", "")

Path("./data").mkdir(exist_ok=True)
