Template: it-kurs-simple.tex  
Engine: xelatex (für System-Schriften)
Schrift: Echte Arial 12pt vom Mac
Farben: Perfekt abgestimmt auf deine Web-App

Dein finaler Befehl:

# Mit echter Arial (empfohlen):
pandoc datei.md -o datei.pdf \
  --template=it-kurs-simple.tex \
  --pdf-engine=xelatex \
  -V title="Dein Titel"

# Fallback mit pdflatex (falls XeLaTeX mal Probleme macht):
pandoc datei.md -o datei.pdf \
  --template=it-kurs-simple.tex \
  --pdf-engine=pdflatex


it-kurs-simple.tex (Latex-Template) ist auch im home folder (auf dem macmini)
dh pandoc kann überall verwendet werden um md in pdf umzuwandeln mit:
pandoc datei.md -o datei.pdf --template=~/it-kurs-simple.tex --pdf-engine=xelatex

