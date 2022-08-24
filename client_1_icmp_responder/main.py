'''
<2022><HBRS - Sören Seeger>
LoRa Class C Node receives SCHC compressed ICMPv6 requests and sends
the equivalent response message over the LoRa/ SCHC/ LNS/ Gateway architecture.

Supports ping request from any device connected to the Internet!
see rules.py for the SCHC compression rule
'''
#FiPy
#DEF00001
#70B3D54992D6A7CC
# (AppK)
#A4B643FFF8F9489A6A03D5CE1F666F55 (AppSk)

from network import LoRa
import socket
import ubinascii
from binascii import unhexlify, hexlify
import struct
import time

from SCHC.RuleMngt import RuleManager
from SCHC.Parser import Parser
from SCHC.Compressor import Compressor
from SCHC.Decompressor import Decompressor
from rules import RULE_PING_REQ as compression_rule_request
from rules import RULE_PING_RESP as compression_rule_response

import pycom
pycom.heartbeat(False)

##SCHC Tools
RM = RuleManager()
RM.addRule(compression_rule_request)
RM.addRule(compression_rule_response)
PARSER = Parser()
COMP = Compressor(RM)
DECOMP = Decompressor(RM)



##LoRaWAN Config
dev_eui =  ubinascii.hexlify(LoRa().mac()).upper()
adr = 'DEF00001'
dev_addr = struct.unpack(">l", ubinascii.unhexlify(adr))[0] #
network_key = '4958F55B7A1AD3FCE52DFFFE12DEB362'
app_key = 'A4B643FFF8F9489A6A03D5CE1F666F55'
nwk_swkey = ubinascii.unhexlify(network_key)
app_swkey = ubinascii.unhexlify(app_key)

src = "2001:08d8:1801:84dd:d011:1cc1:c483:adc9"
ipv6_src = ubinascii.unhexlify(src.replace(':', ''))

print("###################################")
print("     Start IPv6 Ping responder     ")
print("###################################")
print("platform:      "," Lopy - Pysense ")
print("----------LoRa parameters----------")
print("device EUI:    ", str(dev_eui))
print("----------LoRaWAN parameters-------")
print("device adress: ", str(adr))
print("network key:   ", str(network_key))
print("session key:   ", str(app_key))
print("----------IPv6 parameters----------")
print("prefix (LNS):  ", (src[:19]+"::"))
print("identifier:    ", ("::"+src[20:]))


##LoRa SETUP
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, device_class=LoRa.CLASS_C)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

while not lora.has_joined():
    time.sleep(1)
    pycom.rgbled(0)
    time.sleep(1.5)
    pycom.rgbled(0x7f7f00)
    print('connecting...')

print('Joined LoRaWAN')

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

pycom.rgbled(0x007f00)
s.setblocking(True)
s.send(bytes([0x01, 0x02, 0x03])) #welcome message
s.setblocking(False)
time.sleep(1)
pycom.rgbled(0)




#generates fully interpretable IP packet with all fields from a compressed SCHC packet
def schc_2_ip(rx):
    #Decompression
    data = ubinascii.hexlify(rx[0])
    rule_id = rx[1]
    rule_obj = DECOMP.RuleMngt.FindRuleFromID(rule_id)
    buffer, size = DECOMP.apply(rx[0],rule_obj,"bi")

    #IPv6 full package parser
    fields, data = PARSER.parser(buffer)
    print(fields)
    return fields, data

#function (decoupled from SCHC stuff) which generates a response packet for an ICMP request
def potocol_handler(headers, data):
    if headers['IPv6.nextHeader', 1][0] == 58:
        print("potocol_handler: ICMPv6 detected")
        if headers['ICMPV6.TYPE', 1][0] == 128:
            print("potocol_handler: it is ICMP REQUEST")
            print("potocol_handler: creating ICMPv6 RESPONSE")
            #change src_ip and dst_ip, ICMP Type 128-->129
            new_src_p   = headers['IPv6.prefixES', 1]
            new_src_iid = headers['IPv6.iidES', 1]
            new_dst_p   = headers['IPv6.prefixLA', 1]
            new_dst_iid = headers['IPv6.iidLA', 1]
            new_icmp_type = 129

            headers['IPv6.prefixES', 1] = new_src_p
            headers['IPv6.iidES', 1]    = new_src_iid
            headers['IPv6.prefixLA', 1] = new_dst_p
            headers['IPv6.iidLA', 1]    = new_dst_iid
            headers['ICMPV6.TYPE', 1][0]   = new_icmp_type

        else:
            print("ICMP type not supportet")
    else:
        print("protocol not supportet")

    return headers, data

#generates a compressed SCHC packet from the IP packet for the uplink
def ip_2_schc(response, data):
    rule = COMP.RuleMngt.FindRuleFromHeader(response, "up")
    if rule != None:
        res = COMP.apply(response, rule["content"], "up")
        if data != None:
            print("data:")
            print(data)
            res.add_bytes(unhexlify(data))
        print(res.buffer())
        result = res.buffer()
        print("Compressed Header = ", result)
        return result, rule["ruleid"]# sending RuleID as port!

    print("No IP-2-SCHC Rule found")
    return response, 1




while True:
    rx = s.recvfrom(512) # passes received message AND the LoRa port ( in this case RuleID)
    if rx and rx[1] != 0: #if message is received and it is not a control message (port=0)
        pycom.rgbled(0x007f00)
        print(rx)
        headers, data = schc_2_ip(rx)
        response, data = potocol_handler(headers, data)
        print('response')
        print(response)
        payload, rule_port = ip_2_schc(response, data)
        #sends the compressed response to the gateway
        #over a specified port, which specifies the compression ID
        s.bind(rule_port)
        s.send(payload)
        pycom.rgbled(0)
    time.sleep(0.5)
