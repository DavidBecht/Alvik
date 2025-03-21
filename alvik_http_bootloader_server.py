import os
from socket import socket
from alvik_http_server.alvik_http_server import AlvikHTTPServer
from alvik_logger.logger import logger, get_error_message
from alvik_utils.upy_streamwriter import UPYStreamWriter

try:
    import ure  # Im ESP32 heißt das Regexmodul ure
except ImportError:
    import re as ure
try:
    from typing import List, Tuple
except ImportError:
    List = None  # Platzhalter, da MicroPython kein `typing` hat
    Tuple = None

async def endpoint_get_files(_: str, __: socket) -> Tuple[int, str]:
    files = os.listdir(".")  # Liste aller Dateien im aktuellen Verzeichnis
    file_list = "\n".join(files)  # Dateien als Textliste zurückgeben
    logger.debug(f"Current files on server: {files}")
    return 200, file_list

async def endpoint_upload_files(request: str, __: socket):
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
    def __init__(self, writer: UPYStreamWriter):
        self.writer = writer

    async def awrite(self, text):
        """Sendet jeden `print()`-Aufruf sofort weiter."""
        logger.info(text)
        output = text.strip().replace("\n", "<br>")  # HTML-taugliche Zeilenumbrüche
        await self.writer.awrite(f"data: {output}\n\n".encode("utf-8"))

    def write(self, text):
        """Sendet jeden `print()`-Aufruf sofort weiter."""
        logger.info(text)
        output = text.strip().replace("\n", "<br>")  # HTML-taugliche Zeilenumbrüche
        self.writer.write(f"data: {output}\n\n".encode("utf-8"))

    def print(self, *args):
        self.write(" ".join(map(str, args)))

    def flush(self):
        """Wird benötigt, damit `print()` korrekt funktioniert."""
        pass



async def _run_python_file(filename: str, writer: UPYStreamWriter):
    """Startet eine Python-Datei und sendet deren Output in Echtzeit zurück."""
    with open(filename, "r") as f:
        code = f.read()
    stream = LiveStream(writer)

    namespace = {"print": stream.print}
    await stream.awrite(f"Running file {filename}")
    try:
        exec(code, namespace)  # Code mit modifizierter `print()`-Funktion ausführen
    except Exception as e:
        error_trace = get_error_message(e)
        await stream.awrite(f"ERROR:Execution of {filename} failed with {e}.\n{error_trace}")  # Fehler auch sofort senden
    logger.info(f"Execution of {filename} completed.")
    return 200, "OK"
    # from alvik_logger.logger import logger
    # logger.info("returning 3")
    # await asyncio.sleep(1)
    # await runner.start(filename, client)
    # logger.info("returning 1")
    # return 200, "OK"

async def endpoint_run_py_file(request: str, writer: UPYStreamWriter) -> Tuple[int, str]:
    filename = request.split("GET /run?file=")[1].split(" ")[0]
    # filename = os.path.basename(filename)  # Sicherheit: Keine Pfade zulassen

    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/event-stream\r\n"
        "Cache-Control: no-cache\r\n"
        "Connection: keep-alive\r\n\r\n"
    )
    await writer.awrite(response.encode("utf-8"))
    return await _run_python_file(filename, writer)

if __name__ == "__main__":
    controller = AlvikHTTPServer("bootloader_index.html")
    controller.add_endpoint("GET /files", endpoint_get_files)
    controller.add_endpoint("POST /upload", endpoint_upload_files)
    controller.add_endpoint("GET /run?file=*.py", endpoint_run_py_file) # GET /run?file=
    # controller.start_hotspot("david_alvik", "12345678")
    controller.connect_to_wifi("FRITZ!Box 6660 Cable ED", "89755110268842584875")
    controller.start_web_server()