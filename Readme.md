# IT-Kurs Portal – Struktur & Nutzung

## 1. Wie `base.html` und `index.html` zusammenhängen
- **`base.html`** ist das Grundlayout (Head, Navigation, Footer, CSS‑Einbindung).
- Jede Seite „erbt“ das Layout:
  ```jinja2
  {% extends "base.html" %}
  {% block title %}Seitentitel{% endblock %}
  {% block content %}…Seiteninhalt…{% endblock %}
  ```
- **`index.html`** ist die Startseite und enthält nur den Inhalt in `block content`.  
  Route dazu in `app.py`:
  ```python
  @app.get("/")
  def index():
      return render_template("index.html")
  ```

## 2. Wo du was pflegst
- **Navigation, Grundlayout, Footer, globale Stile:**  
  `templates/base.html` und `static/css/style.css`
- **Startseiten‑Inhalt:**  
  `templates/index.html`
- **Admin‑Seiten (Teilnehmende):**  
  `templates/list_participants.html`, `add_participant.html`, `edit_participant.html`
- **Routen/Logik/DB:**  
  `app.py`, `models.py`

## 3. Admin‑Schutz (Token)
- In `web/.env`:
  ```
  ADMIN_TOKEN=dein_geheimes_token
  ```
- Decorator in `app.py` (verkürzt):
  ```python
  from functools import wraps
  from flask import request, abort
  ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

  def require_admin(f):
      @wraps(f)
      def dec(*a, **k):
          token = request.args.get("admin") or request.headers.get("X-Admin-Token")
          if token != ADMIN_TOKEN: abort(403)
          return f(*a, **k)
      return dec
  ```
- Auf **alle Admin‑Routen** anwenden (Beispiele):
  ```python
  @app.get("/teilnehmende") @require_admin
  @app.get("/teilnehmende/new") @require_admin
  @app.post("/teilnehmende/new") @require_admin
  @app.get("/teilnehmende/<int:pid>/edit") @require_admin
  @app.post("/teilnehmende/<int:pid>/edit") @require_admin
  @app.post("/teilnehmende/<int:pid>/delete") @require_admin
  ```
- **Count** kann öffentlich bleiben:
  ```python
  @app.get("/teilnehmende/count")
  ```
- **Admin‑Hub**:
  ```python
  @app.get("/_admin") @require_admin
  def admin_home():
      return render_template("admin_home.html", token=ADMIN_TOKEN)
  ```
  Aufrufen: `http://localhost:5001/_admin?admin=DEIN_TOKEN`

## 4. Wichtigste URLs
- **Öffentlich:** `/` (Startseite), `/teilnehmende/count`
- **Admin:** `/_admin?admin=TOKEN`, `/teilnehmende?admin=TOKEN`, `/teilnehmende/new?admin=TOKEN`, `/teilnehmende/<id>/edit?admin=TOKEN`

## 5. Projektstruktur (relevant)
```
tree -a -I .git
.
├── .DS_Store
├── Doks
│   ├── chat_index.md
│   ├── content.md
│   ├── entscheidungsprotokoll.md
│   ├── kursinhalte.md
│   ├── kursportal_struktur.pdf
│   └── webapp.md
├── Readme.md
├── compose.yaml
└── web
    ├── .DS_Store
    ├── .env
    ├── Dockerfile
    ├── app
    │   ├── .DS_Store
    │   ├── __init__.py
    │   ├── app.py
    │   ├── content
    │   │   ├── alle_kurse.json
    │   │   ├── home.json
    │   │   └── kurs_grundkurs-2025.json
    │   ├── models.py
    │   ├── static
    │   │   ├── .DS_Store
    │   │   ├── css
    │   │   │   ├── img
    │   │   │   └── style.css
    │   │   └── img
    │   │       └── bank_qr.png
    │   └── templates
    │       ├── add_participant.html
    │       ├── admin_home.html
    │       ├── base.html
    │       ├── edit_participant.html
    │       ├── index.html
    │       ├── kurs_info.html
    │       ├── kursleitung.html
    │       ├── list_participants.html
    │       ├── payment.html
    │       ├── register.html
    │       └── register_success.html
    └── requirements.txt

10 directories, 34 files
```

## 6. Nützliche Compose‑Befehle
```bash
docker compose up -d                 # alles starten
docker compose build webapp          # Web-Image neu bauen
docker compose up -d webapp          # Web neu starten
docker compose logs -f webapp        # Web-Logs ansehen
```
