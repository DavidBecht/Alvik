import asyncio
import os
from socket import socket

from alvik_http_server.alvik_async_python_runner import AlvikAsyncPythonRunner
from alvik_http_server.alvik_http_server import AlvikHTTPServer
from alvik_logger.logger import logger

try:
    import ure  # Im ESP32 heißt das Regexmodul ure
except ImportError:
    import re as ure
try:
    from typing import List, Tuple
except ImportError:
    List = None  # Platzhalter, da MicroPython kein `typing` hat
    Tuple = None

def endpoint_get_files(_: str, __: socket) -> Tuple[int, str]:
    files = os.listdir(".")  # Liste aller Dateien im aktuellen Verzeichnis
    file_list = "\n".join(files)  # Dateien als Textliste zurückgeben
    logger.debug(f"Current files on server: {files}")
    return 200, file_list

def endpoint_upload_files(request: str, __: socket):
        _, header, file_content = request.split("\r\n\r\n", 2)

        # Den Dateinamen aus `Content-Disposition` extrahieren
        match = ure.search(r'filename="([^"]+)"', header)
        filename = "unknown_file"  # Falls kein Dateiname gefunden wurde
        if match:
            filename = match.group(1)  # Dateiname aus dem Header extrahieren

        # Falls die Datei am Ende noch einen Trennstring hat (Multipart), diesen entfernen
        file_content = file_content.split("\r\n------", 1)[0]

        # Datei speichern
        with open(filename, "wb") as file:
            file.write(file_content.encode())

        logger.info(f"Datei '{filename}' erfolgreich gespeichert")
        return 200, f"Datei '{filename}' erfolgreich gespeichert."

class LiveStream:
    """Ersetzt `print()`, um Ausgabe live an den Client zu senden."""
    def __init__(self, callback, client):
        self.callback = callback  # Funktion zum Senden der Daten
        self.client = client

    def write(self, text):
        """Sendet jeden `print()`-Aufruf sofort weiter."""
        self.callback(text, self.client)  # Weiterleitung an den Client

    def flush(self):
        """Wird benötigt, damit `print()` korrekt funktioniert."""
        pass

def send_to_client(data, client):
    output = data.strip().replace("\n", "<br>")  # HTML-taugliche Zeilenumbrüche
    client.send(f"data: {output}\n\n".encode("utf-8"))

runner = AlvikAsyncPythonRunner()
def _run_python_file(filename: str, client: socket):
    """Startet eine Python-Datei und sendet deren Output in Echtzeit zurück."""
    # with open(filename, "r") as f:
    #     code = f.read()
    # stream = LiveStream(send_to_client, client)
    # namespace = {"print": lambda *args: stream.write(" ".join(map(str, args)) + "\n")}
    # try:
    #     exec(code, namespace)  # Code mit modifizierter `print()`-Funktion ausführen
    # except Exception as e:
    #     error_trace = get_error_message(e)
    #     stream.write(f"Execution of {filename} failed with {e}.\n{error_trace}")  # Fehler auch sofort senden
    #     logger.error(f"Execution of {filename} failed with {e}.\n{error_trace}")
    # logger.info(f"Execution of {filename} completed.")
    # return 200, "OK"
    asyncio.run(runner.start(filename, client))
    return 200, "OK"

def endpoint_run_py_file(request: str, client: socket) -> Tuple[int, str]:
    filename = request.split("GET /run?file=")[1].split(" ")[0]
    # filename = os.path.basename(filename)  # Sicherheit: Keine Pfade zulassen
    logger.info(f"Running file {filename}")
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/event-stream\r\n"
        "Cache-Control: no-cache\r\n"
        "Connection: keep-alive\r\n\r\n"
    )
    client.send(response.encode("utf-8"))
    _run_python_file(filename, client)
    return 200, "OK"

if __name__ == "__main__":
    controller = AlvikHTTPServer("bootloader_index.html")
    controller.add_endpoint("GET /files", endpoint_get_files)
    controller.add_endpoint("POST /upload", endpoint_upload_files)
    controller.add_endpoint("GET /run?file=*.py", endpoint_run_py_file) # GET /run?file=
    controller.connect_to_wifi("david_htl_test", "12345678")
    controller.start_web_server()