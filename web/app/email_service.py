"""
Email service module for handling email operations.

This module provides functionality for sending emails via Resend API
and generating email templates for the IT-Kurs application.
"""

import os
import logging
from datetime import datetime
from typing import Optional

import requests


logger = logging.getLogger(__name__)


def send_email_api(to_email: str, subject: str, html: str, text: str = "") -> None:
    """
    Versendet E‑Mails über Resend HTTP-API.
    
    Args:
        to_email: Empfänger-E-Mail-Adresse
        subject: E-Mail-Betreff
        html: HTML-Inhalt der E-Mail
        text: Optional: Text-Version der E-Mail
    
    Raises:
        requests.exceptions.RequestException: Wenn der E-Mail-Versand fehlschlägt
        
    Note:
        Benötigt folgende Umgebungsvariablen:
        - EMAIL_PROVIDER=resend
        - RESEND_API_KEY
        - EMAIL_FROM (optional, default: info@dieti-it.ch)
    """
    if os.getenv("EMAIL_PROVIDER") != "resend":
        logger.warning("EMAIL_PROVIDER != 'resend' – Versand übersprungen")
        return
        
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY fehlt – Versand übersprungen")
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
        json=payload, 
        timeout=15
    )
    r.raise_for_status()


def create_registration_confirmation_email(first_name: str, last_name: str) -> str:
    """
    Erstellt den HTML-Inhalt für die Anmeldungsbestätigungs-E-Mail.
    
    Args:
        first_name: Vorname des Teilnehmers
        last_name: Nachname des Teilnehmers
        
    Returns:
        str: HTML-Inhalt für die E-Mail
    """
    return f"""
    <p>Hallo {first_name} {last_name},</p>
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


def create_admin_notification_email(
    first_name: str, 
    last_name: str, 
    email: str, 
    course_label: str, 
    timestamp: str,
    user_email_html: str
) -> str:
    """
    Erstellt den HTML-Inhalt für die Admin-Benachrichtigung.
    
    Args:
        first_name: Vorname des Teilnehmers
        last_name: Nachname des Teilnehmers
        email: E-Mail-Adresse des Teilnehmers
        course_label: Name des gewählten Kurses
        timestamp: Zeitstempel der Anmeldung
        user_email_html: HTML-Inhalt der Benutzer-E-Mail
        
    Returns:
        str: HTML-Inhalt für die Admin-Benachrichtigung
    """
    return f"""
    <p><strong>Neue Anmeldung</strong></p>
    <ul>
    <li><strong>Name:</strong> {first_name} {last_name}</li>
    <li><strong>E-Mail:</strong> {email}</li>
    <li><strong>Kurs:</strong> {course_label}</li>
    <li><strong>Datum/Zeit:</strong> {timestamp}</li>
    </ul>
    <hr>
    {user_email_html}
    """


def send_registration_emails(
    first_name: str, 
    last_name: str, 
    email: str, 
    course_label: str,
    tz: Optional[object] = None
) -> None:
    """
    Versendet Bestätigungs-E-Mail an den Teilnehmer und Benachrichtigung an Admin.
    
    Args:
        first_name: Vorname des Teilnehmers
        last_name: Nachname des Teilnehmers
        email: E-Mail-Adresse des Teilnehmers
        course_label: Name des gewählten Kurses
        tz: Zeitzone für Zeitstempel (optional)
    """
    subject = "Bestätigung deiner Anmeldung – IT-Kurs Dietikon"
    
    # Benutzer-E-Mail erstellen
    user_html = create_registration_confirmation_email(first_name, last_name)
    
    # Zeitstempel für Admin-E-Mail
    timestamp = (datetime.now(tz) if tz else datetime.now()).strftime("%d.%m.%Y %H:%M")
    
    # Admin-E-Mail erstellen
    admin_html = create_admin_notification_email(
        first_name, last_name, email, course_label, timestamp, user_html
    )
    
    try:
        # E-Mails versenden
        send_email_api(email, subject, user_html)
        send_email_api("astrid@dieti-it.ch", f"[Kopie] {subject}", admin_html)
        logger.info(f"Registration emails sent for {email}")
    except Exception as e:
        logger.warning(f"Bestätigungs-Mail fehlgeschlagen: {e}")
        raise
