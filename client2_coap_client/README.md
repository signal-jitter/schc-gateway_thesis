CoAP Client (Anwendungsbeispiel)
===================

Die Bibliothek hinter meinem Anwendungscode basiert auf https://github.com/ltn22/SCHC/tree/master/python/examples/coap_client.
In dieser wurden Bitmap-Fehler behoben, die Übertragung von IPs in SCHC-Paketen ermöglicht (Implementierung dedizierter Buffer in der richtigen Größe).
Auch die Portierung der RuleID als LoRa-Port wurde hier implementiert (Änderung SCHC-Cop/Decomp Flow, weiter Methoden ...)

*Hinweis: Erklärungen des Programms befinden sich in Kommentaren im Code*

# Setup
Verwendet wird ein Pycom FiPy auf einem Pytrack-Shield.

Ein aus dem Internet eingehende ICMP-Request, welcher an eine IP eines LoRa-Gerätes gerichtet ist, erkennt der WanRouter und leitet diese an das Gateway weiter.
Das Gateway komprimiert die Nachricht und schickt sie an den LoRaWAN-LNS, welcher das Paket über das Gateway an die Node sendet.

Dort wird das Paket dekomprimiert, als ICMP-Request interpretiert, ein ICMP-Reply generiert und als komprimierte SCHC wieder zurückgeschickt.
Auf demselben Weg kommt die Nachricht dekomprimiert bei dem SCHC-Gateway an, wo es an den Absender zurückgeschickt wird.


**Die blaue LED signalisiert die Bearbeitung/Beantwortung eines Request-Paketes**


## Test
Aufruf eines Ping Befehls unter Windows (vgl. Linux ping6)
```
ping 2001:8d8:[...snap...]:adc9 -n 1 -l 0
```
Bei erfolgreicher doppelter LoRa-Kommunikation (Down- und Uplink) empfängt der Sender das ICMP-Reply:
```
Ping wird ausgeführt für 2001:8d8:1801:84dd:d011:1cc1:c483:adc9 mit 0 Bytes Daten:
Antwort von 2001:8d8:1801:84dd:d011:1cc1:c483:adc9: Zeit=2189ms

Ping-Statistik für 2001:8d8:1801:84dd:d011:1cc1:c483:adc9:
    Pakete: Gesendet = 1, Empfangen = 1, Verloren = 0
    (0% Verlust),
Ca. Zeitangaben in Millisek.:
    Minimum = 2189ms, Maximum = 2189ms, Mittelwert = 2189ms
```