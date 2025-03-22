import os
from alvik_http_server.alvik_http_server import AlvikHTTPServer
from alvik_logger.logger import logger
from alvik_utils.upy_code_runner import UPYCodeRunner
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

ALVIK_NAME = "ALVIK24-03"
ALVIK_HOTSPOT_PW = "12345678"

class AlvikHTTPBootloader:

    def __init__(self):
        self.code_runner: UPYCodeRunner = None
        self.controller = AlvikHTTPServer("bootloader_index.html")
        self.controller.add_endpoint("GET /files", self._endpoint_get_files)
        self.controller.add_endpoint("POST /upload", self._endpoint_upload_files)
        self.controller.add_endpoint("GET /run?file=*.py", self._endpoint_run_py_file)  # GET /run?file=
        self.controller.add_endpoint("GET /stop", self._endpoint_stop_py_file)
    def start_hotspot(self, ssid: str = ALVIK_NAME, password: str = ALVIK_HOTSPOT_PW):
        self.controller.start_hotspot(ssid, password)

    def connect_to_wifi(self, ssid: str, password: str):
        self.controller.connect_to_wifi(ssid, password)

    def start(self):
        self.controller.start_web_server()

    async def _endpoint_get_files(self, _: str, __: UPYStreamWriter) -> Tuple[int, str]:
        files = os.listdir(".")  # Liste aller Dateien im aktuellen Verzeichnis
        file_list = "\n".join(files)  # Dateien als Textliste zurückgeben
        logger.debug(f"Current files on server: {files}")
        return 200, file_list

    async def _endpoint_upload_files(self, request: str, __: UPYStreamWriter) -> Tuple[int, str]:
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

    async def _run_python_file(self, filename: str, writer: UPYStreamWriter) -> None:
        """Startet eine Python-Datei und sendet deren Output in Echtzeit zurück."""
        if self.code_runner is not None:
            await self.code_runner.stop_and_wait()
        self.code_runner = UPYCodeRunner(filename, writer)
        await self.code_runner.run_file()

    async def _endpoint_run_py_file(self, request: str, writer: UPYStreamWriter) -> Tuple[int, str]:
        filename = request.split("GET /run?file=")[1].split(" ")[0]
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/event-stream\r\n"
            "Cache-Control: no-cache\r\n"
            "Connection: keep-alive\r\n\r\n"
        )
        await writer.awrite(response.encode("utf-8"))
        await self._run_python_file(filename, writer)
        return AlvikHTTPServer.SPECIAL_RESPONSE_CODES.STREAM

    async def _endpoint_stop_py_file(self, request: str, writer: UPYStreamWriter) -> Tuple[int, str]:
        if self.code_runner is not None:
            await self.code_runner.stop_and_wait()
        return 200, "Stopped"

if __name__ == "__main__":
    bootloader = AlvikHTTPBootloader()
    bootloader.connect_to_wifi("FRITZ!Box 6660 Cable ED", "89755110268842584875")
    bootloader.start()

   