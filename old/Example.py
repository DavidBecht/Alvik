import deviceController as dc 

controller = dc.DeviceController('http://172.20.10.10:80') # IP-Adresse von wifi.py hier einfügen

controller.down(10, 'cm')
controller.up(10, 'cm')
controller.right(10, 'cm')
controller.left(10, 'cm')
