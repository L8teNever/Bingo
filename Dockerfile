FROM python:3.11-slim

WORKDIR /app

# Kopiere alle Dateien in das Continer-Verzeichnis
COPY . .

# Installiere die Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Port für Flask
EXPOSE 5000

# Starte die Anwendung über run.py (initialisiert die DB)
CMD ["python", "run.py"]
