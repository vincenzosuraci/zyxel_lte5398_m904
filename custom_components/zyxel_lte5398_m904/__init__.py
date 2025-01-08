import logging
_LOGGER = logging.getLogger(__name__)

from .const import (
    SENSOR,
    BUTTON,
    DOMAIN,
    DEVICE_MANUFACTURER,
    CONF_IP_ADDRESS,
    DEVICE_MODEL,
    DEVICE_NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEVICE_SW_VERSION
)

try:
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from .sensor import async_setup_entry as async_setup_sensors

    from .zyxel_device import ZyxelDevice
    from .coordinator import ZyxelCoordinator

    async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:

        ip_address = config_entry.data[CONF_IP_ADDRESS]
        username = config_entry.data[CONF_USERNAME]
        password = config_entry.data[CONF_PASSWORD]

        zyxel_device = ZyxelDevice(params={
            "username": username,
            "password": password,
            "ip_address": ip_address
        })

        # Inizializza il coordinatore
        coordinator = ZyxelCoordinator(hass, zyxel_device)

        # Memorizza il coordinatore nel registro dei dati di Home Assistant
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

        # Esegui il primo aggiornamento
        await coordinator.async_config_entry_first_refresh()

        # Utilizza `async_forward_entry_setups` per configurare la piattaforma sensor e button
        await hass.config_entries.async_forward_entry_setups(config_entry, [SENSOR, BUTTON])

        return True


    async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
        await hass.config_entries.async_forward_entry_unload(config_entry, SENSOR)
        await hass.config_entries.async_forward_entry_unload(config_entry, BUTTON)
        hass.data[DOMAIN].pop(config_entry.entry_id)

        return True

except ModuleNotFoundError:
    print("Execution outside the Home Assistant environment")