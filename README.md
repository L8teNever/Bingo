# Wort Bingo 🎲

Eine interaktive Flask-Webanwendung für ein unterhaltsames Wort-Ratespiel.

## 📋 Beschreibung

Wort Bingo ist ein Spiel, bei dem Teilnehmer täglich ein Wort auswählen, von dem sie glauben, dass es am Tisch erwähnt wird. Wenn das Wort fällt, erhält der Spieler Punkte!

### Features

- 🔐 **Benutzer-Authentifizierung** mit Admin- und Spieler-Rollen
- 📝 **Tägliche Worteingabe** mit konfigurierbaren Zeitfenstern
- 🏆 **Punktesystem** und Bestenliste
- ⏰ **Zeitbasierte Phasen**: Eingabe → Abstimmung
- 🚫 **Cooldown-System** für bereits verwendete Wörter
- ✏️ **Wortänderungen** mit konfigurierbarem Limit
- 👨‍💼 **Admin-Panel** für Einstellungen und Punkteverwaltung
- 🐳 **Docker-Support** mit Datenpersistenz
- 📱 **Responsive Design** mit modernem UI
- ✨ **Smarte UI**: Einreich-Button verschwindet nach Eingabe, zeigt andere Teilnehmer automatisch
- 🔒 **Sichere Benutzerverwaltung**: Benutzer nur über Skript/CLI erstellbar

## 🚀 Schnellstart

### Mit Docker (Empfohlen)

```bash
# Repository klonen
git clone <repository-url>
cd Bingo

# Container starten
docker-compose up -d

# Anwendung öffnen
# http://localhost:5000
```

### Ohne Docker

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung starten
python run.py

# Anwendung öffnen
# http://localhost:5000
```

## 🔧 Konfiguration

### Umgebungsvariablen

Erstelle eine `.env` Datei (siehe `.env.example`):

```bash
SECRET_KEY=dein-geheimer-schlüssel-hier
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/bingo.db  # Optional
```

### Einstellungen im Admin-Panel

Nach dem Login als Admin können folgende Einstellungen angepasst werden:

- **Startzeit** (`notify_time`): Wann die Worteingabe startet (z.B. `12:00`)
- **Abstimmungszeit** (`dinner_time`): Wann die Abstimmungsphase beginnt (z.B. `18:00`)
- **Cooldown-Tage** (`cooldown_days`): Wie lange ein Wort gesperrt bleibt (z.B. `14`)
- **Max. Änderungen** (`max_changes`): Wie oft ein Wort pro Tag geändert werden kann (z.B. `3`)

## 👤 Benutzerverwaltung

### Methode 1: Über docker-compose (Empfohlen)

Benutzer werden automatisch beim Container-Start erstellt. Bearbeite die `docker-compose.yml`:

```yaml
environment:
  - USERS=admin:admin123:admin,max:geheim123:player,anna:test456:player
```

**Format:** `username:password:role,username:password:role,...`

**Rollen:** `player` oder `admin`

**Vorteile:**
- ✅ Automatisch beim Start
- ✅ Einfach neue Benutzer hinzufügen
- ✅ Passwörter werden bei jedem Start aktualisiert
- ✅ Versionskontrolle möglich

### Methode 2: Über Skript (Alternativ)

Für manuelle Benutzerverwaltung:

```bash
# Lokal
python create_user.py max geheim123 player
python create_user.py --list

# Im Docker-Container
docker exec -it dinner_bingo python create_user.py max geheim123 player
```

```
Benutzername: admin
Passwort: admin123
```

**⚠️ WICHTIG:** Ändere das Admin-Passwort nach dem ersten Login!

## 🐳 Docker-Details

### Datenpersistenz

Die Datenbank wird in einem Docker Volume gespeichert:

```bash
# Volume anzeigen
docker volume ls | grep bingo

# Volume-Daten anzeigen
docker volume inspect bingo_bingo-data
```

### Container-Verwaltung

```bash
# Container starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Container stoppen
docker-compose down

# Container neu bauen
docker-compose up -d --build

# Datenbank zurücksetzen (VORSICHT: Löscht alle Daten!)
docker-compose down -v
docker-compose up -d
```

## 📁 Projektstruktur

```
Bingo/
├── app.py              # Hauptanwendung mit Application Factory
├── models.py           # Datenbankmodelle
├── run.py              # Einstiegspunkt
├── requirements.txt    # Python-Abhängigkeiten
├── Dockerfile          # Docker-Image-Definition
├── docker-compose.yml  # Docker-Compose-Konfiguration
├── templates/          # HTML-Templates
│   ├── layout.html
│   ├── login.html
│   ├── dashboard.html
│   ├── leaderboard.html
│   ├── settings.html
│   └── admin.html
└── static/             # Statische Dateien (CSS, JS, Icons)
    ├── style.css
    ├── manifest.json
    └── sw.js
```

## 🎮 Spielablauf

1. **Vor der Startzeit**: Warten-Phase
2. **Startzeit bis Abstimmungszeit**: Spieler können Wörter einreichen/ändern
3. **Ab Abstimmungszeit**: Abstimmungsphase - Punkte vergeben für erwähnte Wörter

## 🔒 Sicherheit

- Passwörter werden mit Werkzeug's `generate_password_hash` gehasht
- CSRF-Schutz durch Flask-Login
- Non-Root Docker-Container für erhöhte Sicherheit
- Umgebungsvariablen für sensible Daten

## 🛠️ Entwicklung

### Lokale Entwicklung

```bash
# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Im Debug-Modus starten
python run.py
```

### Logging

Die Anwendung verwendet Python's `logging`-Modul. Logs werden auf der Konsole ausgegeben:

```bash
# Logs in Docker anzeigen
docker-compose logs -f bingo
```

## 📝 Lizenz

Dieses Projekt ist für den privaten Gebrauch bestimmt.

## 🤝 Beitragen

Da dies ein privates Familienprojekt ist, sind externe Beiträge nicht vorgesehen.

## 📞 Support

Bei Problemen oder Fragen wende dich an den Administrator.

---

**Viel Spaß beim Dinner Bingo! 🎉**
