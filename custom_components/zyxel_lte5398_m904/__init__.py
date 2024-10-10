import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import discovery
from .const import SENSOR, DOMAIN, MANUFACTURER, CONF_IP_ADDRESS, CONF_MODEL, CONF_NAME, CONF_SW_VERSION

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Legacy setup, richiesto solo per il supporto del file configuration.yaml."""
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the ZyXEL Modem component from a config entry."""
    hass.data[DOMAIN] = config_entry.data

    manufacturer = MANUFACTURER
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    model = config_entry.data.get(CONF_MODEL)
    name = config_entry.data.get(CONF_NAME)
    sw_version = config_entry.data.get(CONF_SW_VERSION)

    # Registra il dispositivo ZyXEL nel device registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, ip_address)},  # Identificatore unico per il dispositivo
        manufacturer=manufacturer,
        name=name,
        model=model,
        sw_version=sw_version
    )

    # Scopri e configura le entità del sensore
    hass.async_create_task(
        discovery.async_load_platform(hass, SENSOR, DOMAIN, {}, config_entry)
    )

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Rimuove un config entry."""
    return True