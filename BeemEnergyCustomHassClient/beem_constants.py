# API Configuration
BASE_URL = "https://api-x.beem.energy/beemapp"
LOGIN_ENDPOINT = "/user/login"
SUMMARY_ENDPOINT = "/box/summary"

# MQTT Configuration
MQTT_BASE_TOPIC = "homeassistant"
MQTT_DISCOVERY_PREFIX = "homeassistant"
MQTT_DEVICE_CLASS = "energy"
MQTT_STATE_CLASS = "measurement"

# Device Information
DEVICE_MANUFACTURER = "Beem Energy"
DEVICE_MODEL = "Solar Panel"
DEVICE_SOFTWARE_VERSION = "1.0"

# Logging Configuration
DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = 'INFO'

# Default Configuration Values
DEFAULT_START_DELAY = 0
DEFAULT_REFRESH_INTERVAL = 1  # minutes
