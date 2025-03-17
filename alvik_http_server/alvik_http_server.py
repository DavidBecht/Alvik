import socket
import time

try:
    from typing import Callable, Union, Tuple
except ImportError:
    Callable = None  # Platzhalter, da MicroPython kein `typing` hat
    Tuple = None
    Union = None
import network
from alvik_logger.logger import logger, get_error_message
import os
try:
    import ure  # Im ESP32 heißt das Regexmodul ure
except ImportError:
    import re as ure
try:
    from arduino_alvik import ArduinoAlvik
    alvik = ArduinoAlvik() # um eine IP Adresse zu bekommen
except ImportError:
    pass

HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}

class AlvikHTTPServer:
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
        self.add_endpoint("GET /", lambda _, __: self._html)



    def connect_to_wifi(self, ssid:str, password:str) -> str:
        """!
        Stellt eine Verbindung zum WLAN her.

        @return Die IP-Adresse des Geräts.
        """
        self._ssid = ssid
        self._password = password
        logger.info(f"Connect to WLAN with ssid:'{self._ssid}' and pw:'{self._password}'")
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.disconnect()  # Trenne vorherige Verbindung, falls vorhanden

        wlan = network.WLAN(network.STA_IF)  # WLAN im Station-Modus (Client)
        wlan.active(True)

        logger.info("Scanne nach WLANs...")
        networks = wlan.scan()

        networks_str_list = []
        for net in networks:
            networks_str_list.append(f"{net[0].decode()} (Signal: {net[3]} dBm)")
        logger.info(f"Gefundene WLANs: {networks_str_list}")

        logger.info("Scan abgeschlossen.")

        wlan.connect(self._ssid, self._password)
        logger.info("Connecting to Wi-Fi...")
        timeout = 20
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                logger.error("WLAN-Verbindung fehlgeschlagen (Timeout)")
                wlan.disconnect()  # Trenne vorherige Verbindung, falls vorhanden
                wlan.active(False)
                raise Exception("WLAN-Verbindung fehlgeschlagen (Timeout)")
            status = wlan.status()
            if status == network.STAT_WRONG_PASSWORD:
                status = f"{status}:Falsches WLAN-Passwort"
            elif status == network.STAT_NO_AP_FOUND:
                status = f"{status}:WLAN-SSID nicht gefunden"
            elif status == network.STAT_CONNECTING:
                status = f"{status}:Am verbinden"
            else:
                status = f"{status}:unkown"
            logger.info(f"Trying to connect to WIFI. Status: {status}")
            time.sleep(1)  # Kurze Pause, um CPU zu schonen
        print("Connected to Wi-Fi")
        self._ip_address = wlan.ifconfig()[0]
        print("IP address:", self._ip_address)
        return self._ip_address

    def _read_index_html(self) -> None:
        logger.info(f"Reading HTML file: '{self._filepath_index_html}'")
        with open(self._filepath_index_html, "r") as fp:
            self._html = fp.read().encode("UTF-8")

    def _receive_entire_http_request(self, client: socket, block_size: int = 1024, timeout: int = 10) -> str:
        request = b""
        client.settimeout(timeout)  # Setze ein Timeout für `recv()`
        try:
            while True:
                chunk = client.recv(block_size)
                if not chunk:
                    break  # Verbindung wurde geschlossen
                request += chunk

                # Prüfe, ob die Anfrage vollständig ist (HTTP-Ende erreicht)
                if b"\r\n\r\n" in request:
                    break
        except OSError as e: # Fehler beim Lesen (MicroPython wirft `OSError`, nicht `socket.timeout`)
            logger.error(f"Socket-Fehler: {e}")
        logger.debug(f"Received request with {len(request)} Bytes of data")
        request_str = request.decode('utf-8')
        return request_str

    def add_endpoint(self, endpoint_url: str, callback: Callable[[str, socket], Union[str, Tuple[int, str], bytes]]):
        """Registriert einen neuen Endpoint.

         @return String -> HTTP Response mit HTTP Status Code 200
         @return (int, String) -> HTTP Repsonse mit HTTP Status Code (int)
         @return Bytes -> RAW-Response
        """
        # self._registered_endpoints[endpoint_url] = callback
        escaped = self._regex_escape(endpoint_url)  # Escaped alle Zeichen (z. B. / -> \/, . -> \.)
        regex_with_wildcard = ure.sub(r'\\\*', r'.*', escaped)
        self._registered_endpoints[endpoint_url] = {"callback": callback, "regex": ure.compile("^" + regex_with_wildcard + "$")}

    def _send_response(self, client: socket.socket, status: int, content: str):
        """Sendet eine HTTP-Response an den Client."""
        response = f"HTTP/1.1 {HTTP_STATUS_CODES.get(status, '500 Error Code not found')}\r\nContent-Type: text/plain\r\n\r\n{content}"
        client.sendall(response.encode("utf-8"))
        client.close()

    def start_web_server(self, ip="0.0.0.0", port=80):
        """!
        Startet den Webserver zur Steuerung des Alvik-Roboters.

        @param ip Die IP-Adresse des Geräts.
        """
        self._read_index_html()
        addr = (ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(addr)
        sock.listen(1)
        print(f"Web server running on http://{ip}:{port}")

        while True:
            cl, addr = sock.accept()
            logger.info(f"Client connected: {addr}")
            try:
                # cl.settimeout(2)
                request = self._receive_entire_http_request(cl)

                # HTTP-Request-Zeile extrahieren (z. B. "GET /hello HTTP/1.1")
                request_lines = request.split("\r\n")
                if not request_lines:
                    return self._send_response(cl, 400, "Invalid request.")

                # Erste Zeile in Methode und URL aufteilen
                request_line_parts = request_lines[0].split(" ")
                if len(request_line_parts) < 2:
                    return self._send_response(cl, 400, "Malformed request.")

                method, path = request_line_parts[:2]  # Beispiel: "GET" und "/hello"
                endpoint = f"{method} {path}"

                # Prüfe, ob der Endpoint registriert ist
                matches = [v for k,v in self._registered_endpoints.items() if self._regex_fullmatch(v['regex'], endpoint)]
                if len(matches) > 0 and matches[0] is not None:
                    logger.debug(f"Handling request for {endpoint}")
                    response_content = matches[0]["callback"](request, cl)

                    if isinstance(response_content, bytes):
                        cl.send(response_content) # RAW Response
                    elif isinstance(response_content, tuple) and len(response_content) == 2 and \
                        isinstance(response_content[0], int) and isinstance(response_content[1], str):
                        self._send_response(cl, response_content[0], response_content[1]) # HTTP Response StatusCode, Message
                    elif isinstance(response_content, str):
                        self._send_response(cl, 200, response_content)  # HTTP Response 200, Message
                    else:
                        logger.error("Wrong return value of endpoint")
                        # raise ValueError("Wrong return value of endpoint")
                else:
                    logger.debug(f"Endpoint {endpoint} not found")
                    self._send_response(cl, 404, "Endpoint not found.")
            except Exception as e:
                error_trace = get_error_message(e)
                logger.error(f"Handling endpoint request failed with Error: {str(e)}\n{error_trace}\n".encode("utf-8"))
                self._send_response(cl, 500, f"Handling endpoint request failed with Error: {str(e)}\n{error_trace}")
            finally:
                cl.close()
    def _regex_escape(self, s: str) -> str:
        """Escape für reguläre Ausdrücke in MicroPython (ersetzt `re.escape()`)."""
        special_chars = r".^$*+?{}[]\|()"
        return "".join("\\" + c if c in special_chars else c for c in s)

    def _regex_fullmatch(self, pattern, string):
        """Ersatz für `re.fullmatch()` in MicroPython."""
        match = ure.match(pattern, string)  # Prüfe, ob es einen Anfangs-Match gibt
        return match is not None

if __name__ == "__main__":
    """!
    Hauptprogramm zur Initialisierung und Steuerung.
    """
    print(os.listdir(".."))
    controller = AlvikHTTPServer("../bootloader_index.html")
    controller.start_web_server()