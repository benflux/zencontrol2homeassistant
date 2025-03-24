import time
from zencontrol.controller import ZenControl
from mqtt.broker import MQTTBroker
from polling.poller import DevicePoller
import yaml

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()

    # Initialize Zencontrol interface for all devices
    zencontrols = []
    for device in config['zencontrol']:
        zencontrol = ZenControl(device)
        zencontrols.append(zencontrol)

    # Initialize MQTT broker
    mqtt_broker = MQTTBroker(config['mqtt'], zencontrols)
    
    # Start MQTT communication
    mqtt_broker.start()

    # Start periodic polling for each Zencontrol device
    device_pollers = []
    for zencontrol in zencontrols:
        device_poller = DevicePoller(zencontrol, mqtt_broker, config['polling_interval'])
        device_pollers.append(device_poller)
        device_poller.start()

    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        mqtt_broker.stop()
        for poller in device_pollers:
            poller.stop()

if __name__ == "__main__":
    main()
