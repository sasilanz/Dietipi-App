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


## 7. CI/DC Workflow
### Übersicht:
[Internet/Browser]
        │
        ▼
  Cloudflare Edge
        │   (Tunnel)
        ▼
+-------------------+
|  cloudflared      |  <-- outbound Tunnel, keine Ports
+-------------------+
          │  routes intern auf http://webapp:5000
          ▼
+-------------------+           +------------------+
|     webapp        | <-------> |       db         |
| :5000 (-> Host 5001)          | :3306 (-> Host)  |
+-------------------+           +------------------+
          ▲
          │
          │                 +------------------+
          └────────────────▶ |     adminer     |
                              | :8080 (-> Host 8081) |
                              +------------------+

### Compose-Dateien übersicht:

repo-root/
├─ Dockerfile
├─ README.md
├─ .env.example
├─ compose.yml          # Base: db + adminer + webapp
├─ compose.dev.yml      # DEV-Override: Ports auf 127.0.0.1 (Mac)
└─ compose.prod.yml     # PROD-Override: Cloudflared (Pi)

### Erklärungen zum compose-split und Aufbau
•	Base (compose.yml)
Enthält db, adminer, webapp — also alles, was man in beiden Umgebungen braucht.
Ports standardmäßig nur intern (expose), damit nichts direkt offen ist.<br>
•	Dev (compose.dev.yml)
Öffnet Ports für localhost:
	•	127.0.0.1:5001 -> webapp:5000
	•	127.0.0.1:8081 -> adminer:8080
	•	(Optional) 127.0.0.1:3306 -> db:3306 falls du mit einem lokalen Client arbeiten willst.
  <br>
•	Prod (compose.prod.yml)
Fügt cloudflared hinzu und verzichtet komplett auf Ports nach außen.
Zugriff auf Webapp/Adminer läuft dann über den Tunnel.

👉 Damit gibt es eine einzige Quelle für alle Services (Base), und  mit kleinen Overrides steuert man, wie sie nach außen erreichbar sind.
<br><br>
## CI/CD Deployment
### DEV (MacMini)
```bash
docker compose -f compose.yml -f compose.dev.yml up -d --build
```
	•	Webapp: http://127.0.0.1:5001
	•	Adminer: http://127.0.0.1:8081

### PROD (Pi)
```bash
docker compose -f compose.yml -f compose.prod.yml up -d --build
```

### Checkliste
```bash
cd /home/pi/Dietipi-App
git pull
test -f web/.env && echo "✅ env ok" || (echo "❌ web/.env fehlt"; exit 1)
docker compose -f compose.yml -f compose.prod.yml config >/dev/null || exit 1
docker compose -f compose.yml -f compose.prod.yml up -d --build
docker compose -f compose.yml -f compose.prod.yml ps
````
### Optional logs
```bash
docker compose -f compose.yml -f compose.prod.yml logs -n 50 webapp
docker compose -f compose.yml -f compose.prod.yml logs -n 50 cloudflared


### deploy-script auf dem Pi
deploy.sh (im Repo ablegen, einmal ausführbar machen chmod +x deploy.sh)
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "▶ git pull"; git pull
[ -f web/.env ] || { echo "❌ web/.env fehlt"; exit 1; }
echo "▶ compose check"; docker compose -f compose.yml -f compose.prod.yml config >/dev/null
echo "▶ deploy"; docker compose -f compose.yml -f compose.prod.yml up -d --build
echo "✅ done"; docker compose -f compose.yml -f compose.prod.yml ps
````
Aufruf mit 
```bash
./deploy.sh
````
