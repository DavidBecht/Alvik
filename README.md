# 📖 Anleitung: Alvik-Roboter mit dem WebController steuern

---

Diese Anleitung zeigt dir, wie du deinen Alvik-Roboter mit `DeviceController` steuerst.

---

## 1️⃣ **Vorbereitungen**

📁 Stelle sicher, dass sich die Datei `deviceController.py` im gleichen Ordner wie dein Python-Skript befindet.

---

## 2️⃣ **Webserver starten**

🖥️ Starte den Webserver `alvikWebController.py` in Arduino Lab for MicroPython, bevor du die Steuerung ausführst.

---

## 3️⃣ **Instanz der Klasse erstellen**

📋 Erstelle eine Instanz von `DeviceController` mit der IP-Adresse deines Alvik-Roboters:

```python
import deviceController # Importiere die Bibliothek

# Verbindung zum Roboter herstellen
controller = alviktest.DeviceController('http://172.20.10.6:80') # Ersetze die URL mit 
# der URL aus der Konsole des AlvikWebControllers

```

---

## 4️⃣ **Bewegungsbefehle ausführen**

📌 Steuere den Roboter mit folgenden Befehlen:

```python
controller.up(10, 'cm')    # Bewegt den Roboter 10 cm vorwärts
controller.down(5, 'cm')   # Bewegt den Roboter 5 cm rückwärts
controller.left(90) # Dreht den Roboter um 90° nach links
controller.right(90)# Dreht den Roboter um 90° nach rechts

```

🔄 **Parameter:**

- Der erste Wert gibt die Distanz oder den Winkel (in Grad) an.
- Der zweite Wert gibt die Einheit an (`'cm'` ,`'m'` ….)

---

## 5️⃣ **Browser öffnen (optional)**

🌍 Falls der Webserver eine Benutzeroberfläche bietet, kannst du die **IP-Adresse** des Roboters in die Adresszeile deines Browsers eingeben:

```
http://172.20.10.6:80
```

🎉 **Viel Spaß beim Steuern deines Alvik-Roboters!** 🚗💨

---

⚠️ **Wichtig:**

- Dein Computer oder Smartphone muss sich im gleichen WLAN-Netzwerk wie der Roboter befinden.
- Falls nötig, stoppe den Webserver mit `Strg+C` in der Konsole.

👉 **Jetzt bist du bereit, loszulegen!** 🥳
