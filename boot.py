# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()
from arduino_alvik import ArduinoAlvik
from alvik_http_bootloader_server import AlvikHTTPBootloader
alvik = ArduinoAlvik()
try:
    alvik.left_led.set_color(0, 1, 0)  # rgb -> red for error
    bootloader = AlvikHTTPBootloader()
    bootloader.start_hotspot()
    bootloader.start()
except:
    alvik.left_led.set_color(1, 0, 0) # rgb -> red for error

