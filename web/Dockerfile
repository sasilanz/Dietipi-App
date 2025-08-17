FROM python:3.12-slim

# Arbeitsverzeichnis
WORKDIR /app

# Schnellere, sauberere Python-Defaults
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Abhängigkeiten installieren
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# App-Code ins Image (wir mounten gleich zusätzlich als Volume zum Live-Reload)
COPY app /app/app

# Flask-Defaults
ENV FLASK_APP=app.app:app
ENV FLASK_RUN_HOST=0.0.0.0

# Start
CMD ["flask", "run", "-p", "5000"]
