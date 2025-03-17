import asyncio

class AlvikExecPrint:
    """Ersetzt `print()`, um Ausgabe live an den Client zu senden."""
    def __init__(self, client):
        self.client = client
        self.namespace = {
            "print": lambda *args: self.write(" ".join(map(str, args)) + "\n")
        }

    def write(self, text: str) -> None:
        """Sendet jeden `print()`-Aufruf sofort weiter."""
        AlvikExecPrint.send_to_client(text, self.client)  # Weiterleitung an den Client

    @staticmethod
    def send_to_client(data, client):
        output = data.strip().replace("\n", "<br>")  # HTML-taugliche Zeilenumbrüche
        client.send(f"data: {output}\n\n".encode("utf-8"))

    def flush(self) -> None:
        """Wird benötigt, damit `print()` korrekt funktioniert."""
        pass
