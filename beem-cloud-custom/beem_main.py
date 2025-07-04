import logging
import time
from datetime import datetime

import requests

from beem_config import BeemEnergyConfig
from beem_mqtt import MQTTHandler
from beem_constants import BASE_URL, LOGIN_ENDPOINT, SUMMARY_ENDPOINT


class BeemEnergyAddon:
    def __init__(self, config: BeemEnergyConfig, mqtt_handler: MQTTHandler):
        self.config = config
        self.mqtt_handler = mqtt_handler
        self.access_token = None

        # Configure logging
        logging_level = logging.DEBUG if config.debug_mode() else logging.INFO
        logging.basicConfig(
            level=logging_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def login(self):
        """Authenticate with Beem Energy API"""
        login_data = {
            'email': self.config.get('beem_email'),
            'password': self.config.get('beem_password')
        }

        try:
            response = requests.post(
                BASE_URL + LOGIN_ENDPOINT,
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            login_response = response.json()

            self.access_token = login_response.get('accessToken')
            self.logger.info("Successfully logged in to Beem Energy")
            return True
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False

    def get_box_summary(self):
        """Retrieve box summary for current month"""
        if not self.access_token:
            self.logger.error("No access token available")
            return None

        now = datetime.now()
        summary_request = {
            'month': now.month,
            'year': now.year
        }

        try:
            response = requests.post(
                BASE_URL + SUMMARY_ENDPOINT,
                json=summary_request,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.access_token}'
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get box summary: {e}")
            return None

    def process_box_data(self, box_data):
        """Process and publish box data to MQTT"""
        if not box_data:
            return

        for box in box_data:
            device_id = f"beem_energy_{box['serialNumber'].lower()}"
            device_name = f"Beem Energy {box['name']}"

            # Define sensors to publish
            sensors = [
                {
                    'type': 'power',
                    'name': 'Current Power',
                    'unit': 'W',
                    'value': box['wattHour']
                },
                {
                    'type': 'energy_daily',
                    'name': 'Daily Energy',
                    'unit': 'Wh',
                    'value': box['totalDay']
                },
                {
                    'type': 'energy_month',
                    'name': 'Monthly Energy',
                    'unit': 'Wh',
                    'value': box['totalMonth']
                },
                {
                    'type': 'signal_strength',
                    'name': 'Signal Strength',
                    'unit': 'dBm',
                    'value': box['lastDbm']
                }
            ]

            # Publish each sensor
            for sensor in sensors:
                # Prepare discovery config
                discovery_config = {
                    'name': sensor['name'],
                    'unique_id': f"{device_id}_{sensor['type']}",
                    'state_topic': f"homeassistant/sensor/{device_id}/{sensor['type']}/state",
                    'unit_of_measurement': sensor['unit']
                }

                # Publish discovery config and state
                self.mqtt_handler.publish_discovery_config(
                    device_id, device_name,
                    sensor['type'], discovery_config
                )
                self.mqtt_handler.publish_sensor_state(
                    device_id, sensor['type'], sensor['value']
                )

    def run(self):
        """Main execution method for the Beem Energy addon"""
        # Wait for start delay
        start_delay = self.config.get('start_delayseconds', 0)
        if start_delay > 0:
            self.logger.info(f"Waiting {start_delay} seconds before starting")
            time.sleep(start_delay)

        # Authenticate
        if not self.login():
            self.logger.error("Authentication failed. Exiting.")
            return

        # Setup MQTT connection
        self.mqtt_handler.connect()

        # Fetch and process data periodically
        refresh_interval = self.config.get('refresh_interval', 1)
        try:
            while True:
                box_summary = self.get_box_summary()
                if box_summary:
                    self.process_box_data(box_summary)
                time.sleep(refresh_interval * 60)
        except KeyboardInterrupt:
            self.logger.info("Addon stopped by user")
        finally:
            self.mqtt_handler.disconnect()


def main():
    config = BeemEnergyConfig()
    mqtt_handler = MQTTHandler(
        host=config.get('mqtt_host'),
        port=config.get('mqtt_port'),
        username=config.get('mqtt_username'),
        password=config.get('mqtt_password')
    )
    addon = BeemEnergyAddon(config, mqtt_handler)
    addon.run()


if __name__ == "__main__":
    main()
