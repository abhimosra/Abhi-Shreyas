import csv
import json
from datetime import datetime
from pathlib import Path

LEADS_FILE = Path(__file__).parent / "leads.csv"

FIELDNAMES = ["timestamp", "instagram_id", "message", "products_mentioned", "status"]


def _ensure_file():
    if not LEADS_FILE.exists():
        with open(LEADS_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def log_lead(instagram_id: str, message: str, products_mentioned: list[str]):
    """
    Appends a new lead row to leads.csv.
    products_mentioned is a list of product names the customer asked about.
    """
    _ensure_file()
    with open(LEADS_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "instagram_id": instagram_id,
            "message": message[:300],
            "products_mentioned": ", ".join(products_mentioned) if products_mentioned else "general inquiry",
            "status": "new",
        })


def get_all_leads() -> list[dict]:
    _ensure_file()
    with open(LEADS_FILE, "r", newline="") as f:
        return list(csv.DictReader(f))
