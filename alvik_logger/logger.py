import logging
try:
    from logging.handlers import RotatingFileHandler
except ImportError:
    from alvik_logger.esp32_logging_handler import RotatingFileHandler

# Logger erstellen
logger = logging.getLogger("ALVIKLogger")
logger.setLevel(logging.DEBUG)  # Alle Log-Level zulassen

# Format für Logs
log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# StreamHandler für die Konsole
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Nur INFO und höher in die Konsole
console_handler.setFormatter(log_format)

# RotatingFileHandler (Max. 1000 KB pro Datei, 2 Backups)
file_handler = RotatingFileHandler("logfile.log", maxBytes=1000000, backupCount=0, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)  # Alles (DEBUG und höher) in die Datei
file_handler.setFormatter(log_format)

# Handler dem Logger hinzufügen
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def logger_test():
  logger.debug("Das ist eine Debug-Nachricht.")
  logger.info("Das ist eine Info-Nachricht.")
  logger.warning("Das ist eine Warnung.")
  logger.error("Das ist eine Fehler-Meldung.")
  logger.critical("Das ist eine kritische Meldung.")

def get_error_message(exception: Exception) -> str:
    try:
        import traceback
        return traceback.format_exc()
    except ImportError:
        import sys
        import io
        buf = io.StringIO()
        sys.print_exception(exception, buf)
        return buf.getvalue()