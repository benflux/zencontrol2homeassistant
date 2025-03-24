#!/usr/bin/env python3
# mqtt.py
#
# Main script bridging ZenInterface with Home Assistant via MQTT.
# Includes TPI advanced handshake & subscription from old code, plus polling.

import yaml
import time
import threading
import paho.mqtt.client as mqtt
import colorama
from colorama import Fore, Style
from zen_interface import ZenInterface

colorama.init()

def load_config(filename="config.yaml"):
    with open(filename, "r") as f:
        return yaml.safe_load(f)

class ZenMQTTBridge:
    def __init__(self, config):
        self.config = config
        self.mqtt_host = config["mqtt"]["host"]
        self.mqtt_port = config["mqtt"].get("port", 1883)
        self.mqtt_user = config["mqtt"].get("user", None)
        self.mqtt_pass = config["mqtt"].get("password", None)
        self.discovery_prefix = config["mqtt"].get("discovery_prefix", "homeassistant")
        self.keepalive = config["mqtt"].get("keepalive", 60)
        self.controllers = config["controllers"]
        self.poll_interval = config.get("poll_interval", 10)

        self.interfaces = []

        # NOTE: This uses MQTT callback API v1 (deprecated but still works).
        self.mqtt_client = mqtt.Client()
        if self.mqtt_user and self.mqtt_pass:
            self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_pass)

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.poll_threads = []
        self.stop_polling = threading.Event()

    def setup_controllers(self):
        for ctrl in self.controllers:
            host = ctrl["host"]
            port = ctrl["port"]
            mac = ctrl.get("mac", None)
            name = ctrl.get("name", f"{host}:{port}")

            print(Fore.GREEN + f"Setting up ZenInterface for {name} ({host}:{port})" + Style.RESET_ALL)
            interface = ZenInterface(host, port, mac=mac, debug=False)
            # We can do an initial refresh
            interface.refresh_all_devices()
            self.interfaces.append(interface)

    def start_mqtt(self):
        print(Fore.GREEN + f"Connecting to MQTT {self.mqtt_host}:{self.mqtt_port}" + Style.RESET_ALL)
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, self.keepalive)
        self.mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(Fore.GREEN + "[MQTT] Connected successfully." + Style.RESET_ALL)
        else:
            print(Fore.RED + f"[MQTT] Connection failed. RC={rc}" + Style.RESET_ALL)

    def on_message(self, client, userdata, msg):
        pass

    def publish_light_state(self, interface, light_id):
        state = interface.get_light_state(light_id)
        if state is None:
            return
        topic = f"{self.discovery_prefix}/zencontrol/{light_id}/state"
        self.mqtt_client.publish(topic, state)
        print(Fore.YELLOW + f"[MQTT] Published {state} for light {light_id}" + Style.RESET_ALL)

    def poll_loop(self, interface):
        """Periodically refresh devices and publish states."""
        while not self.stop_polling.is_set():
            interface.refresh_all_devices()
            time.sleep(1)

            # Publish each known light's state
            for light_id in list(interface.lights.keys()):
                self.publish_light_state(interface, light_id)

            time.sleep(self.poll_interval)

    def start_polling_threads(self):
        for interface in self.interfaces:
            t = threading.Thread(target=self.poll_loop, args=(interface,), daemon=True)
            t.start()
            self.poll_threads.append(t)

    def stop_polling_threads(self):
        self.stop_polling.set()
        for t in self.poll_threads:
            t.join()

    def run(self):
        self.setup_controllers()
        self.start_mqtt()
        self.start_polling_threads()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.stop_polling_threads()
            for interface in self.interfaces:
                interface.close()
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

if __name__ == "__main__":
    cfg = load_config("config.yaml")
    bridge = ZenMQTTBridge(cfg)
    bridge.run()
