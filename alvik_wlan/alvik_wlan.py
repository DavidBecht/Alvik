import time
import network
from alvik_logger.logger import logger
from alvik_utils.utils import is_micropython

class AlvikWlan:
    @staticmethod
    def start_hotspot(ssid: str, password: str) -> str:
        if not is_micropython():
            logger.info("Hotspot is only available in Micropython")
            return ""
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=ssid, password=password, authmode=network.AUTH_WPA_WPA2_PSK)

        logger.info(f"Starting Hotspot: SSID={ssid}")
        timeout = 20
        start_time = time.time()
        while not ap.active() and time.time() < start_time + timeout:
          time.sleep(1)
          logger.info(f"Waiting for Hotspot to get active")

        ip_address = ap.ifconfig()[0]
        logger.info(f"Hotspot active, IP address: {ip_address}")
        return ip_address

    @staticmethod
    def scan_wlan_ssids(wlan):
        wlan.active(True)
        logger.info("Scanne nach WLANs...")
        networks = wlan.scan()

        networks_str_list = []
        networks_ssids = []
        for net in networks:
            networks_ssids.append(net[0].decode())
            networks_str_list.append(f"{net[0].decode()} (Signal: {net[3]} dBm)")
        logger.info(f"Gefundene WLANs: {networks_str_list}")
        logger.info("Scan abgeschlossen.")
        return networks_ssids

    @staticmethod
    def connect_to_wifi(ssid:str, password:str) -> str:
        """!
        Stellt eine Verbindung zum WLAN her.

        @return Die IP-Adresse des Geräts.
        """
        if not is_micropython():
            logger.info("Connect to Wifi is only available in Micropython")
            return ""
        logger.info(f"Connect to WLAN with ssid:'{ssid}' and pw:'{password}'")
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.disconnect()  # Trenne vorherige Verbindung, falls vorhanden

        networks_ssids = AlvikWlan.scan_wlan_ssids(wlan)

        if ssid not in networks_ssids:
            logger.error(f"Netzwerk SSID '{ssid}' nicht gefunden")
            raise AttributeError(f"Netzwerk SSID '{ssid}' nicht gefunden")

        wlan.connect(ssid, password)
        logger.info("Connecting to Wi-Fi...")
        timeout = 20
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() > timeout + start_time:
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
        logger.info("Connected to Wi-Fi")
        ip_address = wlan.ifconfig()[0]
        logger.info(f"IP address: {ip_address}")
        return ip_address