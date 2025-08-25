# web/app/utils/content_loader.py
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[1]  # .../web/app
CONTENT_DIR = BASE_DIR / "content"
META_DIR = CONTENT_DIR / "meta"

def load_json(filename: str):
    """
    Lädt JSON bevorzugt aus content/meta/, fällt ansonsten auf content/ zurück.
    filename = Dateiname inkl. .json (z. B. 'home.json' oder 'courses.json')
    """
    for p in (META_DIR / filename, CONTENT_DIR / filename):
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(f"Nicht gefunden: {filename} in {META_DIR} oder {CONTENT_DIR}")