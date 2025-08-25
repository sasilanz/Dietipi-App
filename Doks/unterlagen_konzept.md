# Unterlagen – vereinbartes Konzept (gültig ab 2025‑08‑25)

## 1) Ebenen & Slugs
- **Kursbeschreibung (für Interessierte)**
  - Slug: **Oberkurs**, z. B. `grundkurs-2025`
  - Quelle: `content/meta/<beschreibung_slug>.json`
  - Route: `/kurs/<beschreibung_slug>`
- **Unterlagen (für Teilnehmende)**
  - Slug: **Durchführung**, z. B. `grundkurs-2025-di` (oder `…-do`)
  - Route: `/unterlagen/<id>` → Lektionsliste  
           `/unterlagen/<id>/<lesson_id>` → Lektionsseite

`courses.json` pro **Durchführung** enthält:
- `id` (z. B. `grundkurs-2025-di`) – wird für **Unterlagen** & Anmeldung verwendet  
- `beschreibung_slug` (z. B. `grundkurs-2025`) – zeigt auf die **Kursbeschreibung**  
- optional `unterlagen_slug` (falls jemals vom `id` abweichend; sonst = `id`)  

> **Wichtig:** In der Unterlagen‑Welt arbeiten wir **konsequent mit der Durchführung** (`id`). Keine Typ‑ oder Oberkurs‑Ableitungen.

## 2) Dateistruktur Unterlagen
```
web/app/content/unterlagen/
├─ kurse/                         ← (optional) Grundgerüst pro Kurs-Typ (Vorlagen)
│  └─ grundkurs/
│     ├─ assets/                  ← kursweite Vorlagen-Assets (optional)
│     ├─ L01/index.md             ← Muster (wird kopiert, nicht live gerendert)
│     └─ L02/index.md
└─ durchfuehrungen/               ← **ein Ordner je laufende/abgeschlossene Durchführung**
   └─ grundkurs-2025-di/
      ├─ assets/                  ← **laufzeitweite Assets** (QR, Fotos, Exporte, …)
      ├─ L01/
      │  ├─ index.md              ← **live gerendert**
      │  └─ foto.png              ← **lektionseigenes Asset**
      └─ L02/
         └─ index.md
```

- **Gerendert** werden ausschließlich die Markdown‑Dateien unter  
  `content/unterlagen/durchfuehrungen/<id>/Lxx/index.md`.
- **Front‑Matter** in jeder Lektion (wird gelesen):  
  `id`, `title`, `order` (für Sortierung).
- **Relative Links in Markdown**:  
  - `./bild.png` → Datei in **Lektionsordner**  
  - `../assets/foo.png` → Datei in **Durchführungs‑assets**  
- **PDFs & Downloaddateien** (fix):  
  liegen in `web/app/static/docs/<id>/…`  
  z. B. `/static/docs/grundkurs-2025-di/G-L01-handout.pdf`  
  (flache Struktur mit sprechenden Dateinamen)

## 3) Darstellung & Navigation
- `/unterlagen` → simple Liste **nur sichtbarer Durchführungen** (`visible=true`)  
  (keine Status‑Badges, keine Anmeldung)
- `/unterlagen/<id>` → Liste der Lektionen (nach `order`, sonst `Lxx`)  
- `/unterlagen/<id>/<lesson_id>` → rendert `index.md`, zeigt optional „Dokumente“-Liste (PDF‑Links)

## 4) Auslieferung von Assets (Bilder etc.)
- Lektionen und Durchführungs‑Assets werden **nicht** aus `static` bedient.  
- Sie werden **sicher** via Media‑Route ausgeliefert, die **auf den Durchführungsordner begrenzt** ist.  
- Relative Links aus Markdown (`./…`, `../assets/…`) werden serverseitig auf diese Media‑Route umgeschrieben.  
- PDFs bleiben über `/static/docs/<id>/…` erreichbar (keine Umschreibung nötig).

## 5) Git‑Vorgehen
- Diesen Stand als **Design‑Entscheidung** dokumentieren (z. B. in `Doks/entscheidungsprotokoll.md` oder `Doks/chat_index.md`).  
  Titelvorschlag: „Unterlagen‑Konzept (gültig ab 2025‑08‑25)“.
- Tag auf dem bestehenden Branch setzen, um „Kurse fertig, Unterlagen offen“ festzuhalten:  
  `kurse-ready` (bereits vorgeschlagen).
- Neuer Feature‑Branch nur für die Unterlagen‑Implementierung: `unterlagen-impl`.
