# web/app/utils/content_loader.py
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[1]  # .../web/app
CONTENT_DIR = BASE_DIR / "content"
META_DIR = CONTENT_DIR / "meta"

def load_json(filename: str) -> dict:
    """
    Lädt JSON-Daten aus dem Content-Verzeichnis.
    
    Sucht bevorzugt in content/meta/, fällt auf content/ zurück.
    
    Args:
        filename: Dateiname inkl. .json (z.B. 'courses.json', 'home.json')
    
    Returns:
        dict: Die geladenen JSON-Daten
    
    Raises:
        FileNotFoundError: Wenn die Datei in keinem der Suchpfade gefunden wird
    """
    for p in (META_DIR / filename, CONTENT_DIR / filename):
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(f"Nicht gefunden: {filename} in {META_DIR} oder {CONTENT_DIR}")