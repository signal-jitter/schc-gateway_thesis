IPv6 über LoRaWAN
===================

Implementierung eines Gesamtsystems zur Übertragung von IPv6-Paketen über LoRa-Endgeräte.

# Konzept
Lora-Endgeräte sind an ein LoRaWAN Netzwerk angebunden.
Sämtliche Up- und Downlink Nachrichten werden von dem Lora-Network-Server(LNS) an ein Backend übermittelt.
Dieses Backend dient als Gateway zwischen der LoRa-Kommunikation und der ein und ausgehenden IPv6-Kommunikation.
Da generische IPv6-Pakete aufgrund ihrer Größe für LPWANS wie LoRaWAN ungeeignet sind, wird das Static-Context-Header-Compression Verfahren (SCHC) verwendet, um die IP-Pakete zu komprimieren und/ oder zu fragmentieren.


# Architektur
![Alt text](architektur2.png?raw=true "Architektur")


# Implementierung

Umgesetzt in diesem Projekt wurden:


### LoRa-CoAP Client
LoRa-Node sendet auf Knopfdruck eine CoAP-Nachricht mit der aktuellen Temperatur an einen generischen CoAP-Server, welcher unter einer IPv6-Adresse erreichbar ist \
*(siehe /client_2_cloap_client)*

### LoRa-Ping Responder Client
LoRa-Node empfängt ICMPv6 Request Paket und antwortet mit passendem Response (über LoRaWAN/ den oben beschriebenen Stack) 

*(siehe /client_2_cloap_client)*

### LoRaWAN Gateway
Konfiguriert als Gateway für den eigenen privaten LoRaWAN-Server

### LoRaWAN Netzwerk Server
verwendet wurde das Open-Source Projekt von Petr Gotthard:\
https://github.com/gotthardp/lorawan-server

Backend, Handler und Connectoren wurden für diese Architektur angepasst und erstellt.\
*(SCHC Backend Adapter)*


### SCHC Gateway
Basis für das Gateway, das dazugehörige Interface und das SCHC-Verfahren ist das OpenSCHC Projekt\
https://github.com/openschc/openschc

Um die Anforderungen dieses Projektes zu erfüllen, wurde es angepasst und verändert. So u.a.
- genieren von echten IPv6-Paketen zur Übertragung ins Internet
- weiterleiten von ausgehenden IP-Paketen an die Netzwerkschnittstelle des Servers (ins Internet)
- ein in das System integrierter und automatischer Listener, welcher aus dem Internet eingehende IP-Pakete an LoRa Geräte erkennt und an das Gateway weiterleitet 
- RuleID übertragen im LoRaWAN FPort-Feld (konform zu TS010-1.0.0 LoRa Alliance)
- zusätzliche SCHC-Regeln für das Betreiben der Beispiel-Clients
- Übermittlung von Payloads
- Fix von Fehlfunktionen (entstanden durch Python Versionsportierung)
- usw.

__(eine genaue Erläuterung aller Anpassungen befindet sich [HIER](SCHC-Backend-Gateway/modifizierungen.md) und in der Dokumentation)__


### Server
LNS und Gateway laufen gemeinsam auf einem V-Server bei IONOS.
Für den Server steht ein ganzes 64er-IPv6-Subnetz zur Verfügung.

IP-Adressen für die Nodes wurden nach TS010-1.0.0 (LoRa Alliance) berechnet und auf dem Server konfiguriert.

Um die ICMP Nachrichten an das LoRa Gerät "durchzuschleusen" wurde das entsprechende Modul der Server Netzwerkschnittstelle deaktiviert 
*(net.ipv6.icmp.echo_ignore_all)*.


### Entwicklungsumgebung
Die Anordnung in dem Entwicklungsaufbau war wie folgend:

![](Entwicklungsumgebung.png)
# Setup - Konfiguration
*weiterführende Informationen in den jeweiligen READMEs der Ordner*

### Nodes:
FiPy und LoPy der Firma Pycom (Micropython)

### Gateway
PyGate der Firma Pycom (Micropython) - Konfiguration wie angegeben (LNS IP anpassen)

### LNS
uplink (LNS --> Gateway)
- json {addr, data, port} to localhost:51225/ul

downlink (Inet --> Gateway)
- REST API - post to localhost:51225/dl

downlink (Gateway --> LNS)
- REST API - post to localhost:8080/in/{devaddr}

