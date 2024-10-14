import logging
_LOGGER = logging.getLogger(__name__)

from .const import (
    SENSOR,
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

    from .zyxel_device import ZyxelDevice
    from .coordinator import ZyxelCoordinator

    async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:

        ip_address = config_entry.data[CONF_IP_ADDRESS]
        username = config_entry.data[CONF_USERNAME]
        password = config_entry.data[CONF_PASSWORD]

        zyxel = ZyxelDevice(params={
            "username": username,
            "password": password,
            "ip_address": ip_address
        })

        # Inizializza il coordinatore
        coordinator = ZyxelCoordinator(hass, zyxel)

        # Memorizza il coordinatore nel registro dei dati di Home Assistant
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][config_entry.entry_id] = coordinator

        # Esegui il primo aggiornamento
        await coordinator.async_config_entry_first_refresh()

        # Aggiungi i sensori
        hass.config_entries.async_setup_platforms(config_entry, [SENSOR])

        return True


    async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
        """Unload a config entry."""
        # Rimuove i sensori
        unload_ok = await hass.config_entries.async_unload_platforms(config_entry, [SENSOR])

        if unload_ok:
            hass.data[DOMAIN].pop(config_entry.entry_id)

        return unload_ok

except ModuleNotFoundError:
    print("Execution outside the Home Assistant environment")