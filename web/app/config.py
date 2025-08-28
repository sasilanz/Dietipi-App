"""
Configuration module for the IT-Kurs application.

This module centralizes all configuration management including
environment variables, database setup, and application settings.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Zurich")
except Exception:
    TZ = None

logger = logging.getLogger(__name__)


class Config:
    """Main configuration class for the application."""
    
    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    
    # Admin configuration
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Email configuration
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "info@dieti-it.ch")
    
    # Payment configuration
    PAYEE_DISPLAY_NAME = os.getenv("PAYEE_DISPLAY_NAME", "IT-Kurs Dietikon")
    PAYEE_LEGAL_NAME = os.getenv("PAYEE_LEGAL_NAME", "")
    PAYEE_IBAN = os.getenv("PAYEE_IBAN", "")
    PAYEE_BIC = os.getenv("PAYEE_BIC", "")
    PAYEE_BANK = os.getenv("PAYEE_BANK", "")
    PAYMENT_PURPOSE_PREFIX = os.getenv("PAYMENT_PURPOSE_PREFIX", "Kursgebühr")
    PAYMENT_EMAIL = os.getenv("PAYMENT_EMAIL", "")
    
    # Application settings
    TIMEZONE = TZ


def create_database_engine():
    """
    Erstellt und konfiguriert die SQLAlchemy Database Engine.
    
    Returns:
        Engine | None: Database engine oder None falls nicht konfiguriert
    """
    db_url = Config.DATABASE_URL
    if not db_url:
        logger.warning("DATABASE_URL nicht gesetzt - Datenbank nicht verfügbar")
        return None
        
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        logger.info("Database engine erfolgreich erstellt")
        return engine
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Database Engine: {e}")
        return None


def create_session_factory(engine):
    """
    Erstellt eine SQLAlchemy Session Factory.
    
    Args:
        engine: SQLAlchemy Engine
        
    Returns:
        sessionmaker | None: Session factory oder None falls Engine fehlt
    """
    if not engine:
        return None
        
    try:
        session_factory = sessionmaker(bind=engine)
        logger.info("Session factory erfolgreich erstellt")
        return session_factory
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Session Factory: {e}")
        return None


def get_payment_config():
    """
    Gibt die Payment-Konfiguration als Dictionary zurück.
    
    Returns:
        dict: Payment configuration für Templates
    """
    return {
        "display_name": Config.PAYEE_DISPLAY_NAME,
        "legal_name": Config.PAYEE_LEGAL_NAME,
        "iban": Config.PAYEE_IBAN,
        "bic": Config.PAYEE_BIC,
        "bank": Config.PAYEE_BANK,
        "purpose_prefix": Config.PAYMENT_PURPOSE_PREFIX,
        "contact_email": Config.PAYMENT_EMAIL,
    }


def configure_logging():
    """Konfiguriert das Logging für die Anwendung."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
