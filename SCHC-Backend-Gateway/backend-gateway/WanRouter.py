'''
<2022><HBRS - Sören Seeger>

--completely newly implemented class--

The WAN router is integrated into the main program and automatically launches packet sniffers at the network interface for all LoRa node IPs.
These are automatically loaded from the configuration file.
When the main program is terminated, it is ensured that these sub-processes are also terminated.
'''

import sys
import json
from subprocess import Popen
import atexit


class WanRouter:
    data = {}
    end_devices = []
    routing_processes = []

    def __init__(self, uri):
        f = open(uri)
        self.data = json.load(f)
        atexit.register(self.cleanup)


    def start(self, interface, url):
        for adr, conf in self.data['route'].items():
            if conf['ifname'] == 'lpwan':
                self.end_devices.append(adr)

        for device in self.end_devices:
            dst = 'dst ' + device
            process = Popen(['./packet_picker.py', '-i', interface, url, '--untrust', '-d', '-F', dst],
                            shell=False)
            self.routing_processes.append(process)

    def stop(self):
        sys.exit()

    def cleanup(self):
        for p in self.routing_processes:
            p.kill()
        print("IMPORTANT: All listeners stopped!")



