📘 IT-Kurs Webapp – Deployment & Nutzung

Dieses Dokument beschreibt den aktuellen Workflow für Development und Production inklusive Git-Workflow, .env-Handhabung und Deployment-Checkliste.

⸻

📂 Projektstruktur (relevant für Docker)

senitkurs/
├── compose.yml          # Basis-Setup (DB, Adminer, Webapp)
├── compose.dev.yml      # Dev-spezifische Overrides (Flask, Ports)
├── compose.prod.yml     # Prod-spezifische Overrides (gunicorn, Cloudflared)
├── deploy_prod.sh       # Script für Prod-Deployment auf dem Pi
├── web/
│   ├── Dockerfile
│   ├── app/
│   └── ...
└── .env                 # im Projektroot, enthält alle Secrets


⸻

🔑 .env Dateien

Alle geheimen Variablen liegen nur lokal in .env (nicht im Repo).

Beispiel .env (Projektroot):

DB_ROOT_PASSWORD=supersecretroot
DB_NAME=beispiel
DB_USER=beispiel
DB_PASSWORD=beispiel
DATABASE_URL=mysql+pymysql://beispieluser:beispielpw@db:3306/db-name
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoi...
FLASK_DEBUG=0

Zusätzlich im Repo: .env.example → Dummy-Werte als Vorlage.

⸻

🛠️ Development

Start (lokal):

docker compose -f compose.yml -f compose.dev.yml up --build

Zugriff:
	•	Webapp: http://localhost:5001
	•	Adminer: http://localhost:8081

⸻

🚀 Production

Deployment (auf dem Pi):

./deploy_prod.sh

Zugriff:
	•	Webapp über dieti-it.ch
	•	Adminer über adminer.dieti-it.ch

⸻

✅ Pre-Deploy Checkliste (Prod)
	1.	Secrets prüfen → .env im Projektroot muss enthalten:
	•	DB_ROOT_PASSWORD
	•	DB_NAME
	•	DB_USER
	•	DB_PASSWORD
	•	CLOUDFLARE_TUNNEL_TOKEN
	2.	Git-Stand prüfen:

git status
git pull


	3.	Auf dem Pi:

cd ~/senitkurs
./deploy_prod.sh


	4.	Kontrolle:

docker compose -f compose.yml -f compose.prod.yml ps
docker compose -f compose.yml -f compose.prod.yml logs -n 20 webapp

→ Webapp muss mit gunicorn laufen, Cloudflared ohne Fehler.

⸻

📝 Git Spickzettel

Status & Commits

git status                  # Überblick
git add <file>              # Änderungen vormerken
git commit -m "Message"     # Commit erstellen
git log --oneline           # Verlauf kompakt

Remote

git pull                    # Änderungen holen
git push                    # Änderungen hochladen
git remote -v               # Remote-URL prüfen

Revert / Reset

git checkout -- <file>      # Lokale Änderung verwerfen
git revert <commit>         # Commit rückgängig machen (neuer Commit)
git reset --hard <commit>   # Alles auf alten Stand zurücksetzen (Vorsicht!)


⸻

📋 ToDos / Ideen
	•	evtl. noch Adminer-Access absichern (Passwort oder Access nur intern)
	•	später: Logs zentralisieren
	•	evtl. automatisches Backup der DB