import logging
_LOGGER = logging.getLogger(__name__)

from .const import SENSOR, DOMAIN, DEVICE_MANUFACTURER, CONF_IP_ADDRESS, DEVICE_MODEL, DEVICE_NAME, DEVICE_SW_VERSION

try:
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers.typing import ConfigType
    from homeassistant.helpers import discovery

    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        # Legacy setup, required only for configuration.yaml file support
        return True


    async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:

        # Set up the ZyXEL component from a config entry
        hass.data[DOMAIN] = config_entry.data

        manufacturer = DEVICE_MANUFACTURER
        ip_address = config_entry.data[CONF_IP_ADDRESS]
        model = config_entry.data.get(DEVICE_MODEL)
        name = config_entry.data.get(DEVICE_NAME)
        sw_version = config_entry.data.get(DEVICE_SW_VERSION)

        # Register the ZyXEL device in the device registry
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, ip_address)},
            manufacturer=manufacturer,
            name=name,
            model=model,
            sw_version=sw_version
        )

        # Discover and configure the sensor entities
        hass.async_create_task(
            discovery.async_load_platform(hass, SENSOR, DOMAIN, {}, config_entry)
        )

        return True


    async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
        """Remove config entry."""
        return True

except ModuleNotFoundError:
    print("Execution outside the Home Assistant environment")