# Modifizierungen aus dem OpenSCHC Projekt
Neben Fehlerbehebung und allgemeinen Veränderungen werden hier die maßgeblichen Modifizierungen des Codes beschrieben, welche die Funktionsweise fundamental verändern.

Notiz: folgender Teil in Englisch aufgrund der Übernahme dieses Teils aus dem von mir in Englisch kommentierten Source-Code.

# Source (/src)
### compr_core
Modifications:\
RuleID not in package but as separate parameter (cf. 580 ff.)\
IP address conversion to correct hex format (incl. problem handling for odd strings) (cf. 717 ff.)

### gen_roulemanager
New implementation of a rule finder method\
FindRuleFromID (cf. 1140 ff.)\
Was not present - finds a rule for a fixed rule ID (from FPort).

### protocol
Implementation of the separate RuleID to send over the LoRaWAN FPort.\
Rule port transfers at different points (calculation, pass, return) (cf. 208, 213, 248, 258 ff.)\
Attach RuleID to packet in front in case of fragmentation (cf. 269 ff.)\
RuleID built into Recv. method (cf. 274 ff.)\
Self-implemented rule finder built into Decompression (FindRuleFromID) (cf. 315 ff.)\
Payload recover after decompression from the remaining SCHC buffer (cf. 344 ff.)


# Program (/backend-gateway)
###packet_picker
Rules (rule-abc, rule-def) and Config (gateway-config) have been created or adapted for the project

###WAN Router
--completely newly implemented class--\
The WAN router is integrated into the main program and automatically launches packet sniffers at the network interface for all LoRa node IPs.\
These are automatically loaded from the configuration file.\
When the main program is terminated, it is ensured that these sub-processes are also terminated.

###gateway
Json fix (see e.g. 73, 99)\
RulePort transfer + handling (cf. 110 ff.)\
WAN router integration (cf. 251 ff., 257)\
Interface transfers at program call (cf. 207)

###net_aio_core
Adding the payload support.\
Payload as a transfer parameter. (cf. 64 ff.)\
Scapy Imelemntation for sending complete IPv6 packets over the OS interface to the Internet (cf. 85 ff.).\
Implement the RulePort as a parameter for the RuleID across the architecture. (cf. 190, 195 ff.)\
JSON adaptation in the downlink in send_paked/post_data (cf. 202- 217 ) for the format promoted by the LNS.\
Building the structure in _do_post_data (cf. 234 ff.)\
Implementation of an HTTP client sesssion for sending HTT mail with authentication. (cf. 244 ff.)

###packet_picker
Troubleshooting in the delivery of the packages.\
Initial part was cut off. Wrong transmission of raw_packet variables. (cf. 40 ff.)

### iid_provider2
Generates the correct IP address of a LoRa node for passed values (Prefix, SessionKey, EUI).\
can be integrated into a process in an object-oriented manner


# Tools (/weitere Tools)

### coap
Implementation of a Test-CoAP-Client