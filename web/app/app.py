from flask import Flask, render_template, request, redirect, url_for, abort, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from functools import wraps
from .models import Base, Participant
import os, json, requests
from datetime import datetime
from .forms import RegisterForm


try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Zurich")
except Exception:
    TZ = None

# JSON liegt in web/app/content/alle_kurse.json
COURSE_JSON = os.path.join(os.path.dirname(__file__), "content", "alle_kurse.json")

def load_courses():
    with open(COURSE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def course_label(course_id: str) -> str:
    for c in load_courses():
        if c.get("id") == course_id:
            return c.get("label", course_id)
    return course_id

# --- App zuerst! ---
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# --- Konfig / Globals ---
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# DB-Engine
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, pool_pre_ping=True) if DB_URL else None

# Tabellen & Session
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

# --- Helpers ---
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get("admin") or request.headers.get("X-Admin-Token")
        if token != ADMIN_TOKEN:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def load_kurs(slug: str):
    """Lädt content/kurs_<slug>.json und gibt ein Dict zurück oder None."""
    base_dir = os.path.dirname(__file__)
    pfad = os.path.join(base_dir, "content", f"kurs_{slug}.json")
    if not os.path.exists(pfad):
        return None
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)

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

# --- Routen ---
@app.get("/")
def index():
    return render_template("index.html")

@app.get("/kursleitung")
def kursleitung():
    return render_template("kursleitung.html")

@app.route("/anmeldung", methods=["GET", "POST"])
def anmeldung():
    form = RegisterForm()

    # Kurse laden (existierende Funktion)
    courses = load_courses()

    # Formular-Kurswahl mit sichtbaren Kursen befüllen
    form.course_id.choices = [(c["id"], c["label"]) for c in courses if c.get("visible", False)]

    info = None

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

        # Speichern in Datenbank (beste Logik bleibt)
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
        # Zusatztext nur für kopie-mail:
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

@app.get("/kurs/<slug>")
def kurs_info(slug):
    kurs = load_kurs(slug)
    if not kurs:
        return ("<p class='error'>Kurs nicht gefunden.</p>"
                "<p><a href='/'>Zur Startseite</a></p>"), 404
    return render_template("kurs_info.html", kurs=kurs)

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
    last  = request.form.get("last_name", "").strip()
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

        # E‑Mail‑Duplikate vermeiden (eigenes ID zulassen)
        exists = s.query(Participant).filter(Participant.email == email, Participant.id != pid).first()
        if exists:
            return ("<p class='error'>Diese E‑Mail ist bereits vergeben.</p>"
                    f"<p><a href='/teilnehmende/{pid}/edit'>Zurück</a></p>"), 409

        p.first_name = first
        p.last_name  = last
        p.email      = email
        p.phone      = phone
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
    last  = request.form.get("last_name", "").strip()
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

if __name__ == "__main__":
    app.run(debug=True)

@app.get("/unterlagen")
def unterlagen():
    return render_template("unterlagen.html")

@app.get("/unterlagen/grundkurs")
def unterlagen_grundkurs():
    return render_template("unterlagen_grundkurs.html")

