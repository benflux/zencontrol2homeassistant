#!/usr/bin/env python3
# zen.py
#
# Implements the Zencontrol TPI Advanced protocol over a raw TCP socket.

import socket
import struct
import threading
import time
import colorama
from colorama import Fore, Style

colorama.init()

class ZenProtocol:
    """Handles raw TPI Advanced comms, including a basic handshake."""

    def __init__(self, host, port, mac=None, debug=False):
        self.host = host
        self.port = port
        self.mac = mac
        self.debug = debug

        self.sock = None
        self.connected = False
        self.stop_flag = threading.Event()
        self.recv_thread = None
        self.recv_callback = None

        self.lock = threading.Lock()

    def connect(self):
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

                # Basic handshake to inform Zencontrol we're TPI Advanced
                self.send_hello()

            except Exception as e:
                print(Fore.RED + f"[ZenProtocol] Connection error: {e}" + Style.RESET_ALL)
                self.connected = False

    def send_hello(self):
        """Send an initial handshake command that the original code used."""
        # In the real original code, you might see a different command ID or payload.
        # If the old code had 'SUBSCRIBE' or 'LOGIN' commands, replicate them exactly here.
        packet = self.build_command(0x90, b"TPI_ADVANCED_HELLO")
        self.send_packet(packet)
        if self.debug:
            print(Fore.CYAN + "[ZenProtocol] Sent TPI advanced handshake" + Style.RESET_ALL)

    def close(self):
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
        self.recv_callback = callback

    def _recv_loop(self):
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
        # If your original code had a more complex format (checksums, etc.), replicate it here.
        packet = struct.pack("!B", cmd_id) + payload
        return packet
