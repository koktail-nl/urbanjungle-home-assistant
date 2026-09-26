"""Constants for UrbanJungle Care integration."""

DOMAIN = "urbanjungle_care"

# Backend API
DEFAULT_API_URL = "https://api.urbanjungle.care"

# OAuth2. The integration is a public client: it runs in the user's home and cannot keep a
# secret, so it proves possession of the authorization code with PKCE instead. The paths are
# appended to the API URL, which keeps a development backend a matter of one setting.
OAUTH_CLIENT_ID = "home-assistant"
OAUTH_AUTHORIZE_PATH = "/oauth/auth"
OAUTH_TOKEN_PATH = "/oauth/token"

# What the integration asks for: read the account and its plants, read the devices and push
# the readings of its own sensors, and manage its own integration record. offline_access
# yields the refresh token that keeps the link alive without asking the user again.
OAUTH_SCOPES = [
    "offline_access",
    "profile:read",
    "plants:read",
    "devices:read",
    "devices:write",
    "metrics:write",
    "tasks:read",
    "integrations:read",
    "integrations:write",
]

# Integration registration (matches Homey's postIntegration payload)
INTEGRATION_TYPE = "homeassistant"
INTEGRATION_NAME = "Home Assistant"

# Config entry data keys
CONF_USER_ID = "user_id"
CONF_INTEGRATION_ID = "integration_id"
CONF_API_URL = "api_url"

# Sync intervals (mirrors Homey device.ts scheduleNextSync)
SYNC_INTERVAL_PREMIUM_MINUTES = 15
SYNC_INTERVAL_FREE_HOURS = 24

# Capability types (must match @urbanjungle.care/common-models CapabilityType)
CAP_TEMPERATURE = "temperature"
CAP_LUMINANCE = "luminance"
CAP_NUTRITION = "nutrition"
CAP_MOISTURE = "moisture"
CAP_BATTERY = "battery"

# Sensor metadata keyed by capability type
SENSOR_TYPES = {
    CAP_TEMPERATURE: {
        "name": "Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
    },
    CAP_MOISTURE: {
        "name": "Moisture",
        "unit": "%",
        "icon": "mdi:water-percent",
        "device_class": "moisture",
    },
    CAP_LUMINANCE: {
        "name": "Light",
        "unit": "lx",
        "icon": "mdi:brightness-5",
        "device_class": "illuminance",
    },
    CAP_NUTRITION: {
        "name": "Conductivity",
        "unit": "µS/cm",
        "icon": "mdi:flash",
        "device_class": None,
    },
    CAP_BATTERY: {
        "name": "Battery",
        "unit": "%",
        "icon": "mdi:battery",
        "device_class": "battery",
    },
}
