from pathlib import Path
import yaml
import markdown
import re

BASE_DIR = Path(__file__).resolve().parents[1]  # .../web/app

def course_dir(slug: str) -> Path:
    """
    Pfad zur Durchführung:
    content/unterlagen/durchfuehrungen/<slug>
    """
    return BASE_DIR / "content" / "unterlagen" / "durchfuehrungen" / slug

def list_lessons(slug: str):
    """
    Listet Lektionen aus durchfuehrungen/<slug>/Lxx/index.md
    und liest Front‑Matter (id, title, order).
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

def render_lesson(slug: str, lesson_id: str):
    """
    Rendert eine Lektion (Markdown -> HTML) und gibt (meta, html, folder) zurück.
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