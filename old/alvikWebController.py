"""! @brief AlvikWifi V1.0"""


##
# @mainpage Alvik Web Controller
#
# @section description_main Beschreibung
# Dieses Skript implementiert eine Webschnittstelle zur Steuerung eines Alvik-Roboters.
# Es verbindet sich mit einem WLAN-Netzwerk, startet einen Webserver und verarbeitet 
# Steuerbefehle, die über die Weboberfläche gesendet werden.
#
# @section notes_main Hinweise
# - Basierend auf Arduino und Micropython.
# - Ermöglicht Echtzeitsteuerung des Roboters.
# - Schulprojekt 2025.
#
# Copyright (c) 2025 Jannik & Thomas.  All rights reserved.

from arduino_alvik import ArduinoAlvik
from machine import UART
import sys
import socket
import network

class AlvikWebController:
    """!
    Klasse zur Steuerung des Alvik-Roboters über eine Webschnittstelle.
    """
    def __init__(self, ssid, password):
        """!
        Initialisiert die AlvikWebController-Klasse.

        @param ssid Die SSID des WLAN-Netzwerks.
        @param password Das Passwort des WLAN-Netzwerks.
        """
        self.ssid = ssid
        self.password = password
        self.alvik = ArduinoAlvik()
        self.html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Alvik Control</title>
            <style>
                body { text-align: center; font-family: Arial, sans-serif; margin-top: 50px; }
                button { width: 100px; height: 50px; font-size: 20px; margin: 10px; }
            </style>
        </head>
        <body>
            <h1>Alvik Robot Control</h1>
            <button id="upButton" onmousedown="startCommand('up')" onmouseup="stopCommand()" onmouseleave="stopCommand()">Up</button><br>
            <button id="leftButton" onmousedown="startCommand('left')" onmouseup="stopCommand()" onmouseleave="stopCommand()">Left</button>
            <button id="downButton" onmousedown="startCommand('down')" onmouseup="stopCommand()" onmouseleave="stopCommand()">Down</button>
            <button id="rightButton" onmousedown="startCommand('right')" onmouseup="stopCommand()" onmouseleave="stopCommand()">Right</button>

            <script>
                let intervalId; // Interval ID for repeated execution
                let isProcessing = false; // Verhindert gleichzeitige Anfragen

                function startCommand(direction) {
                    sendCommand(direction); // Send initial command immediately
                    intervalId = setInterval(() => {
                        sendCommand(direction);
                    }, 300); // Sends command every 300 ms
                }

                function stopCommand() {
                    clearInterval(intervalId);
                }

                function sendCommand(direction) {
                    if (isProcessing) return; // Prevents overlapping requests
                    isProcessing = true;

                    fetch('/command?dir=' + direction)
                        .then(() => console.log('Command sent:', direction))
                        .catch(err => console.error('Error:', err))
                        .finally(() => isProcessing = false); // Reset processing flag
                }
            </script>
        </body>
        </html>
        """

    def connect_to_wifi(self):
        """!
        Stellt eine Verbindung zum WLAN her.

        @return Die IP-Adresse des Geräts.
        """
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.password)
        print("Connecting to Wi-Fi...")
        while not wlan.isconnected():
            pass
        print("Connected to Wi-Fi")
        ip_address = wlan.ifconfig()[0]
        print("IP address:", ip_address)
        return ip_address

    def start_web_server(self, ip):
        """!
        Startet den Webserver zur Steuerung des Alvik-Roboters.

        @param ip Die IP-Adresse des Geräts.
        """
        addr = (ip, 80)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(addr)
        sock.listen(1)
        print(f"Web server running on http://{ip}:80")

        self.alvik.begin()
        self.alvik.left_led.set_color(0, 1, 0)
        self.alvik.right_led.set_color(0, 1, 0)

        while True:
            cl, addr = sock.accept()
            print(f"Client connected: {addr}")
            request = cl.recv(1024).decode('utf-8')
            print(f"Request: {request}")

            if "GET / " in request:
                response = self.html
            elif "GET /command?dir=" in request:
              # Extrahiere direction und optional distance aus der Anfrage
              try:
                  # Beispiel-URL: /command?dir=up&distance=10
                  query = request.split("GET /command?")[1].split(" ")[0]
                  params = dict(param.split('=') for param in query.split('&') if '=' in param)
  
                  direction = params.get('dir')
                  distance = int(params.get('distance', 5))
                  unit = params.get('unit', 'cm')
  
                  self.handle_command(direction, distance, unit)
                  response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
  
              except Exception as e:
                  print("Fehler beim Verarbeiten der Anfrage:", e)
                  response = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nFehlerhafte Anfrage"

            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"

            cl.send(response.encode('utf-8'))
            cl.close()

    def handle_command(self, direction, distance=5, Unit = 'cm'):
      """!
      Verarbeitet Steuerbefehle für den Alvik-Roboter.
  
      @param direction Die Bewegungsrichtung ('up', 'down', 'left', 'right').
      @param distance Die Distanz (Standard: 5).
      """
      if direction == 'up':
          print(f"Move up by {distance}")
          self.alvik.move(distance, blocking=False, unit = Unit)
      elif direction == 'down':
          print(f"Move down by {distance}")
          self.alvik.move(-distance, blocking=False, unit = Unit)
      elif direction == 'left':
          print(f"Rotate left by {distance}")
          self.alvik.rotate(distance, blocking=False)
      elif direction == 'right':
          print(f"Rotate right by {distance}")
          self.alvik.rotate(-distance, blocking=False)

    def stop(self):
        """!
        Stoppt den Roboter und beendet das Programm.
        """
        print("Stopping server and robot.")
        self.alvik.stop()
        sys.exit()

if __name__ == "__main__":
    """!
    Hauptprogramm zur Initialisierung und Steuerung.
    """
    try:
        controller = AlvikWebController("", "") # Hotspot-Name und Passwort hier einfügen
        ip_address = controller.connect_to_wifi()
        controller.start_web_server(ip_address)
    except KeyboardInterrupt:
        controller.stop()
