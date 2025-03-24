#!/usr/bin/env python3
# zen_interface.py
#
# High-level TPI interface. Now includes the subscription step from the old code.

import struct
import colorama
from colorama import Fore, Style
from zen import ZenProtocol

colorama.init()

class ZenInterface:
    def __init__(self, host, port, mac=None, debug=False):
        self.protocol = ZenProtocol(host, port, mac=mac, debug=debug)
        self.debug = debug

        self.lights = {}
        self.groups = {}
        self.scenes = {}

        # Set the callback to handle incoming data
        self.protocol.set_recv_callback(self.handle_incoming)
        # Connect (which does basic handshake)
        self.protocol.connect()

        # **NEW**: replicate old code's subscription step
        self.subscribe_controller_events()

    def close(self):
        self.protocol.close()

    def handle_incoming(self, data):
        if self.debug:
            print(Fore.CYAN + f"[ZenInterface] Incoming data: {data}" + Style.RESET_ALL)
        # Parse TPI data, update self.lights, etc.

    def subscribe_controller_events(self):
        """
        The old code used a 'subscribe' command after connecting.
        For example, command ID 0x91, or something similar, with a payload
        that tells the controller to enable advanced event notifications.
        """
        sub_cmd_id = 0x91  # Hypothetical 'SUBSCRIBE_EVENTS' command
        payload = b"\x01"  # Some subscription flag, depending on old code
        packet = self.protocol.build_command(sub_cmd_id, payload)
        self.protocol.send_packet(packet)

        if self.debug:
            print(Fore.MAGENTA + "[ZenInterface] Subscribed to controller events" + Style.RESET_ALL)

    def refresh_all_devices(self):
        cmd_id = 0x01  # hypothetical 'QUERY_ALL_DEVICES'
        packet = self.protocol.build_command(cmd_id)
        self.protocol.send_packet(packet)

    def set_light_state(self, light_id, on_off):
        cmd_id = 0x02  # hypothetical 'SET_LIGHT_STATE'
        payload = struct.pack("!IB", light_id, 1 if on_off else 0)
        packet = self.protocol.build_command(cmd_id, payload)
        self.protocol.send_packet(packet)

    def get_light_state(self, light_id):
        return self.lights.get(light_id, {}).get("state")

    def update_light_state(self, light_id):
        cmd_id = 0x03  # hypothetical 'QUERY_LIGHT_STATE'
        payload = struct.pack("!I", light_id)
        packet = self.protocol.build_command(cmd_id, payload)
        self.protocol.send_packet(packet)
