FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Dependencies installieren (inkl. curl für healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Requirements kopieren und installieren (für besseres Layer-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Instance-Verzeichnis erstellen (für Datenbank)
RUN mkdir -p /app/instance && chmod 755 /app/instance

# Non-root User erstellen und verwenden (Sicherheit)
RUN useradd -m -u 1000 bingo && \
    chown -R bingo:bingo /app
USER bingo

# Port exposieren
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Anwendung starten
CMD ["python", "run.py"]
