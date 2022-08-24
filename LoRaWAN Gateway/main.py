from network import ETH
import time
import machine
from machine import RTC
import pycom
import socket

print('\nStarting LoRaWAN concentrator')
# Disable Hearbeat
pycom.heartbeat(False)

# Define callback function for Pygate events
def machine_cb (arg):
    evt = machine.events()
    if (evt & machine.PYGATE_START_EVT):
        # Green
        pycom.rgbled(0x103300)
    elif (evt & machine.PYGATE_ERROR_EVT):
        # Red
        pycom.rgbled(0x331000)
    elif (evt & machine.PYGATE_STOP_EVT):
        # RGB off
        pycom.rgbled(0x000000)

# register callback function
machine.callback(trigger = (machine.PYGATE_START_EVT | machine.PYGATE_STOP_EVT | machine.PYGATE_ERROR_EVT), handler=machine_cb)


eth = ETH()
#eth.init("hostname")
print("connecting to ETH...")
while not eth.isconnected():
    time.sleep(1)
    print(".", end='')

print(eth.ifconfig())
print(socket.getaddrinfo("pycom.io", 80))
print(" OK")

# Sync time via NTP server for GW timestamps on Events
print('Syncing RTC via ntp...', end='')
rtc = RTC()
rtc.ntp_sync(server="pool.ntp.org")

while not rtc.synced():
    print('.', end='')
    time.sleep(.5)
print(" OK\n")

# Read the GW config file from Filesystem
with open('/flash/global_conf.json','r') as fp:
    buf = fp.read()

# Start the Pygate
machine.pygate_init(buf)
# disable degub messages
machine.pygate_debug_level(1)
