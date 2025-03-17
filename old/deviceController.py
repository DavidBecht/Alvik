import requests
import time

class DeviceController:
    def __init__(self, base_url: str):
        self.base_url = base_url + "/command?dir="
    
    def _send_command(self, command: str):
        url = f"{self.base_url}{command}"
        try:
            response = requests.get(url)
            
            print(f"Befehl: {command}")
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)

            if response.status_code == 200:
                print(f"Befehl '{command}' erfolgreich gesendet.\n")
            else:
                print(f"Fehler bei der Anfrage für '{command}': {response.status_code}\n")

            time.sleep(0.3)

        except requests.RequestException as e:
            print(f"Anfrage für '{command}' fehlgeschlagen:", e)

    def up(self, distance = 5, unit = 'cm'):
        self._send_command(f"up&distance={distance}&unit={unit}")

    def down(self, distance = 5, unit = 'cm', speed = 0.1):
        self._send_command(f"down&distance={distance}&unit={unit}")

    def left(self, distance = 5, unit = 'cm', speed = 0.1):
        self._send_command(f"left&distance={distance}&unit={unit}")

    def right(self, distance = 5, unit = 'cm', speed = 0.1):
        self._send_command(f"right&distance={distance}&unit={unit}")
