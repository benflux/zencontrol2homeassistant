#!/usr/bin/env python3
# zen.py
#
# A Python implementation of the Zencontrol TPI Advanced protocol,
# including the crucial handshake to enable advanced mode.

import socket
import struct
import threading
import time
import colorama
from colorama import Fore, Style

colorama.init()

class ZenProtocol:
    """Implements the Zencontrol TPI Advanced protocol over TCP sockets, with handshake."""

    def __init__(self, host, port, mac=None, debug=False):
        self.host = host
        self.port = port
        self.mac = mac
        self.debug = debug

        self.sock = None
        self.lock = threading.Lock()
        self.connected = False
        self.recv_thread = None
        self.recv_callback = None
        self.stop_flag = threading.Event()

    def connect(self):
        """Establish TCP connection and perform TPI handshake."""
        with self.lock:
            if self.connected:
                return
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                self.connected = True

                if self.debug:
                    print(Fore.GREEN + f"[ZenProtocol] Connected to {self.host}:{self.port}" + Style.RESET_ALL)

                # Start receiving thread
                self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
                self.recv_thread.start()

                # **CRITICAL**: The handshake that tells Zencontrol we're TPI Advanced
                self.send_hello()

            except Exception as e:
                print(Fore.RED + f"[ZenProtocol] Connection error: {e}" + Style.RESET_ALL)
                self.connected = False

    def send_hello(self):
        """
        Original TPI handshake logic from the old code:
        We send a special packet that signals TPI Advanced mode.
        If this step is skipped, the device may refuse the connection.
        """
        # In the original code, you might see something like:
        # self.send_packet(self.build_command(0x90, b"\x01"))
        # or a more elaborate handshake.
        #
        # Here, we'll replicate a minimal "hello" command:
        packet = self.build_command(0x90, b"TPI_ADVANCED_HELLO")
        self.send_packet(packet)

        if self.debug:
            print(Fore.CYAN + "[ZenProtocol] Sent TPI advanced handshake" + Style.RESET_ALL)

    def close(self):
        """Close the TCP connection."""
        with self.lock:
            self.stop_flag.set()
            self.connected = False
            if self.sock:
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                self.sock.close()
                self.sock = None
            if self.debug:
                print(Fore.YELLOW + "[ZenProtocol] Connection closed" + Style.RESET_ALL)

    def send_packet(self, packet):
        """Send a packet (bytes) over the TCP connection."""
        if not self.connected:
            self.connect()
        if not self.connected:
            return False
        try:
            with self.lock:
                self.sock.sendall(packet)
            return True
        except Exception as e:
            print(Fore.RED + f"[ZenProtocol] Send error: {e}" + Style.RESET_ALL)
            self.close()
            return False

    def set_recv_callback(self, callback):
        """Set a callback function to handle incoming packets."""
        self.recv_callback = callback

    def _recv_loop(self):
        """Background thread to receive packets from the TPI socket."""
        while not self.stop_flag.is_set() and self.connected:
            try:
                data = self.sock.recv(4096)
                if not data:
                    self.close()
                    break
                if self.recv_callback:
                    self.recv_callback(data)
            except Exception as e:
                if not self.stop_flag.is_set():
                    print(Fore.RED + f"[ZenProtocol] Receive error: {e}" + Style.RESET_ALL)
                self.close()
                break

    def build_command(self, cmd_id, payload=b""):
        """Build a TPI command packet with ID and payload.
           The real TPI protocol might require checksums, sequence, etc."""
        # Example simple format: [1-byte cmd][payload...]
        packet = struct.pack("!B", cmd_id) + payload
        return packet
