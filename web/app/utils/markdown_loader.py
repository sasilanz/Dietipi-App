from pathlib import Path
import yaml
import markdown
import re

BASE_DIR = Path(__file__).resolve().parents[1]  # .../web/app

def course_dir(slug: str) -> Path:
    """
    Gibt den Pfad zum Verzeichnis einer spezifischen Kursdurchführung zurück.
    
    Args:
        slug: Eindeutige Bezeichnung der Kursdurchführung
    
    Returns:
        Path: Pfad zu content/unterlagen/durchfuehrungen/<slug>
    """
    return BASE_DIR / "content" / "unterlagen" / "durchfuehrungen" / slug

def list_lessons(slug: str) -> list[dict]:
    """
    Listet alle verfügbaren Lektionen einer Kursdurchführung.
    
    Durchsucht durchfuehrungen/<slug>/Lxx/index.md Dateien und
    extrahiert Metadaten aus dem Front-Matter.
    
    Args:
        slug: Eindeutige Bezeichnung der Kursdurchführung
    
    Returns:
        list[dict]: Liste der Lektionen mit id, titel, order
    """
    d = course_dir(slug)
    lessons = []
    if not d.exists():
        return lessons

    for md in sorted(d.glob("L*/index.md")):
        lid = md.parent.name  # z.B. "L01"
        raw = md.read_text(encoding="utf-8")
        meta, body = {}, raw

        # sehr simples Front‑Matter‑Parsing
        if raw.startswith("---"):
            head, _, rest = raw.partition("\n---")
            try:
                meta = yaml.safe_load(head.replace("---", "", 1)) or {}
            except Exception:
                meta = {}
            body = rest.lstrip("\n")

        lessons.append({
            "id": meta.get("id", lid),
            "titel": meta.get("title", f"Lektion {lid[-2:]}"),
            "order": meta.get("order", 999),
        })

    lessons.sort(key=lambda x: (x.get("order", 999), x.get("id", "")))
    return lessons

def render_lesson(slug: str, lesson_id: str) -> tuple[dict | None, str | None, Path | None]:
    """
    Rendert eine spezifische Lektion von Markdown zu HTML.
    
    Args:
        slug: Eindeutige Bezeichnung der Kursdurchführung
        lesson_id: ID der Lektion (z.B. 'L01', 'L02')
    
    Returns:
        tuple: (meta, html, folder) oder (None, None, None) falls nicht gefunden
            - meta: Front-Matter Metadaten als dict
            - html: Gerenderter HTML-Inhalt
            - folder: Path zum Lektionsverzeichnis
    """
    md_path = course_dir(slug) / lesson_id / "index.md"
    if not md_path.exists():
        return None, None, None

    raw = md_path.read_text(encoding="utf-8")
    meta, body = {}, raw

    if raw.startswith("---"):
        head, _, rest = raw.partition("\n---")
        try:
            meta = yaml.safe_load(head.replace("---", "", 1)) or {}
        except Exception:
            meta = {}
        body = rest.lstrip("\n")

    html = markdown.markdown(body, extensions=["extra", "fenced_code", "tables"])
    return meta, html, md_path.parent

def rewrite_relative_urls(html: str, slug: str, lesson_id: str | None = None) -> str:
    """
    Wandelt relative href/src (./bild.png, ../assets/x.pdf, foo.jpg) in
    /unterlagen/<slug>/media/<pfad> um.
    Lässt absolute URLs, /root-Pfade, #anchors, mailto:, tel: unverändert.

    Wenn die Datei im selben Lektionsordner liegt und lesson_id gesetzt ist,
    wird automatisch '<lesson_id>/' vorangestellt.
    """
    base = f"/unterlagen/{slug}/media/"

    pattern = re.compile(
        r'(?P<attr>\b(?:src|href))=("|\')(?P<url>(?!https?://|/|#|mailto:|tel:)[^"\']+)'
    )

    def repl(m):
        url = m.group('url')

        # ./... -> ...
        while url.startswith("./"):
            url = url[2:]
        # ../whatever -> whatever (wir referenzieren immer relativ zum Kursordner)
        while url.startswith("../"):
            url = url[3:]

        # Falls die Referenz nicht bereits kursweit ist, und wir wissen,
        # aus welcher Lektion gerendert wird: präfix mit Lektionsordner
        if lesson_id and not url.startswith(("assets/", "docs/", "static/")):
            url = f"{lesson_id}/{url}"

        return f'{m.group("attr")}="{base}{url}"'

    return pattern.sub(repl, html)