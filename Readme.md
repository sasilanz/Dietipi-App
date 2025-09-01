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

## 2. Wichtige Konfigfiles
- **Navigation, Grundlayout, Footer, globale Stile:**  
  `templates/base.html` und `static/css/style.css`
- **Startseiten‑Inhalt:**  
  `templates/index.html`
- **Admin‑Seiten (Teilnehmende):**  
  `templates/list_participants.html`, `add_participant.html`, `edit_participant.html`
- **Routen/Logik/DB:**  
  `app.py`, `models.py`, forms.py, markdown_loader.py, content_loader.py

## 3. Admin‑Schutz (Token)
- In `web/.env` in .gitignore, dh nicht auf github:
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
- Auf **alle Admin‑Routen** angewendet (siehe in app.py wo mit @require_admin dekoriert sind):
  ```python
  @app.get("/teilnehmende") @require_admin
  @app.get("/teilnehmende/new") @require_admin
  @app.post("/teilnehmende/new") @require_admin
  @app.get("/teilnehmende/<int:pid>/edit") @require_admin
  @app.post("/teilnehmende/<int:pid>/edit") @require_admin
  @app.post("/teilnehmende/<int:pid>/delete") @require_admin
  @app.post("/teilnehmende/<int:pid>/paid")
  ```
- **Count** kann öffentlich bleiben, ist nicht auf der webseite implementiert:
  ```python
  @app.get("/teilnehmende/count")
  ```
- **Admin‑Hub**:
  ```python
  @app.get("/_admin") @require_admin
  def admin_home():
      return render_template("admin_home.html", token=ADMIN_TOKEN)
  ```
  Aufrufen mit: `http://localhost:5001/_admin?admin=DEIN_TOKEN`

## 4. URLs
- **Öffentlich:** `/` (Startseite), `/teilnehmende/count`
- **Admin:** `/_admin?admin=TOKEN`, `/teilnehmende?admin=TOKEN`, `/teilnehmende/new?admin=TOKEN`, `/teilnehmende/<id>/edit?admin=TOKEN`

## 5. Projektstruktur (relevant)
```
tree -a -I .git
.
├── changelog.md
├── compose.dev.yml
├── compose.prod.yml
├── compose.yml
├── deployment.Readme.md
├── Doks
│   ├── chat_index.md
│   ├── content.md
│   ├── entscheidungsprotokoll.md
│   ├── kursinhalte.md
│   ├── kursportal_struktur.pdf
│   ├── unterlagen_architektur.md
│   ├── unterlagen_konzept.md
│   └── webapp.md
├── .DS_Store
├── .env
├── .env.example
├── .gitignore
├── git_spickzettel.md
├── Readme.md
└── web
    ├── app
    │   ├── app.py
    │   ├── content
    │   │   ├── .DS_Store
    │   │   ├── meta
    │   │   │   ├── aufbaukurs.json
    │   │   │   ├── courses.json
    │   │   │   ├── grundkurs-2025.json
    │   │   │   └── home.json
    │   │   └── unterlagen
    │   │       ├── .DS_Store
    │   │       ├── durchfuehrungen
    │   │       │   ├── .DS_Store
    │   │       │   └── grundkurs-2025-10-02-di
    │   │       │       ├── assets
    │   │       │       │   └── bank_qr.png
    │   │       │       ├── .DS_Store
    │   │       │       ├── L01
    │   │       │       │   ├── index.md
    │   │       │       │   └── testbild.png
    │   │       │       ├── L02
    │   │       │       │   └── index.md
    │   │       │       └── L03
    │   │       │           ├── asi_handpan.jpg
    │   │       │           ├── echoes_cover.jpeg
    │   │       │           └── index.md
    │   │       └── .gitkeep
    │   ├── .DS_Store
    │   ├── forms.py
    │   ├── __init__.py
    │   ├── models.py
    │   ├── static
    │   │   ├── css
    │   │   │   └── style.css
    │   │   ├── docs
    │   │   │   ├── .DS_Store
    │   │   │   ├── grundkurs-2025
    │   │   │   │   ├── .DS_Store
    │   │   │   │   └── G-L01-handout.pdf
    │   │   │   └── promo
    │   │   │       ├── .DS_Store
    │   │   │       └── Flyer-IT-Kurs-Dietikon.pdf
    │   │   ├── .DS_Store
    │   │   └── img
    │   │       ├── astrid.png
    │   │       ├── bank_qr.png
    │   │       ├── .DS_Store
    │   │       └── l-con_logo.png
    │   ├── templates
    │   │   ├── add_participant.html
    │   │   ├── admin_home.html
    │   │   ├── base.html
    │   │   ├── edit_participant.html
    │   │   ├── flyer.html
    │   │   ├── index.html
    │   │   ├── kursbeschreibung.html
    │   │   ├── kursleitung.html
    │   │   ├── kursliste.html
    │   │   ├── list_participants.html
    │   │   ├── partials
    │   │   │   ├── kurs_liste.html
    │   │   │   └── kurs_liste_info.html
    │   │   ├── payment.html
    │   │   ├── register.html
    │   │   ├── register_success.html
    │   │   ├── unterlagen.html
    │   │   ├── unterlagen_kurs.html
    │   │   └── unterlagen_lektion.html
    │   └── utils
    │       ├── content_loader.py
    │       ├── __init__.py
    │       └── markdown_loader.py
    ├── Dockerfile
    ├── .DS_Store
    └── requirements.txt
```

## 6. CI/CD Deployment

### DEV (MacMini)
```bash
docker compose -f compose.yml -f compose.dev.yml up -d --build
```
	•	Webapp: http://127.0.0.1:5001
	•	Adminer: http://127.0.0.1:8081

### PROD (Pi)
```bash
cd /home/pi/Dietipi-App
git pull
docker compose -f compose.yml -f compose.prod.yml up -d --build
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
cd /home/pi/Dietipi-App
git pull
docker compose -f compose.yml -f compose.prod.yml up -d --build
```



### Checkliste
## PROD auf dem Pi
```bash
cd /home/pi/Dietipi-App
git pull
test -f web/.env && echo "✅ env ok" || (echo "❌ web/.env fehlt"; exit 1)
docker compose -f compose.yml -f compose.prod.yml config >/dev/null || exit 1
docker compose -f compose.yml -f compose.prod.yml up -d --build
docker compose -f compose.yml -f compose.prod.yml ps
````


### CHECKS
Prüfen, ob .env im Projekt-Root vorhanden ist:
```bash
test -f .env && echo "✅ .env vorhanden" || echo "❌ .env fehlt!"
````
# Tunnel status
docker compose -f compose.yml -f compose.prod.yml logs -n 30 cloudflared

# Zustand prüfen
```bash
docker compose -f compose.yml -f compose.prod.yml ps

# Webapp reachable aus dem Netz?
curl -I https://dieti-it.ch

# Database Administration
adminer.dieti-pi.ch

### LOGS
docker compose -f compose.yml -f compose.prod.yml logs -n 50 webapp
docker compose -f compose.yml -f compose.prod.yml logs -n 50 cloudflared


### GIT Spickzettel

💡 Tipp (falls VSCode beim commiten hängenbleibt):
Im VS Code-Terminal direkt committen:
```bash
git add -A
git commit -m "kurze message"
git push
```

### Security and Monitoring Features added 1.9.2025

🔒 Security Enhancements:
- Add rate limiting on registration endpoint (5 req/5min)
- Implement security headers (CSP, XSS protection, HSTS)
- Add input sanitization and enhanced validation
- Create Swiss phone number and email validation with typo detection

🛡️ Error Handling & Reliability:
- Add global error handlers with custom error pages (404, 403, 500)
- Implement comprehensive logging throughout application
- Add database session management with proper error handling
- Create graceful error recovery and user-friendly error messages

📊 Monitoring & Observability:
- Add health check endpoints (/health, /health/ready, /health/live)
- Implement database connectivity monitoring
- Add metrics endpoint for application monitoring
- Create structured logging with proper error tracking

⚡ Performance & Optimization:
- Implement in-memory caching system for courses (10min TTL)
- Add database indexes on frequently queried columns
- Optimize database operations with connection pooling
- Cache course loading to reduce I/O operations

<0001f9ea> Testing & Quality:
- Add comprehensive testing framework with pytest
- Create test fixtures and mocks for all major components
- Add validation tests for security functions
- Implement CI/CD ready test structure

🏗️ Code Architecture:
- Modularize code into separate concerns (security, monitoring, database)
- Add enhanced form validation with custom validators
- Implement proper dependency management and fix duplicate requirements
- Create reusable database utilities and session management

✨ Additional Features:
- Add admin monitoring capabilities
- Implement proper timezone handling
- Create email validation with common typo detection
- Add Swiss-specific phone number validation

## Database backup config and procedure
•  Option 1: compose.backup.yml - Simple 6-hour loop
•  Option 2: compose.backup-cron.yml - Cron every 6 hours (00:00, 06:00, 12:00, 18:00)
•  Option 3: compose.backup-daily.yml - Daily at 2 AM


🆘 Emergency Procedures:

•  Manual backup: docker compose exec backup /usr/local/bin/backup.sh
•  Restore latest: docker compose exec backup /usr/local/bin/restore.sh latest
•  List backups: docker compose exec backup /usr/local/bin/restore.sh

# Add backup service to production deployment
docker compose -f compose.yml -f compose.prod.yml -f compose.backup.yml up -d