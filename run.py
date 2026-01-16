from app import create_app
import logging

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        app = create_app()
        logger.info("=" * 50)
        logger.info("Dinner Bingo Server gestartet!")
        logger.info("Admin-Login: admin / admin123")
        logger.info("=" * 50)
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Fehler beim Starten der Anwendung: {e}")
        raise

