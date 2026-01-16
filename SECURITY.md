# Sicherheitsrichtlinien - Wort Bingo

## Übersicht

Dieses Dokument beschreibt die Sicherheitsmaßnahmen, die im Wort Bingo Projekt implementiert wurden, um sensible Daten zu schützen.

## ✅ Implementierte Sicherheitsmaßnahmen

### 1. Umgebungsvariablen (.env)

**Status: ✅ GESCHÜTZT**

- Die `.env` Datei ist in `.gitignore` eingetragen (Zeile 4)
- Die `.env` Datei ist in `.dockerignore` eingetragen
- Nur `.env.example` mit Beispielwerten wird versioniert
- Alle sensiblen Daten werden über Umgebungsvariablen geladen

**Sensible Variablen:**
- `SECRET_KEY` - Flask Session Secret
- `USERS` - Benutzerdaten im Format `username:password:role`
- `DATABASE_URL` - Datenbankverbindungsstring (optional)

### 2. Passwörter

**Status: ✅ SICHER**

- Alle Passwörter werden mit `werkzeug.security.generate_password_hash()` gehasht
- Passwörter werden NIE im Klartext gespeichert
- Passwort-Hashes werden in der Datenbank gespeichert
- Login verwendet `check_password_hash()` für sichere Verifikation

**Dateien:**
- `app.py`: Zeilen 96, 147, 155, 193, 423
- `models.py`: Zeile 11 (password_hash Spalte)
- `create_user.py`: Zeile 35

### 3. Datenbank

**Status: ✅ GESCHÜTZT**

- Datenbank-Datei `bingo.db` ist in `.gitignore` eingetragen (Zeile 15)
- Instance-Ordner ist in `.gitignore` eingetragen (Zeile 11)
- Datenbank wird NICHT ins Git-Repository committed
- Datenbank wird NICHT ins Docker-Image kopiert (.dockerignore Zeile 31-34)

### 4. Git Repository

**Status: ✅ SAUBER**

Überprüfung durchgeführt:
```bash
git ls-files | grep -E '\.env$|\.env\.|secret|password|token'
# Ergebnis: Nur .env.example gefunden ✅
```

**Geschützte Dateien/Ordner:**
- `.env` - Umgebungsvariablen
- `.venv`, `venv/`, `ENV/` - Python Virtual Environments
- `instance/` - Flask Instance Ordner (enthält Datenbank)
- `*.db`, `*.sqlite*` - Datenbankdateien
- `__pycache__/` - Python Cache

### 5. Docker

**Status: ✅ SICHER**

- `.env` wird NICHT ins Docker-Image kopiert
- Sensible Daten werden zur Laufzeit über Environment Variables injiziert
- `docker-compose.yml` verwendet Platzhalter-Werte mit `${SECRET_KEY:-default}`
- Produktions-Secrets müssen extern konfiguriert werden

## 📋 Checkliste für Deployment

Vor dem Deployment in Produktion:

- [ ] `.env` Datei mit echten Produktionswerten erstellen
- [ ] `SECRET_KEY` mit einem starken, zufälligen Wert setzen
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] Standard-Admin-Passwort ändern
- [ ] `FLASK_ENV=production` setzen
- [ ] Datenbank-Backups einrichten
- [ ] HTTPS/SSL für Produktionsumgebung konfigurieren
- [ ] Firewall-Regeln überprüfen

## 🔒 Best Practices

### Für Entwickler:

1. **NIE** sensible Daten committen
2. **IMMER** `.env.example` aktualisieren (ohne echte Werte)
3. **NIEMALS** Passwörter im Code hardcoden
4. **IMMER** Umgebungsvariablen für Secrets verwenden

### Für Deployment:

1. Verwende starke, zufällige `SECRET_KEY`
2. Ändere alle Standard-Passwörter
3. Verwende HTTPS in Produktion
4. Regelmäßige Backups der Datenbank
5. Monitoring und Logging aktivieren

## 🚨 Was tun bei versehentlichem Commit sensibler Daten?

Falls versehentlich sensible Daten committed wurden:

1. **SOFORT** alle betroffenen Secrets ändern (Passwörter, Tokens, Keys)
2. Git-History bereinigen:
   ```bash
   # Datei aus Git-History entfernen
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch DATEINAME" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force Push (VORSICHT!)
   git push origin --force --all
   ```
3. Alle Teammitglieder informieren
4. Neue Secrets generieren und verteilen

## 📞 Sicherheitsprobleme melden

Bei Sicherheitsproblemen oder Fragen:
- Erstelle ein Issue im Repository (OHNE sensible Daten!)
- Kontaktiere den Repository-Maintainer direkt

## 🔍 Letzte Sicherheitsüberprüfung

- **Datum:** 2026-01-16
- **Status:** ✅ Alle Sicherheitsmaßnahmen implementiert
- **Nächste Überprüfung:** Bei größeren Code-Änderungen

---

**Wichtig:** Dieses Dokument sollte regelmäßig aktualisiert werden, wenn neue Sicherheitsmaßnahmen implementiert werden.
