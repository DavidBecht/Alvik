import _thread
import asyncio
import os
from socket import socket
from alvik_http_server.alvik_http_server import AlvikHTTPServer
from alvik_logger.logger import logger
from alvik_utils.upy_code_runner import UPYCodeRunner
from alvik_utils.upy_streamwriter import UPYStreamWriter
from collections import deque

from alvik_utils.utils import get_error_message

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
    exit_msg = "__EXIT__LIVESTREAM__"
    """Ersetzt `print()`, um Ausgabe live an den Client zu senden."""
    def __init__(self, writer: UPYStreamWriter):
        self.writer: UPYStreamWriter = writer
        self.msg_queue = deque()
        self.stop = False

    def __del__(self):
        self.stop = True

    async def awrite(self, text):
        """Sendet jeden `print()`-Aufruf sofort weiter."""
        logger.info(text)
        output = text.strip().replace("\n", "<br>")  # HTML-taugliche Zeilenumbrüche
        await self.writer.awrite(f"data: {output}\n\n".encode("utf-8"))

    def write(self, text):
        """Sendet jeden `print()`-Aufruf sofort weiter."""
        self.msg_queue.append(text)
        # logger.info(text)
        # output = text.strip().replace("\n", "<br>")  # HTML-taugliche Zeilenumbrüche
        # asyncio.run(self.writer.awrite(f"data: {output}\n\n".encode("utf-8")))

    async def stream_writer_loop(self):
        exit = False
        while not exit:
            while self.msg_queue:
                try:
                    text = self.msg_queue.popleft()
                    print(text)
                    if text == self.exit_msg:
                        exit = True
                        break
                    await self.awrite(text)
                except ConnectionResetError:
                    logger.warning("Client hat die Verbindung getrennt.")
                    exit = True
                    break
            await asyncio.sleep(0.1)
        logger.info(f"Execution completed.")
        await self.writer.send_response(200)
        await self.writer.aclose()

    def print(self, *args):
        self.write(" ".join(map(str, args)))

    def flush(self):
        """Wird benötigt, damit `print()` korrekt funktioniert."""
        pass

    def close(self):
        self.msg_queue.append(self.exit_msg)

def run_user_code(code, namespace, stream: LiveStream, filename):
    try:
        exec(code, namespace)  # Code mit modifizierter `print()`-Funktion ausführen
    except Exception as e:
        error_trace = get_error_message(e)
        stream.write(f"ERROR:Execution of {filename} failed with {e}.\n{error_trace}")  # Fehler auch sofort senden
    finally:
        stream.close()

async def _run_python_file(filename: str, writer: UPYStreamWriter):
    """Startet eine Python-Datei und sendet deren Output in Echtzeit zurück."""
    await UPYCodeRunner(filename, writer).run_file()

async def endpoint_run_py_file(request: str, writer: UPYStreamWriter) -> Tuple[int, str]:
    filename = request.split("GET /run?file=")[1].split(" ")[0]
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/event-stream\r\n"
        "Cache-Control: no-cache\r\n"
        "Connection: keep-alive\r\n\r\n"
    )
    await writer.awrite(response.encode("utf-8"))
    await _run_python_file(filename, writer)
    return AlvikHTTPServer.SPECIAL_RESPONSE_CODES.STREAM

if __name__ == "__main__":
    controller = AlvikHTTPServer("bootloader_index.html")
    controller.add_endpoint("GET /files", endpoint_get_files)
    controller.add_endpoint("POST /upload", endpoint_upload_files)
    controller.add_endpoint("GET /run?file=*.py", endpoint_run_py_file) # GET /run?file=
    # controller.start_hotspot("david_alvik", "12345678")
    controller.connect_to_wifi("FRITZ!Box 6660 Cable ED", "89755110268842584875")
    controller.start_web_server()