import asyncio

class AlvikExecPrint:
    """Ersetzt `print()`, um Ausgabe live an den Client zu senden."""
    def __init__(self, callback, client):
        self.callback = callback  # Funktion zum Senden der Daten
        self.client = client
        self.namespace =  {
            "print": lambda *args: self.write(" ".join(map(str, args)) + "\n"),
            "asyncio": asyncio  # Damit das Skript auch `await asyncio.sleep()` nutzen kann
        }

    def write(self, text):
        """Sendet jeden `print()`-Aufruf sofort weiter."""
        self.callback(text, self.client)  # Weiterleitung an den Client

    def flush(self):
        """Wird benötigt, damit `print()` korrekt funktioniert."""
        pass
