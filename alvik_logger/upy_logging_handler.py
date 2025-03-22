import os
import logging

class RotatingFileHandler(logging.Handler):
    """Einfacher Rotating File Handler für MicroPython mit Backup-Count & Encoding."""

    def __init__(self, filename="log.txt", maxBytes=5000, backupCount=3, encoding="utf-8"):
        super().__init__()
        self.filename = filename
        self.max_bytes = maxBytes
        self.backup_count = backupCount
        self.encoding = encoding

    def handle(self, record):
        """Verarbeitet einen Log-Eintrag, indem er `emit()` aufruft."""
        self.emit(record)

    def emit(self, record):
        """Schreibt Logs in die Datei und rotiert sie, wenn sie zu groß wird."""
        try:
            log_entry = self.format(record) + "\n"

            # Prüfe, ob die Datei existiert und zu groß ist
            file_exists = self.file_exists(self.filename)
            file_size = self.get_file_size(self.filename) if file_exists else 0

            if file_size > self.max_bytes:
                self.rotate_files()

            # Log in Datei schreiben
            with open(self.filename, "a", encoding=self.encoding) as log_file:
                log_file.write(log_entry)
        except Exception as e:
            print(f"[ERROR] RotatingFileHandler konnte nicht schreiben: {e}")

    def rotate_files(self):
        """Rotiert Logdateien basierend auf `backup_count`."""
        try:
            # Lösche die älteste Datei, wenn `backup_count` erreicht wurde
            oldest_file = f"{self.filename}.{self.backup_count}"
            if self.file_exists(oldest_file):
                os.remove(oldest_file)

            # Verschiebe alte Logdateien
            for i in range(self.backup_count - 1, 0, -1):
                old_file = f"{self.filename}.{i}"
                new_file = f"{self.filename}.{i+1}"
                if self.file_exists(old_file):
                    os.rename(old_file, new_file)

            # Hauptlogdatei umbenennen
            if self.file_exists(self.filename):
                os.rename(self.filename, f"{self.filename}.1")
        except Exception as e:
            print(f"[ERROR] Konnte Logrotation nicht durchführen: {e}")

    def file_exists(self, filename):
        """Prüft, ob eine Datei existiert (ersetzt `os.path.exists()`)."""
        try:
            os.stat(filename)
            return True
        except OSError:
            return False

    def get_file_size(self, filename):
        """Gibt die Dateigröße zurück (MicroPython-Alternative zu `os.path.getsize()`)."""
        try:
            return os.stat(filename)[6]  # Datei-Größe ist das 7. Element in `os.stat()`
        except OSError:
            return 0


if __name__ == "__main__":
    # Logger einrichten
    logger = logging.getLogger("esp32")
    logger.setLevel(logging.DEBUG)

    # Rotating File Handler mit Backup
    file_handler = RotatingFileHandler("../log.txt", maxBytes=5000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Beispiel-Nutzung
    logger.info("ESP32 gestartet")
    logger.error("Verbindung fehlgeschlagen")
    logger.warning("Temperatur hoch")
