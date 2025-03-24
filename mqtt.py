#!/usr/bin/env python3
# mqtt.py
#
# Main script to connect ZenInterface with MQTT (Home Assistant).
# Now includes a polling thread for periodic state refresh.

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
    """Bridges ZenInterface with Home Assistant via MQTT."""

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

        # We'll hold a ZenInterface object for each controller
        self.interfaces = []

        # MQTT client
        self.mqtt_client = mqtt.Client()
        if self.mqtt_user and self.mqtt_pass:
            self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_pass)

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Polling thread references
        self.poll_threads = []
        self.stop_polling = threading.Event()

    def setup_controllers(self):
        """Initialize ZenInterface objects for each controller in config."""
        for ctrl in self.controllers:
            host = ctrl["host"]
            port = ctrl["port"]
            mac = ctrl.get("mac", None)
            name = ctrl.get("name", f"{host}:{port}")
            print(Fore.GREEN + f"Setting up ZenInterface for {name} ({host}:{port})" + Style.RESET_ALL)

            # Create ZenInterface
            interface = ZenInterface(host, port, mac=mac, debug=False)
            # Example: refresh all devices
            interface.refresh_all_devices()
            self.interfaces.append(interface)

    def start_mqtt(self):
        """Connect to the MQTT broker and start loop."""
        print(Fore.GREEN + f"Connecting to MQTT {self.mqtt_host}:{self.mqtt_port}" + Style.RESET_ALL)
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, self.keepalive)
        self.mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(Fore.GREEN + "[MQTT] Connected successfully." + Style.RESET_ALL)
        else:
            print(Fore.RED + f"[MQTT] Connection failed. RC={rc}" + Style.RESET_ALL)

        # Example: subscribe to some topics if needed
        # client.subscribe("some/topic/#")

    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        # Typically parse messages to control lights, etc.
        pass

    def publish_light_state(self, interface, light_id):
        """Publish a single light's state to MQTT."""
        state = interface.get_light_state(light_id)
        if state is None:
            return
        topic = f"{self.discovery_prefix}/zencontrol/{light_id}/state"
        self.mqtt_client.publish(topic, state)
        print(Fore.YELLOW + f"[MQTT] Published {state} for light {light_id}" + Style.RESET_ALL)

    def poll_loop(self, interface):
        """Loop that periodically polls the ZenInterface for updated states."""
        while not self.stop_polling.is_set():
            # Example: for each known light in interface.lights, request an update
            for light_id in interface.lights.keys():
                interface.update_light_state(light_id)
                time.sleep(0.1)  # small delay between queries

            # Give TPI some time to respond
            time.sleep(1.0)

            # Now publish each known light's state
            for light_id in list(interface.lights.keys()):
                self.publish_light_state(interface, light_id)

            # Wait poll_interval before next cycle
            time.sleep(self.poll_interval)

    def start_polling_thread(self):
        """Create and start a thread for each ZenInterface to poll device states."""
        for interface in self.interfaces:
            t = threading.Thread(target=self.poll_loop, args=(interface,), daemon=True)
            t.start()
            self.poll_threads.append(t)

    def stop_polling_threads(self):
        """Signal all polling threads to stop."""
        self.stop_polling.set()
        for t in self.poll_threads:
            t.join()

    def run(self):
        """Main entry to set up everything and run indefinitely."""
        self.setup_controllers()
        self.start_mqtt()
        self.start_polling_thread()

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
