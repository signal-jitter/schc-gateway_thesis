'''
<2022><HBRS - Sören Seeger>
LoRa Class A Node sends the current temperature on the shield
to a remote generic CoAP server when a button is pressed.
Communication via compressed SCHC-IP packet over LoRaWAN
see rules.py for the SCHC compression rule
'''
#LoPy
#AAA00001
#70B3D54992D6A7CC
#E273233ED4D0D27E5FF06BA27BBE951E (AppK)
#52F3985B646201216B70B1273654953F (AppSk)

from network import LoRa
import socket
import time
import ubinascii
import binascii
from binascii import unhexlify, hexlify
import machine
from machine import Pin
import struct

import pycom
from pysense import Pysense
from SI7006A20 import SI7006A20

import CoAP
from SCHC.RuleMngt import RuleManager
from SCHC.Parser import Parser
from SCHC.Compressor import Compressor
from rules import RULE_COAP as compression_rule

#Pycom Init
pycom.heartbeat(False)

pycom.rgbled(0x7f7f00)
py = Pysense()
dht = SI7006A20(py)
p_in = Pin('P10', mode=Pin.IN, pull=Pin.PULL_UP)

#LoRa Init
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

dev_eui =  ubinascii.hexlify(LoRa().mac()).upper()
app_eui = ubinascii.unhexlify('0000000000000001')
app_key = ubinascii.unhexlify('E273233ED4D0D27E5FF06BA27BBE951E')

dev_addr = struct.unpack(">l", ubinascii.unhexlify('ABC00001'))[0]
network_key = '4958FB2B7A1AD3FCE6B75AFE12DEB362'
app_key = 'E1B643DFF8F9489A6A03D5CE1F6665A9'
nwk_swkey = ubinascii.unhexlify(network_key)
app_swkey = ubinascii.unhexlify(app_key)

#IP Config ###  CoAP Application  ##
src = "2001:08d8:1801:84dd:51d7:bc91:4fb5:0477"

###IP of the CoAP Server
dst = "2a05:d014:0faa:5500:6ff9:8389:cf03:f3c1"
coap_port = 5683

#IP Config
ipv6_src = binascii.unhexlify(src.replace(':', ''))
ipv6_dst = binascii.unhexlify(dst.replace(':', ''))

print("###################################")
print("        Start IPv6 CoAP client     ")
print("###################################")
print("platform:      "," Lopy - Pysense ")
print("----------LoRa parameters----------")
print("device EUI:    ", str(dev_eui))
print("----------LoRaWAN parameters-------")
print("device adress: ", str(dev_addr))
print("network key:   ", str(network_key))
print("session key:   ", str(app_key))
print("----------IPv6 parameters----------")
print("prefix (LNS):  ", (src[:19]+"::"))
print("identifier:    ", ("::"+src[20:]))
print("----------CoAP parameters----------")
print("server adress:  ", dst)
print("server port:    ", coap_port)

##LoRa INIT
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

while not lora.has_joined():
    time.sleep(1)
    pycom.rgbled(0)
    time.sleep(1.5)
    pycom.rgbled(0x7f7f00)
    print('connecting...')

print('Joined LoRaWAN')
pycom.rgbled(0x007f00)

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
print('LoRa Init finished!')




##SCHC-Tools
RM = RuleManager()
RM.addRule(compression_rule)
PARSER = Parser()
COMP = Compressor(RM)

#generates an generic IP-UDP-(CoAP) Paket
def make_ipudp_buffer(ips, ipd, source_port, destination_port, ulp, payload):
    print("Ips:")
    print(ips)
    print("IpD:")
    print(ipd)

    retval = struct.pack('!HHHBB', 0x6000, 0x0000, len(ulp) + 8, 17, 30) + ips + ipd + struct.pack("!HHHH", source_port, destination_port, (len(ulp)+ len(payload) + 8 + 1), 0x0000)
    retval += ulp
    retval += struct.pack('!B', 0xFF)
    retval += payload

    print("RET:")
    print(retval)
    return retval

#generates an generic CoAP-Message
def make_coap_package(path, data):
    """ Compresses and sends dummy data """
    coap_message = CoAP.Message()
    coap_message.new_header(type=CoAP.CON, code=CoAP.POST, midSize=4, token=0x82)
    coap_message.add_option_path(path)
    coap_message.end_option()

    payload =  str(data)
    pl_byte = bytes(payload, 'ascii')

    print("BUFFER: ", coap_message.buffer)
    ipv6 = make_ipudp_buffer(ipv6_src, ipv6_dst, coap_port, coap_port, coap_message.buffer, pl_byte)
    return ipv6

#compresses the IP packet according to the available rules
def schc_compress(pkg):
    fields, data = PARSER.parser(pkg)
    #search for a rule where all field definitions match
    rule = COMP.RuleMngt.FindRuleFromHeader(fields, "up")
    if rule != None:
        rule_port = rule["ruleid"]
        res = COMP.apply(fields, rule["content"], "up")
        print("data:")
        print(data)
        print(hexlify(data))
        res.add_bytes(data)
        print(res.buffer())
        result = res.buffer()
        print("Compressed Header = ", result, " - on Rule/Port: ", rule_port)
        #Header and RuleID SEPERATED !!
        return result, rule_port


while True:
    time.sleep(0.1)
    if p_in() == 0:
        pycom.rgbled(0x0000ff)

        #Application - make generic CoAP PKG
        coap_path = 'basic'
        coap_data = dht.temperature()
        pkg_to_send = make_coap_package(coap_path, coap_data)

        #Interface/ Paket Sink - compress and send
        data, rule_port = schc_compress(pkg_to_send)
        s.setblocking(True)

        # sends the compressed response to the gateway
        # over a specified port, which specifies the compression ID
        s.bind(rule_port)
        s.send(data)
        s.setblocking(False)
        pycom.rgbled(0x000000)
