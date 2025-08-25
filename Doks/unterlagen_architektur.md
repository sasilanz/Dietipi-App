•	Routen:
	•	/unterlagen → unterlagen.html (Kursliste ohne Status/Anmeldung)
	•	/unterlagen/<slug> → unterlagen_kurs.html (Lektionsliste + Dokument‑Aktionen)
	•	/unterlagen/<slug>/<lesson> → unterlagen_lektion.html (Markdown‑Ansicht)
	•	Struktur:
	•	web/app/content/unterlagen/<kursart>/Lxx/index.md (Grundgerüst)
	•	web/app/content/unterlagen/durchfuehrungen/<kurs-datum>/... (laufende Kurse)
	•	web/app/static/docs/<kurs-slug>/… (PDFs; Namensschema)
	•	Namensschema: z. B. G-L01-handout.pdf oder <kurs-slug>/G-L01-handout.pdf