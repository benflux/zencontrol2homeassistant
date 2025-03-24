import threading
import time
import logging

class DevicePoller(threading.Thread):
    def __init__(self, zencontrol, mqtt_broker, interval):
        super().__init__()
        self.zencontrol = zencontrol
        self.mqtt_broker = mqtt_broker
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            devices = self.zencontrol.get_devices()
            for device in devices:
                state = self.zencontrol.query_device_state(device['id'])
                if state is not None:
                    self.mqtt_broker.publish_state(device['id'], state)
            time.sleep(self.interval)

    def stop(self):
        self._stop_event.set()
