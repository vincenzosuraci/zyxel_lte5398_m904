import logging
from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass, SensorEntity
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorDeviceClass
from .const import *
from .coordinator import ZyxelCoordinator

_LOGGER = logging.getLogger(__name__)


class ZyxelSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator: ZyxelCoordinator, device_info: DeviceInfo, description: SensorEntityDescription):
        """Inizializza il sensore."""
        super().__init__(coordinator)

        self._description = description
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_suggested_display_precision = description.suggested_display_precision
        self._attr_name = description.name
        self._attr_unique_id = f"{device_info["name"]}_{description.key}"
        self._attr_icon = description.icon
        self._attr_unit_of_measurement = description.unit_of_measurement
        self._attr_device_info = device_info

    @property
    def state(self):
        """Ritorna lo stato attuale del sensore."""
        return self.coordinator.data.get(self._description.name)

    @property
    def available(self):
        """Controlla se il sensore è disponibile."""
        return self.coordinator.last_update_success

    async def async_update(self):
        """Aggiorna manualmente lo stato del sensore."""
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """Iscrive il sensore al coordinatore per gli aggiornamenti."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


async def get_sensors(coordinator: ZyxelCoordinator, device_info: DeviceInfo):

    sensors = []

    data = await coordinator.zyxel_device.fetch_data()

    if data is not None:

        if ZYXEL_SENSOR_LAST_SMS in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_LAST_SMS).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_LAST_SMS,
                icon="mdi:message-text-outline",
            )))
        if ZYXEL_SENSOR_RSRP in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_RSRP).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_RSRP,
                icon="mdi:signal",
                unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
                suggested_display_precision=0,
                device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                state_class=SensorStateClass.MEASUREMENT
            )))
        if ZYXEL_SENSOR_RSRQ in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_RSRQ).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_RSRQ,
                icon="mdi:signal",
                suggested_display_precision=0,
                unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
                device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                state_class=SensorStateClass.MEASUREMENT
            )))
        if ZYXEL_SENSOR_SINR in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_SINR).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_SINR,
                icon="mdi:signal",
                suggested_display_precision=0,
                unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
                device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                state_class=SensorStateClass.MEASUREMENT
            )))
        if ZYXEL_SENSOR_ACCESS_TECH in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_ACCESS_TECH).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_ACCESS_TECH,
                icon="mdi:radio-tower"
            )))
        if ZYXEL_SENSOR_CELL_ID in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_CELL_ID).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_CELL_ID,
                icon="mdi:radio-tower"
            )))
        if ZYXEL_SENSOR_PHY_CELL_ID in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_PHY_CELL_ID).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_PHY_CELL_ID,
                icon="mdi:radio-tower"
            )))
        if ZYXEL_SENSOR_ENB in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_ENB).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_ENB,
                icon="mdi:radio-tower"
            )))
        if ZYXEL_SENSOR_MAIN_BAND in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_MAIN_BAND).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_MAIN_BAND,
                icon="mdi:radio-tower"
            )))
        if ZYXEL_SENSOR_CA_BANDS in data:
            sensors.append(ZyxelSensor(coordinator, device_info, SensorEntityDescription(
                key=str(ZYXEL_SENSOR_CA_BANDS).lower().replace(" ", "_"),
                name=ZYXEL_SENSOR_CA_BANDS,
                icon="mdi:radio-tower"
            )))

    return sensors


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configura i sensori da una config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    zyxel_device = coordinator.zyxel_device

    device_manufacturer = DEVICE_MANUFACTURER
    device_name = await zyxel_device.get_name()
    device_model = await zyxel_device.get_model()
    device_sw_version = await zyxel_device.get_sw_version()
    device_id = await zyxel_device.get_id()

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, device_id)},  # Usa un identificativo unico per il router
        manufacturer=device_manufacturer,
        model=device_model,
        name=device_name,
        sw_version=device_sw_version,
    )

    device_info = DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=device_name,
        manufacturer=device_manufacturer,
        model=device_model,  # Modello del modem (aggiorna con il modello corretto)
        sw_version=device_sw_version # Versione del software, può essere dinamico se riesci a recuperarlo dal modem
    )

    sensors = await get_sensors(coordinator, device_info)

    async_add_entities(sensors)

