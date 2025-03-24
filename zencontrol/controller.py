import requests
import logging

class ZenControl:
    def __init__(self, config):
        self.id = config['id']
        self.name = config['name']
        self.label = config['label']
        self.mac = config['mac']
        self.host = config['host']
        self.port = config['port']
        self.base_url = f"http://{self.host}:{self.port}/api"
        self.auth_token = config.get('auth_token', '')
    
    def get_devices(self):
        try:
            response = requests.get(f"{self.base_url}/devices", headers={"Authorization": f"Bearer {self.auth_token}"})
            response.raise_for_status()
            return response.json()  # Assume the response is a list of devices
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch devices: {e}")
            return []
    
    def query_device_state(self, device_id):
        try:
            response = requests.get(f"{self.base_url}/devices/{device_id}/state", headers={"Authorization": f"Bearer {self.auth_token}"})
            response.raise_for_status()
            return response.json()['state']
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to query device state: {e}")
            return None
