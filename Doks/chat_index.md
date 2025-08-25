# IT-Kurs Projektindex

## Webapp
Chat-Link: [IT-Kurs | Webapp-Entwicklung](https://chat.openai.com/...)
Dokument: `webapp.md`

## Content
Chat-Link: [IT-Kurs | Website-Content](https://chat.openai.com/...)
Dokument: `content.md`

## Kursinhalte
Chat-Link: [IT-Kurs | Kursinhalte](https://chat.openai.com/...)
Dokument: `kursinhalte.md`


## Stand 25.8.2025 Unterlagen-Flow und Struktur 
### web/app/content/unterlagen/
	•	Grundgerüst für Kursarten (z. B. grundkurs/, aufbaukurs/)
	•	Darin Lektionsordner (L01/, L02/, …) → jeweils index.md
## web/app/content/unterlagen/durchfuehrungen/
	•	z. B. grundkurs-2025-10/
	•	jede Durchführung eines Kurses bekommt ihren eigenen Ordner
	•	kann eigene Lektionen, Protokolle, Ergebnisse enthalten
## web/app/static/docs/
	•	hier liegen die PDFs/Handouts mit sauberem Namensschema:
G-L01-handout.pdf, oder grundkurs-2025/G-L01-handout.pdf
## Trennung:
	•	Grundgerüst = Basislektionen/Themen
	•	Durchführungen = echte Kurse mit TN, evtl. abweichendem Verlauf


## Routing & Bereichstrennung (Stand 2025-08-26)

### Kurs-Info-Bereich (für Interessierte / Öffentlichkeit)
- **/kursliste** → Endpoint `kursliste` → Template `kursliste.html`  
  → Liste aller Kurse mit Status, Sichtbarkeit, Anmeldebutton.  
- **/kurs/<slug>** → Endpoint `kursbeschreibung` → Template `kursbeschreibung.html`  
  → Detailansicht eines Kurses mit Themen, Beschreibung, Ort, Status, Anmeldung.

### Unterlagen-Bereich (für Teilnehmende)
- **/unterlagen** → Endpoint `unterlagen` → Template `unterlagen.html`  
  → Liste nur der Kurse, die Unterlagen besitzen. Keine Anmeldung, kein Status.  
- **/unterlagen/<slug>** → Endpoint `unterlagen_kurs` → Template `unterlagen_kurs.html`  
  → Übersicht aller Lektionen + Dokumente (Markdown, PDFs) pro Kurs.  
- **/unterlagen/<slug>/<lesson_id>** → Endpoint `unterlagen_lektion` → Template `unterlagen_lektion.html`  
  → Ansicht einer Lektion mit gerendertem Markdown, Anhängen.

### Wichtig
- **Kurs-Infos ≠ Unterlagen.**  
  → Kurs-Infos = Marketing/Info für Interessierte.  
  → Unterlagen = Arbeitsmaterial für Teilnehmer:innen.  
- Gemeinsame Basis: beide ziehen die Kursdaten (`courses.json`) – aber Darstellung + Inhalte unterscheiden sich.