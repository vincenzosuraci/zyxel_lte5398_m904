import logging
import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS
from homeassistant.components.sensor import SensorDeviceClass
from .const import *
from .zyxel_ha import ZyXEL_HomeAssistant

_LOGGER = logging.getLogger(__name__)

class ZyXEL_Sensor(SensorEntity):
    """Rappresenta un sensore di stato del modem ZyXEL."""

    def __init__(self,
        zyxel: ZyXEL_HomeAssistant,
        name: str,
        props = {}
    ):
        """Inizializza il sensore."""
        self._name = name
        self._zyxel = zyxel

        self._value = None
        self._device_class = props.get("device_class")
        self._last_reset = props.get("last_reset")
        self._native_unit_of_measurement = props.get("native_unit_of_measurement")
        self._native_value = props.get("native_value")
        self._options = props.get("options", [])
        self._state_class = props.get("state_class")
        self._suggested_display_precision = props.get("suggested_display_precision")
        self._suggested_unit_of_measurement = props.get("suggested_unit_of_measurement")
        self._icon = props.get("icon")

    @property
    def name(self):
        """Restituisce il nome del sensore."""
        return self._name

    @property
    def state(self):
        """Restituisce lo stato corrente del sensore."""
        return self._value

    @property
    def device_class(self):
        """Imposta il tipo di dispositivo (facoltativo)."""
        return self._device_class

    @property
    def last_reset(self):
        """Imposta il timestamp dell'ultimo reset (facoltativo)."""
        return self._last_reset

    @property
    def native_unit_of_measurement(self):
        """Imposta l'unità di misura nativa."""
        return self._native_unit_of_measurement

    @property
    def native_value(self):
        """Ritorna il valore attuale del sensore nel suo formato nativo."""
        return self._value

    @property
    def options(self):
        """Imposta le opzioni disponibili per il sensore (facoltativo)."""
        return self._options  # Opzioni personalizzate per il sensore

    @property
    def state_class(self):
        """Imposta la classe di stato del sensore."""
        return self._state_class

    @property
    def suggested_display_precision(self):
        """Suggerisce la precisione per la visualizzazione del valore del sensore (facoltativo)."""
        return self._suggested_display_precision

    @property
    def suggested_unit_of_measurement(self):
        """Suggerisce un'unità di misura personalizzata (facoltativo)."""
        return self._suggested_unit_of_measurement

    @property
    def icon(self):
        """Icona (facoltativo)."""
        return self._icon

    async def async_update(self):
        try:
            """Aggiorna lo stato del sensore con i dati del modem."""
            cell_status = await self._zyxel.async_get_cell_status()
            if cell_status is not None:
                if self._name == ZYXEL_SENSOR_RSRP:
                    self._value = int(cell_status["INTF_RSRP"])
                elif self._name == ZYXEL_SENSOR_RSRQ:
                    self._value = int(cell_status["INTF_RSRQ"])
                elif self._name == ZYXEL_SENSOR_SINR:
                    self._value = int(cell_status["INTF_SINR"])
                elif self._name == ZYXEL_SENSOR_ACCESS_TECH:
                    self._value = int(cell_status["INTF_Current_Access_Technology"])
                elif self._name == ZYXEL_SENSOR_CELL_ID:
                    self._value = int(cell_status["INTF_Cell_ID"])
                elif self._name == ZYXEL_SENSOR_ENB:
                    self._value = int(cell_status["INTF_Cell_ID"]) // 256
                elif self._name == ZYXEL_SENSOR_PHY_CELL_ID:
                    self._value = int(cell_status["INTF_PhyCell_ID"])
                elif self._name == ZYXEL_SENSOR_MAIN_BAND:
                    ul = 5 * (int(cell_status["INTF_Uplink_Bandwidth"]) - 1)
                    dl = 5 * (int(cell_status["INTF_Downlink_Bandwidth"]) - 1)
                    self._value = cell_status["INTF_Current_Band"] + "(" + str(dl) + "MHz/" + str(ul) + "MHz)"
                elif self._name == ZYXEL_SENSOR_CA_BANDS:
                    CA_Bands = []
                    for scc in cell_status["SCC_Info"]:
                        if scc["Enable"]:
                            CA_Bands.append(scc["Band"])
                    self._value = ' '.join(CA_Bands)
        except Exception as e:
            pass


async def get_sensors(zyxel: ZyXEL_HomeAssistant):

    sensors = []

    cell_status = await zyxel.async_get_cell_status()

    if cell_status is not None:

        if "INTF_RSRP" in cell_status:
            props = {
                "icon": "mdi:signal",
                "suggested_display_precision": 0,
                "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
                "native_unit_of_measurement": SIGNAL_STRENGTH_DECIBELS
            }
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_RSRP, props))

        if "INTF_RSRQ" in cell_status:
            props = {
                "icon": "mdi:signal",
                "suggested_display_precision": 0,
                "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
                "native_unit_of_measurement": SIGNAL_STRENGTH_DECIBELS
            }
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_RSRQ, props))

        if "INTF_SINR" in cell_status:
            props = {
                "icon": "mdi:signal",
                "suggested_display_precision": 0,
                "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
                "native_unit_of_measurement": SIGNAL_STRENGTH_DECIBELS
            }
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_SINR, props))

        if "INTF_Current_Access_Technology" in cell_status:
            props = {
                "icon": "mdi:radio-tower",
            }
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_ACCESS_TECH, props))

        if "INTF_Cell_ID" in cell_status:
            props = {
                "icon": "mdi:radio-tower",
            }
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_ENB, props))
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_CELL_ID, props))

        if "INTF_PhyCell_ID" in cell_status:
            props = {
                "icon": "mdi:radio-tower",
            }
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_PHY_CELL_ID, props))

        if ("INTF_Uplink_Bandwidth" in cell_status
                and "INTF_Downlink_Bandwidth" in cell_status
                and "INTF_Current_Band" in cell_status):
            props = {
                "icon": "mdi:radio-tower",
            }
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_PHY_CELL_ID, props))

        if "SCC_Info" in cell_status:
            props = {
                "icon": "mdi:radio-tower",
            }
            sensors.append(ZyXEL_Sensor(zyxel, ZYXEL_SENSOR_CA_BANDS, props))

    return sensors

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):

    # Recupera l'entry di configurazione per il dominio
    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    # Creo l'oggetto ZyXEL
    zyxel = ZyXEL_HomeAssistant(params={
        "username": config_entry.data.get(CONF_USERNAME),
        "password": config_entry.data.get(CONF_PASSWORD),
        "ip_address": config_entry.data.get(CONF_IP_ADDRESS)
    })

    _LOGGER.debug(config_entry.data)

    # Recupero dei sensori in base ai dati dello ZyXEL
    sensors = await get_sensors(zyxel)

    _LOGGER.debug(sensors)

    async_add_entities(sensors)
