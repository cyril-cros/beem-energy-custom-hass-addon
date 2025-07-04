import json
import logging
from typing import Dict, Any

import paho.mqtt.client as mqtt

from beem_constants import (
    MQTT_BASE_TOPIC,
    MQTT_DISCOVERY_PREFIX,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_SOFTWARE_VERSION
)

logger = logging.getLogger(__name__)


class MQTTHandler:
    def __init__(self, host: str, port: int, username: str = None, password: str = None):
        self.client = mqtt.Client(client_id="beem-energy-client")
        self.host = host
        self.port = port

        if username and password:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")

    def connect(self):
        try:
            self.client.connect(self.host, self.port)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")

    def publish_discovery_config(
            self,
            device_id: str,
            device_name: str,
            sensor_type: str,
            sensor_config: Dict[str, Any]
    ):
        """Publish Home Assistant discovery configuration for a sensor"""
        discovery_topic = f"{MQTT_DISCOVERY_PREFIX}/sensor/{device_id}/{sensor_type}/config"

        # Prepare device information
        device_info = {
            'identifiers': [device_id],
            'name': device_name,
            'manufacturer': DEVICE_MANUFACTURER,
            'model': DEVICE_MODEL,
            'sw_version': DEVICE_SOFTWARE_VERSION
        }

        # Merge device info into sensor configuration
        sensor_config['device'] = device_info

        try:
            self.client.publish(
                discovery_topic,
                json.dumps(sensor_config),
                retain=True
            )
            logger.debug(f"Published discovery config for {sensor_type}")
        except Exception as e:
            logger.error(f"Failed to publish discovery config: {e}")

    def publish_sensor_state(
            self,
            device_id: str,
            sensor_type: str,
            value: Any
    ):
        """Publish sensor state to MQTT"""
        state_topic = f"{MQTT_BASE_TOPIC}/sensor/{device_id}/{sensor_type}/state"

        try:
            self.client.publish(
                state_topic,
                str(value),
                retain=True
            )
            logger.debug(f"Published state for {sensor_type}: {value}")
        except Exception as e:
            logger.error(f"Failed to publish sensor state: {e}")

    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
