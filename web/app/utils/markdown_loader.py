from pathlib import Path
import re
import yaml
import markdown

# Basis: .../web/app/content/unterlagen
BASE = Path(__file__).resolve().parents[1] / "content" / "unterlagen"

def course_dir(slug: str) -> Path:
    return BASE / slug

def list_lessons(slug: str):
    """
    Listet Lektionsordner (mit index.md) und liefert Metadaten:
    id, title, order, date, folder.
    """
    d = course_dir(slug)
    if not d.exists():
        return []

    lessons = []
    for p in sorted(d.iterdir()):
        if p.is_dir() and (p / "index.md").exists():
            meta, _ = _read_md(p / "index.md")
            lessons.append({
                "id": meta.get("id", p.name),
                "title": meta.get("title") or meta.get("titel") or p.name,
                "order": meta.get("order", 999),
                "date": meta.get("date"),
                "folder": p.name,
            })
    lessons.sort(key=lambda x: (x["order"], x["id"]))
    return lessons

def render_lesson(slug: str, lesson_id: str):
    """
    Rendert index.md für eine Lektion.
    Sucht Ordner mit Name == lesson_id oder Ordner, dessen meta.id == lesson_id.
    Gibt (meta, html, folder_name) zurück oder (None, None, None).
    """
    d = course_dir(slug)
    if not d.exists():
        return None, None, None

    # 1: exakter Ordnername
    cand = d / lesson_id / "index.md"
    if cand.exists():
        meta, body = _read_md(cand)
        html = _md_to_html(body)
        return meta, html, cand.parent.name

    # 2: per meta.id matchen
    for p in d.iterdir():
        md = p / "index.md"
        if md.exists():
            meta, body = _read_md(md)
            if meta.get("id") == lesson_id:
                html = _md_to_html(body)
                return meta, html, p.name

    return None, None, None

def _read_md(path: Path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        # Frontmatter split
        parts = text.split("---", 2)
        if len(parts) >= 3:
            _, fm, body = parts[0], parts[1], parts[2]
            meta = yaml.safe_load(fm) or {}
            return meta, body.strip()
    return {}, text

def _md_to_html(body: str) -> str:
    return markdown.markdown(
        body,
        extensions=["extra", "sane_lists", "toc"]
    )

REL_ATTRS = ('href', 'src')

def rewrite_relative_urls(html: str, slug: str):
    """
    Schreibt relative Links (./, ../, kein Schema) auf die Media-Route um:
    /unterlagen/<slug>/media/<relpath>
    PDFs/Images im Lektionsordner oder kursweiten assets funktionieren damit.
    """
    def repl(match):
        attr = match.group(1)
        url = match.group(2)
        # absolute oder schema-Links unverändert lassen
        if re.match(r'^(https?://|mailto:|#|/)', url):
            return match.group(0)
        # sonst zur Media-Route umbiegen
        safe = url.lstrip("./")  # ./ entfernen (../ lassen wir zu, Flask prüft gleich)
        # Wir hängen NICHT lesson_id an — relpath wird relativ zum Kursordner interpretiert
        return f'{attr}="/unterlagen/{slug}/media/{url}"'

    pattern = re.compile(r'(?:href|src)\s*=\s*"([^"]*?)"')
    # Der obige pattern matcht nur das Attribut – wir brauchen (attr, value)
    # Besser: zwei Durchläufe für href und src
    for attr in REL_ATTRS:
        html = re.sub(
            rf'({attr})\s*=\s*"([^"]+)"',
            repl,
            html
        )
    return html