# IT-Kurs | Webapp-Entwicklung

## Status & Ziele
- Ziel: Fertige Kursverwaltungs-Webapp mit Anmeldung, Teilnehmerverwaltung, Kurskalender
- Stack: Django + Docker
- Hosting Platform: eigener Raspberry Pi 4 mit externere SSD im Dauerbetrieb
- DB in separatem Container
- Soll auf domain: dieti-it.ch laufen welche auf hostpoint.ch registriert ist

## Nächste Schritte
-  Setup auf der SSD für den raspberry, dh vorbereitung der SSD 
-  Entwicklung des contets ist aktuell lokal auf dem macmini, wegen performance und bequemlichkeit mit vscode und so
-  sobald SSD bereit,und alle funktionen funktionieren, die bestehenden Dateien umziehen
- [ ] Mobile-Optimierung, sobald der content fertig definiert ist.
-  QR Code einbinden in den Flyer
- [ ] E-Mail-Benachrichtigungen testen
- [ ] Dropdown für Kurse in Teilnehmer-Ansicht

## Entscheidungen
- 2025-08-13 | Teilnehmerverwaltung in Django umgesetzt, mobile Ansicht noch offen.
- 2025-08-15 | Start mit nur einem Kurs, Dropdown aber schon vorbereitet.

## Offene Fragen
- Authentifizierung: Nur Admin oder auch Teilnehmer-Login?
- Sollen Dateien (PDFs) direkt in der Webapp hochgeladen werden können?

## Links & Referenzen
- Repo: `https://...`
- Dokumentation Django: https://docs.djangoproject.com/en/5.0/