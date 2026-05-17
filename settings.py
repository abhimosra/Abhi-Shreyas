import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID", "")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "")
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Our Jewelry Brand")

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
INSTAGRAM_API_BASE = "https://graph.instagram.com/v21.0"

CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog.json"
