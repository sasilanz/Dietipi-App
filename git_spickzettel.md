# Git Spickzettel

## Status & Änderungen ansehen
```bash
git status                 # Was ist geändert / staged?
git diff                   # Änderungen im Working Tree
git diff --staged          # Änderungen, die committed würden
```

## Dateien vormerken / zurücknehmen
```bash
git add <file>             # Datei zum Commit vormerken (stagen)
git add -A                 # Alles stagen
git restore --staged <f>   # Aus Staging wieder entfernen
git restore <file>         # Working-Tree-Änderung verwerfen (Vorsicht!)
```

## Committen
```bash
git commit -m "msg"        # Commit mit Nachricht
git commit --amend         # Letzten Commit (inkl. Message) ersetzen
```

## Push & Pull
```bash
git pull                   # Änderungen holen & mergen
git pull --rebase          # Preferred: ohne Merge-Commit
git push                   # Aktuellen Branch pushen
git push --set-upstream origin <branch>   # Erstes Pushen eines neuen Branches
```

## Branches
```bash
git branch                 # Lokale Branches anzeigen
git switch <branch>        # In Branch wechseln
git switch -c <neu>        # Neuen Branch erstellen + wechseln
git branch -d <branch>     # Lokalen Branch löschen (merged)
git push origin --delete <branch>  # Remote-Branch löschen
```

## Schnell „Undo“ (häufige Fälle)
```bash
git checkout -- <file>     # (alt) Änderung an Datei verwerfen (wie restore)
git reset --soft HEAD^     # Letzten Commit rückgängig, Änderungen bleiben STAGED
git reset --mixed HEAD^    # Letzten Commit rückgängig, Änderungen bleiben im WT
git reset --hard HEAD^     # Letzten Commit + Änderungen verwerfen (Vorsicht!)
git revert <commit>        # Commit rückgängig machen (neuer Gegen-Commit)
```

## Verlaufsrettung
```bash
git log --oneline --graph --decorate -n 20   # Schöner Kurzlog
git reflog                                   # „Zeitsprung“-Verlauf (HEAD Historie)
git reset --hard HEAD@{1}                    # Zum vorherigen Zustand springen
```

## Stash (Zwischenparken)
```bash
git stash save "kurz notiert"   # Änderungen wegpacken
git stash list                  # Stashes ansehen
git stash pop                   # Letzten Stash anwenden + entfernen
git stash drop                  # Stash löschen
```

## Remotes & SSH
```bash
git remote -v               # Remotes anzeigen
ssh -T git@github.com       # SSH‑Zugang zu GitHub testen
```

## Tags (Versionen markieren)
```bash
git tag -a v0.1 -m "v0.1"   # Annotated Tag
git push --tags             # Tags hochschieben
```

## Dateien ignorieren / aus Repo entfernen
```bash
# .gitignore anpassen (z. B. .env, web/.env)
git rm --cached web/.env    # Aus Repo entfernen, lokal behalten
git commit -m "remove web/.env from repo"
git push
```

## Aufräumen
```bash
git clean -fd               # Ungetrackte Dateien/Ordner löschen (Vorsicht!)
```
