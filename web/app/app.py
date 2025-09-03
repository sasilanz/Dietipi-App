# Standard library imports
import json
import logging
import re
from datetime import datetime
from functools import wraps
from pathlib import Path

# Third-party imports
import yaml
from flask import Flask, render_template, request, redirect, url_for, abort, flash, send_file, send_from_directory
from sqlalchemy.exc import IntegrityError

# Local imports
from .config import Config, create_database_engine, create_session_factory, get_payment_config, configure_logging
from .models import Base, Participant
from .forms import RegisterForm
from .utils.content_loader import load_json
from .utils.markdown_loader import list_lessons, render_lesson, course_dir, rewrite_relative_urls
from .email_service import send_registration_emails
from .error_handlers import register_error_handlers
from .security import register_security_features, rate_limit, sanitize_input
from .database import get_db_session, set_session_factory
from .monitoring import register_monitoring_endpoints
from .cache import cached, cache_courses_key

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


# --- Helper: Kurse laden (einheitliche Quelle) ---
@cached(key_func=cache_courses_key, ttl=600)  # Cache for 10 minutes
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
    """
    Gibt das menschenlesbare Label für eine Kurs-ID zurück.
    
    Args:
        course_id: Die eindeutige Kurs-ID
    
    Returns:
        str: Das Kurs-Label oder die ID selbst als Fallback
    """
    for c in load_courses():
        if c.get("id") == course_id:
            return c.get("label", course_id)
    return course_id

def _split_front_matter(md_text: str):
    """
    Trennt YAML Front-Matter vom Markdown-Body.
    
    Args:
        md_text: Markdown-Text möglicherweise mit Front-Matter
    
    Returns:
        tuple: (meta_dict, body_text)
    """
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
    """
    Schreibt relative Links in Markdown für Web-Anzeige um.
    
    Args:
        md_text: Markdown-Text mit relativen Links
        content_slug: Kurs-Slug für URL-Generierung
        lesson_id: Lektions-ID für URL-Generierung
    
    Returns:
        str: Markdown mit umgeschriebenen URLs
    """
    # ./foo -> /u-asset/<course>/<lesson_id>/foo
    base_lesson = url_for("unterlagen_asset", course=content_slug, subpath=f"{lesson_id}/")
    md_text = md_text.replace("](./", f"]({base_lesson}")

    # ../assets/foo -> /u-asset/<course>/assets/foo
    base_assets = url_for("unterlagen_asset", course=content_slug, subpath="assets/")
    md_text = md_text.replace("](../assets/", f"]({base_assets}")

    return md_text

# --- App / Config ---
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Database setup
engine = create_database_engine()
if engine:
    Base.metadata.create_all(bind=engine)
SessionLocal = create_session_factory(engine)

# Set global session factory for database module
set_session_factory(SessionLocal)


@app.context_processor
def inject_admin_flag():
    is_admin = (
        request.args.get("admin") == Config.ADMIN_TOKEN
        or request.headers.get("X-Admin-Token") == Config.ADMIN_TOKEN
    )
    return dict(is_admin=is_admin, token=(Config.ADMIN_TOKEN if is_admin else None))


# --- Admin Decorator ---
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get("admin") or request.headers.get("X-Admin-Token")
        if token != Config.ADMIN_TOKEN:
            abort(403)
        return f(*args, **kwargs)
    return decorated




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
@rate_limit(limit=5, window=300)  # 5 registrations per 5 minutes
def anmeldung():
    courses = load_courses()
    form = RegisterForm(course_loader_func=load_courses)

    # Formular-Kurswahl mit sichtbaren Kursen befüllen
    form.course_id.choices = [(c["id"], c["label"]) for c in courses if c.get("visible", False)]

    if form.validate_on_submit():
        first = form.first_name.data.strip()
        last = form.last_name.data.strip()
        email = form.email.data.strip().lower() if form.email.data else None
        phone = form.phone.data.strip() if form.phone.data else None
        course_id = form.course_id.data
        
        # Address fields
        street = form.street.data.strip() if form.street.data else None
        house_number = form.house_number.data.strip() if form.house_number.data else None
        postal_code = form.postal_code.data.strip() if form.postal_code.data else None
        city = form.city.data.strip() if form.city.data else None

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
                    street=street,
                    house_number=house_number,
                    postal_code=postal_code,
                    city=city,
                    course_name=selected_course_label,
                )
                s.add(p)
                s.commit()
        except IntegrityError:
            flash("Diese E-Mail ist bereits registriert.", "error")
            return render_template("register.html", form=form)

        # Bestätigungs‑Mail via Resend
        try:
            send_registration_emails(first, last, email, selected_course_label, Config.TIMEZONE)
        except Exception as e:
            logger.warning(f"E-Mail-Versand fehlgeschlagen: {e}")

        return render_template("register_success.html", first=first)

    # GET oder Fehlerfall
    return render_template("register.html", form=form)


@app.get("/zahlung")
def payment_info():
    payment = get_payment_config()
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
    return render_template("list_participants.html", participants=participants, token=Config.ADMIN_TOKEN)


@app.post("/teilnehmende/<int:pid>/paid")
@require_admin
def set_paid(pid: int):
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500

    set_flag = 1 if (request.form.get("set") == "1") else 0
    now = datetime.now(Config.TIMEZONE) if Config.TIMEZONE else datetime.now()

    with SessionLocal() as s:
        p = s.get(Participant, pid)
        if not p:
            return ("<p class='error'>Teilnehmer:in nicht gefunden.</p>"
                    "<p><a href='/teilnehmende'>Zur Liste</a></p>"), 404
        p.paid = bool(set_flag)
        p.payment_date = (now if set_flag else None)
        s.commit()

    return redirect(url_for("list_participants") + f"?admin={Config.ADMIN_TOKEN}")


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
    return render_template("admin_home.html", token=Config.ADMIN_TOKEN)


@app.get("/api/participants/stats")
@require_admin
def participants_stats():
    """API endpoint for participant statistics"""
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500
    
    with SessionLocal() as s:
        total = s.query(Participant).count()
        paid = s.query(Participant).filter(Participant.paid == True).count()
        unpaid = total - paid
    
    return {
        "total": total,
        "paid": paid,
        "unpaid": unpaid
    }


@app.get("/teilnehmende/export/csv")
@require_admin
def export_participants_csv():
    """Export participants as CSV file"""
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500
    
    import csv
    import io
    from flask import make_response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV Header
    writer.writerow([
        'ID', 'Vorname', 'Nachname', 'E-Mail', 'Telefon', 'Straße', 'Hausnummer', 'PLZ', 'Ort', 'Kurs',
        'Bezahlt', 'Zahlungsdatum', 'Erstellt'
    ])
    
    with SessionLocal() as s:
        participants = s.query(Participant).order_by(Participant.created_at.desc()).all()
        
        for p in participants:
            writer.writerow([
                p.id,
                p.first_name,
                p.last_name,
                p.email,
                p.phone or '',
                p.street or '',
                p.house_number or '',
                p.postal_code or '',
                p.city or '',
                p.course_name or '',
                'Ja' if p.paid else 'Nein',
                p.payment_date.strftime('%d.%m.%Y %H:%M') if p.payment_date else '',
                p.created_at.strftime('%d.%m.%Y %H:%M') if p.created_at else ''
            ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=teilnehmende.csv'
    
    return response


@app.post("/api/participants/<int:pid>/update")
@require_admin
def update_participant_field():
    """API endpoint for inline editing of participant fields"""
    if not SessionLocal:
        return {"error": "DB nicht konfiguriert"}, 500
    
    pid = request.view_args['pid']
    data = request.get_json()
    
    if not data or 'field' not in data or 'value' not in data:
        return {"error": "Ungültige Daten"}, 400
    
    field = data['field']
    value = data['value'].strip() if data['value'] else None
    
    # Validate allowed fields
    allowed_fields = ['first_name', 'last_name', 'email', 'phone']
    if field not in allowed_fields:
        return {"error": "Feld nicht erlaubt"}, 400
    
    with SessionLocal() as s:
        p = s.get(Participant, pid)
        if not p:
            return {"error": "Teilnehmer nicht gefunden"}, 404
        
        # Special validation for email
        if field == 'email' and value:
            value = value.lower()
            # Check if email already exists for another participant
            existing = s.query(Participant).filter(
                Participant.email == value, 
                Participant.id != pid
            ).first()
            if existing:
                return {"error": "E-Mail bereits vergeben"}, 409
        
        # Update the field
        setattr(p, field, value)
        
        try:
            s.commit()
            return {
                "success": True,
                "field": field,
                "value": value or "",
                "display_value": value or "—"
            }
        except Exception as e:
            s.rollback()
            return {"error": f"Speichern fehlgeschlagen: {str(e)}"}, 500


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

# Register additional modules
register_error_handlers(app)
register_security_features(app)
register_monitoring_endpoints(app)

# --- Debug local ---
if __name__ == "__main__":
    app.run(debug=True)
