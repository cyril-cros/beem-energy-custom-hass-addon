import json
import logging
import os
import requests

from typing import Dict, Any

from beem_constants import (
    DEFAULT_START_DELAY,
    DEFAULT_REFRESH_INTERVAL
)

logger = logging.getLogger(__name__)


class BeemEnergyConfig:
    def __init__(self, config_path: str = "/data/options.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from options.json and supervisor MQTT info"""
        try:
            with open(self.config_path, 'r') as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found. Using empty configuration.")
            config = {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {self.config_path}")
            config = {}

        # Merge with MQTT info from supervisor
        mqtt_info = self._get_mqtt_info()
        config.update(mqtt_info)

        return config

    def _get_mqtt_info(self) -> Dict[str, str]:
        """Retrieve MQTT configuration from Home Assistant supervisor"""
        supervisor_token = os.environ.get('SUPERVISOR_TOKEN', '')
        if not supervisor_token:
            logger.error("SUPERVISOR_TOKEN not set")
            return {}

        try:
            response = requests.get(
                'http://supervisor/services/mqtt',
                headers={
                    'Authorization': f'Bearer {supervisor_token}',
                    'Content-Type': 'application/json'
                }
            )
            response.raise_for_status()
            mqtt_response = response.json()

            return {
                'mqtt_host': mqtt_response['data']['host'],
                'mqtt_port': mqtt_response['data']['port'],
                'mqtt_username': mqtt_response.get('data', {}).get('username', ''),
                'mqtt_password': mqtt_response.get('data', {}).get('password', '')
            }
        except Exception as e:
            logger.error(f"Failed to retrieve MQTT info: {e}")
            return {}

    def _validate_config(self):
        """Validate and set default values for configuration"""
        # Beem Energy credentials
        if not self.config.get('beem_email'):
            logger.error("Beem Energy email not provided")
        if not self.config.get('beem_password'):
            logger.error("Beem Energy password not provided")

        # MQTT configuration
        self.config.setdefault('mqtt_host', 'localhost')
        self.config.setdefault('mqtt_port', 1883)

        # Operational parameters
        self.config.setdefault('start_delayseconds', DEFAULT_START_DELAY)
        self.config.setdefault('refresh_interval', DEFAULT_REFRESH_INTERVAL)
        self.config.setdefault('debug', False)

    def get(self, key: str, default=None):
        """Retrieve a configuration value"""
        return self.config.get(key, default)

    def debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.config.get('debug', False)
