import logging
import requests
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN, CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

class ZyXEL_Sensor(SensorEntity):
    """Rappresenta un sensore di stato del modem ZyXEL."""

    def __init__(self, name: str, endpoint: str, config: dict):
        """Inizializza il sensore."""
        self._name = name
        self._state = None
        self._endpoint = endpoint
        self._ip_address = config[CONF_IP_ADDRESS]
        self._username = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]

    @property
    def name(self):
        """Restituisce il nome del sensore."""
        return self._name

    @property
    def state(self):
        """Restituisce lo stato corrente del sensore."""
        return self._state

    def update(self):
        """Aggiorna lo stato del sensore con i dati del modem."""
        try:
            response = requests.get(
                f"http://{self._ip_address}{self._endpoint}",
                auth=(self._username, self._password),
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self._state = data['value']
            else:
                _LOGGER.error("Errore nel recupero dei dati dal modem ZyXEL")
        except requests.RequestException as error:
            _LOGGER.error(f"Errore di connessione al modem: {error}")

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Imposta i sensori ZyXEL per l'integrazione."""
    config = hass.data[DOMAIN]

    sensors = [
        ZyXELModemSensor("ZyXEL Connection Status", "/status", config),
        ZyXELModemSensor("ZyXEL Download Speed", "/download_speed", config),
        ZyXELModemSensor("ZyXEL Upload Speed", "/upload_speed", config),
    ]
    async_add_entities(sensors)