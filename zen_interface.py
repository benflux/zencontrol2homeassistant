#!/usr/bin/env python3
# zen_interface.py
#
# Higher-level interface on top of zen.py to manage devices/states.

import time
import struct
import colorama
from colorama import Fore, Style
from zen import ZenProtocol

colorama.init()

class ZenInterface:
    """High-level interface to Zencontrol TPI (using ZenProtocol)."""

    def __init__(self, host, port, mac=None, debug=False):
        self.protocol = ZenProtocol(host, port, mac, debug=debug)
        self.debug = debug
        self.lights = {}
        self.groups = {}
        self.scenes = {}

        self.protocol.set_recv_callback(self.handle_incoming)
        self.protocol.connect()

    def close(self):
        """Close the underlying protocol connection."""
        self.protocol.close()

    def handle_incoming(self, data):
        """Callback for incoming packets from TPI protocol."""
        if self.debug:
            print(Fore.CYAN + f"[ZenInterface] Incoming data: {data}" + Style.RESET_ALL)
        # Original code might parse data to update self.lights, self.groups, etc.

    def refresh_all_devices(self):
        """Query TPI for all known devices."""
        cmd_id = 0x01  # hypothetical 'QUERY_ALL_DEVICES'
        packet = self.protocol.build_command(cmd_id)
        self.protocol.send_packet(packet)

    def set_light_state(self, light_id, on_off):
        """Set a light to ON or OFF."""
        cmd_id = 0x02  # hypothetical 'SET_LIGHT_STATE'
        payload = struct.pack("!IB", light_id, 1 if on_off else 0)
        packet = self.protocol.build_command(cmd_id, payload)
        self.protocol.send_packet(packet)

    def get_light_state(self, light_id):
        """Return last known state from internal cache."""
        return self.lights.get(light_id, {}).get("state")

    def update_light_state(self, light_id):
        """Ask TPI for an immediate update of a single light."""
        cmd_id = 0x03  # hypothetical 'QUERY_LIGHT_STATE'
        payload = struct.pack("!I", light_id)
        packet = self.protocol.build_command(cmd_id, payload)
        self.protocol.send_packet(packet)
