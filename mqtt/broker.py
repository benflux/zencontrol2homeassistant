import paho.mqtt.client as mqtt
import logging

class MQTTBroker:
    def __init__(self, config, zencontrols):
        self.host = config['host']
        self.port = config.get('port', 1883)
        self.discovery_prefix = config.get('discovery_prefix', "homeassistant")
        self.client = mqtt.Client()
        self.zencontrols = zencontrols
    
    def start(self):
        self.client.connect(self.host, self.port, 60)
        self.client.loop_start()
    
    def stop(self):
        self.client.loop_stop()
    
    def publish_state(self, device_id, state):
        topic = f"{self.discovery_prefix}/zencontrol/{device_id}/state"
        self.client.publish(topic, state)
        logging.info(f"Published state {state} for device {device_id}")
    
    def handle_device_state_change(self, device_id):
        state = None
        for zencontrol in self.zencontrols:
            if zencontrol.id == device_id:
                state = zencontrol.query_device_state(device_id)
                break
        if state is not None:
            self.publish_state(device_id, state)
