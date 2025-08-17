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
tree -a
.
├── .DS_Store
├── .git
│   ├── COMMIT_EDITMSG
│   ├── HEAD
│   ├── config
│   ├── description
│   ├── hooks
│   │   ├── applypatch-msg.sample
│   │   ├── commit-msg.sample
│   │   ├── fsmonitor-watchman.sample
│   │   ├── post-update.sample
│   │   ├── pre-applypatch.sample
│   │   ├── pre-commit.sample
│   │   ├── pre-merge-commit.sample
│   │   ├── pre-push.sample
│   │   ├── pre-rebase.sample
│   │   ├── pre-receive.sample
│   │   ├── prepare-commit-msg.sample
│   │   ├── push-to-checkout.sample
│   │   └── update.sample
│   ├── index
│   ├── info
│   │   └── exclude
│   ├── logs
│   │   ├── HEAD
│   │   └── refs
│   │       ├── heads
│   │       │   └── main
│   │       └── remotes
│   │           └── origin
│   │               └── main
│   ├── objects
│   │   ├── 0a
│   │   │   └── ef7935ef823c763143c1e64b89bb878eaa636f
│   │   ├── 0d
│   │   │   └── 0a48be5dbbdc177bb869a2cbd58400723ed278
│   │   ├── 17
│   │   │   └── 443e133dcfc74cd23f017a8dc59312cafb70db
│   │   ├── 1c
│   │   │   └── 2414c142b2a47985ec16b5ee4ddb7780bd1079
│   │   ├── 28
│   │   │   └── 4406afe4e1d11308135041f6593447f8544125
│   │   ├── 2c
│   │   │   └── 0f0154c063aa90c7d2f65e2e77dd25d805f073
│   │   ├── 2d
│   │   │   ├── a76eeb8af7ab84cc70962609d63ef4c53faaaa
│   │   │   └── d7b9bc17324f61f271eefe6de79c772970c52e
│   │   ├── 3b
│   │   │   └── e8f966be32f3cede0f3af5d9e5680404a680d4
│   │   ├── 3c
│   │   │   └── 108b9d5bc827ee666e617989abd7e3b3983ee4
│   │   ├── 3e
│   │   │   └── 1afe26d91c67a55b48e304d7a86dafe67d86a9
│   │   ├── 42
│   │   │   └── 229e2a4da6411fe2b67d65174daff373b4ce6b
│   │   ├── 46
│   │   │   └── a1dc9f90d1d33f266f6d94a0480ba6b32b77a5
│   │   ├── 48
│   │   │   └── 6e87239230f987835e98bd6c06626d976e3eae
│   │   ├── 51
│   │   │   └── ecbfede0aa308b033be9b58b62a0081ee091e8
│   │   ├── 66
│   │   │   └── 2a051297f0b5a87f171238dc1fdf2f74211ad2
│   │   ├── 67
│   │   │   ├── b586034ce10c8d8bdd8410057b528ea41882a2
│   │   │   └── ee6b4200980efe82531f224bdf4f2ab3813d68
│   │   ├── 68
│   │   │   └── 365fe6d0bbd7e117390c50e56c1fedb5ada74b
│   │   ├── 72
│   │   │   └── adbe01bb11ad57c94beb47a1d04072f62dcbc5
│   │   ├── 81
│   │   │   └── 6b8f7c46f3d4f7a9307fe968c8049ddbf5a497
│   │   ├── 82
│   │   │   └── 16560bc366e85b477da2b574708f2b09a722ac
│   │   ├── 84
│   │   │   └── 77074acdf296aececf842638ba1c57c427cb12
│   │   ├── 87
│   │   │   └── 7268c9b0820efc39d08c5ca4ac16eae1c2ece0
│   │   ├── 8c
│   │   │   └── ae86fed1e8a3cb5a85a4d00f25d8375b46b9e3
│   │   ├── 91
│   │   │   └── d916825d2a4077fec578b25c4c3627535bd0a6
│   │   ├── 93
│   │   │   └── 22134ec4c96e5326977d5523cd29fc05bfbb16
│   │   ├── 99
│   │   │   └── 3c894d693548dac12a8590d04f1724454c3a66
│   │   ├── 9b
│   │   │   └── 7df0e6fac09e2dc3fcfce2404fa7490f45a02a
│   │   ├── a7
│   │   │   └── cb3a06de6df604a03e9e0c0578c235961d5476
│   │   ├── a8
│   │   │   └── f46660aea4710187c6b1e76ea5464b07ec82d2
│   │   ├── ae
│   │   │   └── 318612463b2d94fd9410063c0f643c4296cfc3
│   │   ├── b2
│   │   │   └── 40970e68fcc1b097430302590e4b08f7babfeb
│   │   ├── b7
│   │   │   └── f94de4edf82a5f9e14264a7adf65d748d362dd
│   │   ├── c3
│   │   │   └── 9bd9389d972af18a5be6b781174f1f36eb54f9
│   │   ├── d4
│   │   │   └── a51e285215c2085ca43e45c7728619a52974a8
│   │   ├── d7
│   │   │   └── 56c9b1e71991cd016348eb44b85d4de8b8ade4
│   │   ├── da
│   │   │   └── 00777dd605ea7b141b8d0d7381339245761f6b
│   │   ├── df
│   │   │   └── e66547c045c6706c8ecb55c6665a497bf2b98c
│   │   ├── e6
│   │   │   └── 9de29bb2d1d6434b8b29ae775ad8c2e48c5391
│   │   ├── e8
│   │   │   └── 0aae62a9a223b8f508fca27ca47ce7f4b23a1b
│   │   ├── ea
│   │   │   └── a1e02b4275ff807d3c5870916e4d71c4f2eac3
│   │   ├── fc
│   │   │   └── 51e8fd34507a6444fb87090d45fd66ab74aba0
│   │   ├── fe
│   │   │   └── baf0ccb4ae23296b74d962a2978298b49c6feb
│   │   ├── info
│   │   └── pack
│   └── refs
│       ├── heads
│       │   └── main
│       ├── remotes
│       │   └── origin
│       │       └── main
│       └── tags
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

68 directories, 102 files
```

## 6. Nützliche Compose‑Befehle
```bash
docker compose up -d                 # alles starten
docker compose build webapp          # Web-Image neu bauen
docker compose up -d webapp          # Web neu starten
docker compose logs -f webapp        # Web-Logs ansehen
```
