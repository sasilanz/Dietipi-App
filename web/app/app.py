from flask import Flask, render_template, request, redirect, url_for, abort, flash, send_file, send_from_directory 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from functools import wraps
from .models import Base, Participant
import os, json, requests, re, yaml
from datetime import datetime
from .forms import RegisterForm
from .utils.content_loader import load_json
from pathlib import Path
from .utils.markdown_loader import list_lessons, render_lesson, course_dir, rewrite_relative_urls

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Zurich")
except Exception:
    TZ = None


# --- Helper: Kurse laden (einheitliche Quelle) ---
def load_courses():
    """
    Bevorzugt meta/courses.json, fallback auf content/alle_kurse.json (über load_json).
    """
    try:
        return load_json("courses.json")
    except FileNotFoundError:
        # Legacy-Name als Fallback (falls courses.json noch nicht existiert)
        return load_json("alle_kurse.json")


def course_label(course_id: str) -> str:
    for c in load_courses():
        if c.get("id") == course_id:
            return c.get("label", course_id)
    return course_id

def _split_front_matter(md_text: str):
    if md_text.startswith("---"):
        parts = md_text.split("\n---", 1)
        if len(parts) == 2:
            fm = parts[0][3:]  # ohne führendes ---
            body = parts[1].lstrip("\n")
            try:
                meta = yaml.safe_load(fm) or {}
            except Exception:
                meta = {}
            return meta, body
    return {}, md_text

def _rewrite_relative_links(md_text: str, content_slug: str, lesson_id: str):
    # ./foo -> /u-asset/<course>/<lesson_id>/foo
    base_lesson = url_for("unterlagen_asset", course=content_slug, subpath=f"{lesson_id}/")
    md_text = md_text.replace("](./", f"]({base_lesson}")

    # ../assets/foo -> /u-asset/<course>/assets/foo
    base_assets = url_for("unterlagen_asset", course=content_slug, subpath="assets/")
    md_text = md_text.replace("](../assets/", f"]({base_assets}")

    return md_text

# --- App / Config ---
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, pool_pre_ping=True) if DB_URL else None

if engine:
    Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine) if engine else None


@app.context_processor
def inject_admin_flag():
    is_admin = (
        request.args.get("admin") == ADMIN_TOKEN
        or request.headers.get("X-Admin-Token") == ADMIN_TOKEN
    )
    return dict(is_admin=is_admin, token=(ADMIN_TOKEN if is_admin else None))


# --- Admin Decorator ---
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get("admin") or request.headers.get("X-Admin-Token")
        if token != ADMIN_TOKEN:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# --- Mail ---
def send_email_api(to_email: str, subject: str, html: str, text: str = ""):
    """Versendet E‑Mails über Resend HTTP-API. Erwartet ENV:
       EMAIL_PROVIDER=resend, RESEND_API_KEY=..., EMAIL_FROM=info@dieti-it.ch
    """
    if os.getenv("EMAIL_PROVIDER") != "resend":
        print("[WARN] EMAIL_PROVIDER != 'resend' – Versand übersprungen")
        return
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[WARN] RESEND_API_KEY fehlt – Versand übersprungen")
        return

    from_addr = os.getenv("EMAIL_FROM", "info@dieti-it.ch")

    payload = {
        "from": f"IT‑Kurs Dietikon <{from_addr}>",
        "to": [to_email],
        "subject": subject,
        "html": html
    }
    if text:
        payload["text"] = text

    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload, timeout=15
    )
    r.raise_for_status()


# --- Routen: Public ---
@app.get("/")
def index():
    # Startseite kann (optional) sichtbare Kurse anzeigen
    courses = [c for c in load_courses() if c.get("visible", False)]
    return render_template("index.html", courses=courses)

# Direct PDF serving for flyer
@app.get("/flyer")
def flyer():
    return send_file("static/docs/promo/Flyer-IT-Kurs-Dietikon.pdf", mimetype="application/pdf")


# Kurs-Übersicht (Info-Liste)
@app.get("/kursliste", endpoint="kursliste")
def kursliste():
    courses = [c for c in load_courses() if c.get("visible", False)]
    return render_template("kursliste.html", courses=courses)


# Kurs-Onepager (Beschreibung) – Daten aus meta/<slug>.json, 
@app.get("/kurs/<slug>", endpoint="kursbeschreibung")
def kursbeschreibung_view(slug):
    """
    Kurs-Onepager (Beschreibung):
    - Basisdaten aus courses.json (nur sichtbare Kurse)
    - Detaildaten aus meta/<beschreibung_slug|typ|slug>.json
    """
    # Basisdaten (Status, Preis etc.) aus courses.json
    basis = next(
        (c for c in load_courses() if c.get("visible", False) and c.get("id") == slug),
        None,
    )
    if not basis:
        return (
            f"<p>Kurs nicht gefunden.</p>"
            f"<p><a href='{url_for('kursliste')}'>Zur Übersicht</a></p>"
        ), 404

    # Detaildaten (Titel, Untertitel, Themen ...) – bevorzugt beschreibung_slug
    meta_slug = basis.get("beschreibung_slug") or slug
    candidates = [meta_slug]
    if basis.get("typ"):
        candidates.append(basis["typ"])
    candidates.append(slug)

    detail = {}
    for name in dict.fromkeys(candidates):  # entdoppeln, Reihenfolge bewahren
        try:
            detail = load_json(f"{name}.json")  # sucht meta/<name>.json bevorzugt
            break
        except FileNotFoundError:
            continue

    # Merge: Detail überschreibt Basis bei gleichen Keys
    kurs = {**basis, **detail}
    return render_template("kursbeschreibung.html", kurs=kurs)

@app.get("/kursleitung")
def kursleitung():
    return render_template("kursleitung.html")


@app.route("/anmeldung", methods=["GET", "POST"])
def anmeldung():
    form = RegisterForm()

    courses = load_courses()
    # Formular-Kurswahl mit sichtbaren Kursen befüllen
    form.course_id.choices = [(c["id"], c["label"]) for c in courses if c.get("visible", False)]

    if form.validate_on_submit():
        first = form.first_name.data.strip()
        last = form.last_name.data.strip()
        email = form.email.data.strip().lower() if form.email.data else None
        phone = form.phone.data.strip() if form.phone.data else None
        course_id = form.course_id.data

        # Kurs-Label ermitteln für DB / Mail
        selected_course_label = next((c["label"] for c in courses if c["id"] == course_id), None)

        if not email:
            return render_template(
                "register.html",
                form=form,
                show_no_email_hint=True,
                phone="076 497 42 62"
            )

        # Speichern in Datenbank
        try:
            with SessionLocal() as s:
                p = Participant(
                    first_name=first,
                    last_name=last,
                    email=email,
                    phone=phone,
                    course_name=selected_course_label,
                )
                s.add(p)
                s.commit()
        except IntegrityError:
            flash("Diese E-Mail ist bereits registriert.", "error")
            return render_template("register.html", form=form)

        # Bestätigungs‑Mail via Resend
        subject = "Bestätigung deiner Anmeldung – IT-Kurs Dietikon"
        html = f"""
        <p>Hallo {first} {last},</p>
        <p>Vielen Dank für Deine Anmeldung zum SeniorInnen IT-Kurs in Dietikon.</p>
        <br><br>
        <p>Mit diesem Link bekommst Du Infos zum Bezahlen der Kursgebühr:</p>
        <br><br>
        <p style="margin:16px 0;">
        <a href="https://dieti-it.ch/zahlung"
            style="display:inline-block;
                    padding:10px 16px;
                    background-color:#28a745;
                    color:#ffffff;
                    text-decoration:none;
                    border-radius:6px;
                    font-weight:600;">
            💳 Jetzt bezahlen
        </a>
        </p>
        <br><br>
        <p>Falls der Button nicht funktioniert, nutze diesen Link:<br>
        <a href="https://dieti-it.ch/zahlung">https://dieti-it.ch/zahlung</a>
        </p>
        <br>
        <p>Herzliche Grüsse und bis bald<br><br>Astrid<br>IT-Kurs Dietikon</p>
        """
        ts = (datetime.now(TZ) if TZ else datetime.now()).strftime("%d.%m.%Y %H:%M")
        admin_html = f"""
        <p><strong>Neue Anmeldung</strong></p>
        <ul>
        <li><strong>Name:</strong> {first} {last}</li>
        <li><strong>E-Mail:</strong> {email}</li>
        <li><strong>Kurs:</strong> {selected_course_label}</li>
        <li><strong>Datum/Zeit:</strong> {ts}</li>
        </ul>
        <hr>
        {html}
        """

        try:
            send_email_api(email, subject, html)
            send_email_api("astrid@dieti-it.ch", f"[Kopie] {subject}", admin_html)
        except Exception as e:
            print(f"[WARN] Bestätigungs-Mail fehlgeschlagen: {e}")

        return render_template("register_success.html", first=first)

    # GET oder Fehlerfall
    return render_template("register.html", form=form)


@app.get("/zahlung")
def payment_info():
    payment = {
        "display_name": os.getenv("PAYEE_DISPLAY_NAME", "IT-Kurs Dietikon"),
        "legal_name": os.getenv("PAYEE_LEGAL_NAME", ""),
        "iban": os.getenv("PAYEE_IBAN", ""),
        "bic": os.getenv("PAYEE_BIC", ""),
        "bank": os.getenv("PAYEE_BANK", ""),
        "purpose_prefix": os.getenv("PAYMENT_PURPOSE_PREFIX", "Kursgebühr"),
        "contact_email": os.getenv("PAYMENT_EMAIL", ""),
    }
    return render_template("payment.html", payment=payment)


# --- Routen: Admin / Teilnehmende ---
@app.get("/teilnehmende/count")
def count_participants():
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500
    with SessionLocal() as s:
        n = s.query(Participant).count()
    return {"participants": n}


@app.get("/teilnehmende/new")
@require_admin
def new_participant_form():
    return render_template("add_participant.html")


@app.get("/teilnehmende/<int:pid>/edit")
@require_admin
def edit_participant(pid: int):
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500
    with SessionLocal() as s:
        p = s.get(Participant, pid)
        if not p:
            return ("<p class='error'>Teilnehmer:in nicht gefunden.</p>"
                    "<p><a href='/teilnehmende'>Zur Liste</a></p>"), 404
    return render_template("edit_participant.html", p=p)


@app.post("/teilnehmende/<int:pid>/edit")
@require_admin
def update_participant(pid: int):
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500

    first = request.form.get("first_name", "").strip()
    last = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip() or None

    if not first or not last or not email:
        return ("<p class='error'>Bitte Vorname, Nachname und E‑Mail angeben.</p>"
                f"<p><a href='/teilnehmende/{pid}/edit'>Zurück</a></p>"), 400

    with SessionLocal() as s:
        p = s.get(Participant, pid)
        if not p:
            return ("<p class='error'>Teilnehmer:in nicht gefunden.</p>"
                    "<p><a href='/teilnehmende'>Zur Liste</a></p>"), 404

        exists = s.query(Participant).filter(Participant.email == email, Participant.id != pid).first()
        if exists:
            return ("<p class='error'>Diese E‑Mail ist bereits vergeben.</p>"
                    f"<p><a href='/teilnehmende/{pid}/edit'>Zurück</a></p>"), 409

        p.first_name = first
        p.last_name = last
        p.email = email
        p.phone = phone
        s.commit()

    return redirect(url_for("list_participants"))


@app.get("/teilnehmende")
@require_admin
def list_participants():
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500
    with SessionLocal() as s:
        participants = s.query(Participant).order_by(Participant.created_at.desc()).all()
    return render_template("list_participants.html", participants=participants, token=ADMIN_TOKEN)


@app.post("/teilnehmende/<int:pid>/paid")
@require_admin
def set_paid(pid: int):
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500

    set_flag = 1 if (request.form.get("set") == "1") else 0
    now = datetime.now(TZ) if TZ else datetime.now()

    with SessionLocal() as s:
        p = s.get(Participant, pid)
        if not p:
            return ("<p class='error'>Teilnehmer:in nicht gefunden.</p>"
                    "<p><a href='/teilnehmende'>Zur Liste</a></p>"), 404
        p.paid = bool(set_flag)
        p.payment_date = (now if set_flag else None)
        s.commit()

    return redirect(url_for("list_participants") + f"?admin={ADMIN_TOKEN}")


@app.post("/teilnehmende/new")
@require_admin
def create_participant():
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500

    first = request.form.get("first_name", "").strip()
    last = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip() or None

    if not first or not last or not email:
        return ("<p class='error'>Bitte Vorname, Nachname und E‑Mail angeben.</p>"
                "<p><a href='/teilnehmende/new'>Zurück</a></p>"), 400

    try:
        with SessionLocal() as s:
            s.add(Participant(first_name=first, last_name=last, email=email, phone=phone))
            s.commit()
    except IntegrityError:
        return ("<p class='error'>Diese E‑Mail existiert bereits.</p>"
                "<p><a href='/teilnehmende/new'>Zurück</a></p>"), 409

    return ("<p class='msg'>Gespeichert ✅</p>"
            "<p><a href='/teilnehmende/new'>Weiteren Eintrag anlegen</a> · "
            "<a href='/teilnehmende/count'>Anzahl ansehen</a></p>")


@app.post("/teilnehmende/<int:pid>/delete")
@require_admin
def delete_participant(pid: int):
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500
    with SessionLocal() as s:
        p = s.get(Participant, pid)
        if not p:
            return ("<p class='error'>Teilnehmer:in nicht gefunden.</p>"
                    "<p><a href='/teilnehmende'>Zur Liste</a></p>"), 404
        try:
            s.delete(p)
            s.commit()
        except Exception as e:
            return (f"<p class='error'>Löschen fehlgeschlagen: {e}</p>"
                    "<p><a href='/teilnehmende'>Zur Liste</a></p>"), 500
    return redirect(url_for("list_participants"))


@app.get("/_admin")
@require_admin
def admin_home():
    return render_template("admin_home.html", token=ADMIN_TOKEN)


# --- Unterlagen (Einstieg) ---
@app.get("/unterlagen", endpoint="unterlagen")
def unterlagen():
    courses = load_courses()
    visible = [c for c in courses if c.get("visible", False)]
    return render_template("unterlagen.html", courses=visible)

# Kurs-Unterlagen: Lektionsliste
@app.get("/unterlagen/<slug>", endpoint="unterlagen_kurs")
def unterlagen_kurs(slug):
    # nur Kurse zeigen, die es wirklich gibt (und sichtbar sind)
    kurs = next((c for c in load_courses() if c.get("visible", False) and c["id"] == slug), None)
    if not kurs:
        return ("<p>Kurs nicht gefunden.</p><p><a href='/unterlagen'>Zur Übersicht</a></p>"), 404

    lessons = list_lessons(slug)
    return render_template("unterlagen_kurs.html", kurs=kurs, lessons=lessons)


# Lektionsdetail: Markdown rendern
@app.get("/unterlagen/<slug>/<lesson_id>", endpoint="unterlagen_lektion")
def unterlagen_lektion(slug, lesson_id):
    kurs = next((c for c in load_courses() if c.get("visible", False) and c["id"] == slug), None)
    if not kurs:
        return ("<p>Kurs nicht gefunden.</p><p><a href='/unterlagen'>Zur Übersicht</a></p>"), 404

    meta, html, folder = render_lesson(slug, lesson_id)
    if not meta:
        return (f"<p>Lektion nicht gefunden.</p><p><a href='/unterlagen/{slug}'>Zurück</a></p>"), 404

    # relative Links/Bilder auf Media-Route umschreiben
    html = rewrite_relative_urls(html, slug, lesson_id )
    return render_template("unterlagen_lektion.html", kurs=kurs, meta=meta, html=html)


# Media-Auslieferung für Kurs-Unterlagen (sicher)
@app.get("/unterlagen/<slug>/media/<path:relpath>")
def unterlagen_media(slug, relpath):
    """
    Liefert Dateien relativ zum Kursordner content/unterlagen/<slug>/...
    Verhindert Ausbruch aus dem Kursordner.
    """
    base = course_dir(slug)
    target = (base / relpath).resolve()

    try:
        # Sicherheitscheck: target muss innerhalb von base liegen
        base_resolved = base.resolve()
        if not str(target).startswith(str(base_resolved)):
            return "Pfad nicht erlaubt", 403
        if not target.exists() or not target.is_file():
            return "Datei nicht gefunden", 404
        return send_file(target)
    except Exception as e:
        return (f"Fehler beim Laden der Datei: {e}", 500)

# --- Debug local ---
if __name__ == "__main__":
    app.run(debug=True)