from asyncio import StreamReader
from alvik_utils.upy_streamwriter import UPYStreamWriter, HTTP_STATUS_CODES
from alvik_utils.utils import get_error_message
from alvik_wlan.alvik_wlan import AlvikWlan
import socket
from alvik_logger.logger import logger
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
try:
    from typing import Callable, Union, Tuple
except ImportError:
    Callable = None  # Platzhalter, da MicroPython kein `typing` hat
    Tuple = None
    Union = None
try:
    import ure  # Im ESP32 heißt das Regexmodul ure
except ImportError:
    import re as ure
try:
    from arduino_alvik import ArduinoAlvik
    alvik = ArduinoAlvik() # um eine IP Adresse zu bekommen
except ImportError:
    pass



class AlvikHTTPServer:

    class SPECIAL_RESPONSE_CODES:
        STREAM = 1111

    def __init__(self, filepath_index_html:str):
        """!
        Initialisiert die AlvikWebController-Klasse.

        @param ssid Die SSID des WLAN-Netzwerks.
        @param password Das Passwort des WLAN-Netzwerks.
        """
        self._filepath_index_html = filepath_index_html
        self._ssid = ""
        self._password = ""
        self._html:bytes = b""
        self._ip_address = "0.0.0.0"
        self._registered_endpoints = {}
        self.add_endpoint("GET /", self._endpoint_get_index)

    async def _endpoint_get_index(self, _, __):
        return self._html

    def start_hotspot(self, ssid: str, password: str) -> str:
        self._ssid = ssid
        return AlvikWlan.start_hotspot(self._ssid, password)

    def connect_to_wifi(self, ssid: str, password: str) -> str:
        self._ssid = ssid
        return AlvikWlan.connect_to_wifi(self._ssid, password)

    def _read_index_html(self) -> None:
        logger.info(f"Reading HTML file: '{self._filepath_index_html}'")
        with open(self._filepath_index_html, "r") as fp:
            self._html = fp.read().encode("UTF-8")

    async def _receive_entire_http_request(self, reader: StreamReader, block_size: int = 1024, timeout: int = 10) -> str:
        request = b""
        # TODO may add a timeout of 10 seconds
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                break  # Verbindung wurde geschlossen
            request += chunk
            # Prüfe, ob die Anfrage vollständig ist (HTTP-Ende erreicht)
            if b"\r\n\r\n" in request:
                break
        logger.debug(f"Received request with {len(request)} Bytes of data")
        request_str = request.decode('utf-8')
        return request_str

    def add_endpoint(self, endpoint_url: str, callback: Callable[[str, socket], Union[str, Tuple[int, str], bytes]]):
        """Registriert einen neuen Endpoint.

         @return String -> HTTP Response mit HTTP Status Code 200
         @return (int, String) -> HTTP Repsonse mit HTTP Status Code (int)
         @return Bytes -> RAW-Response
        """
        escaped = self._regex_escape(endpoint_url)  # Escaped alle Zeichen (z. B. / -> \/, . -> \.)
        regex_with_wildcard = ure.sub(r'\\\*', r'.*', escaped)
        self._registered_endpoints[endpoint_url] = {"callback": callback, "regex": ure.compile("^" + regex_with_wildcard + "$")}

    async def _start_async_web_server(self, ip="0.0.0.0", port=80):
        server = await asyncio.start_server(self._handle_client, ip, port, backlog=5)
        logger.info(f"Server running on http://{ip}:{port}")
        while True:
            await asyncio.sleep(0.1)  # MicroPython hat kein serve_forever(), also brauchen wir eine Endlosschleife

    async def _handle_client(self, reader, writer):
        logger.info(f"Client connected.")
        response_content = None
        try:
            request_str = await self._receive_entire_http_request(reader)
            writer = UPYStreamWriter(writer)
            if len(request_str) == 0:
                logger.debug("No data received")
                await writer.aclose()
                return
            request_line = request_str.split("\r\n")[0]
            method, path, _ = request_line.split(" ", 2)
            endpoint = f"{method} {path}"
            matches = [v for k, v in self._registered_endpoints.items() if self._regex_fullmatch(v['regex'], endpoint)]
            if len(matches) > 0 and matches[0] is not None:
                logger.debug(f"Handling request for {endpoint}")
                response_content = await matches[0]["callback"](request_str, writer)
                if response_content == AlvikHTTPServer.SPECIAL_RESPONSE_CODES.STREAM:
                    return # in case of streams we can not close the writer!
                elif isinstance(response_content, bytes):
                    await writer.awrite(response_content)  # RAW Response
                elif isinstance(response_content, tuple) and len(response_content) == 2 and \
                        isinstance(response_content[0], int) and isinstance(response_content[1], str):
                    await writer.send_response(response_content[0], response_content[1])  # HTTP Response StatusCode, Message
                elif isinstance(response_content, str):
                    await writer.send_response(200, response_content)  # HTTP Response 200, Message
                else:
                    logger.error("Wrong return value of endpoint")
                    raise ValueError("Wrong return value of endpoint")
            else:
                logger.error(f"Endpoint {endpoint} not found")
                await writer.send_response(404, "Endpoint not found")
        except Exception as e:
            error_trace = get_error_message(e)
            logger.error(f"Handling endpoint request failed with Error: {str(e)}\n{error_trace}\n".encode("utf-8"))
            await writer.send_response(500, f"Error: {str(e)}")
        finally:
            logger.info("Client request handled.")
            if response_content != AlvikHTTPServer.SPECIAL_RESPONSE_CODES.STREAM:
                await writer.aclose()

    def start_web_server(self, ip="0.0.0.0", port=80):
        """!
        Startet den Webserver zur Steuerung des Alvik-Roboters.

        @param ip Die IP-Adresse des Geräts.
        """
        self._read_index_html()
        asyncio.run(self._start_async_web_server(ip, port))

    def _regex_escape(self, s: str) -> str:
        """Escape für reguläre Ausdrücke in MicroPython (ersetzt `re.escape()`)."""
        special_chars = r".^$*+?{}[]\|()"
        return "".join("\\" + c if c in special_chars else c for c in s)

    def _regex_fullmatch(self, pattern, string):
        """Ersatz für `re.fullmatch()` in MicroPython."""
        match = ure.match(pattern, string)  # Prüfe, ob es einen Anfangs-Match gibt
        return match is not None

if __name__ == "__main__":
    controller = AlvikHTTPServer("../bootloader_index.html")
    controller.start_hotspot("david_alvik", "12345678")
    controller.start_web_server()