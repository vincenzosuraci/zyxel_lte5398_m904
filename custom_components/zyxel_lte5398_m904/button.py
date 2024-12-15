import logging
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *
from .coordinator import ZyxelCoordinator

_LOGGER = logging.getLogger(__name__)


class ZyxelButton(CoordinatorEntity, ButtonEntity):

    def __init__(self, coordinator: ZyxelCoordinator, device_info: DeviceInfo, description: ButtonEntityDescription):
        """Inizializza il sensore."""
        super().__init__(coordinator)

        self._description = description
        self._attr_device_class = description.device_class
        self._attr_suggested_display_precision = description.suggested_display_precision
        self._attr_name = description.name
        self._attr_unique_id = f"{device_info["name"]}_{description.key}"
        self._attr_icon = description.icon
        self._attr_device_info = device_info
        self._attr_icon = description.icon

    def press(self):
        """Esegue l'azione di reboot."""
        try:
            # Accedi al dispositivo tramite il coordinatore
            if self.coordinator.zyxel.reboot():


            # Notifica l'utente
            self.hass.components.persistent_notification.create(
                "Reboot avviato con successo.", title="Reboot Device"
            )
        except Exception as e:
            # Gestisci eventuali errori
            self.hass.components.persistent_notification.create(
                f"Errore durante il reboot: {e}", title="Errore Reboot"
            )


async def get_buttons(coordinator: ZyxelCoordinator, device_info: DeviceInfo):

    buttons = []

    # Reboot button
    buttons.append(ZyxelButton(coordinator, device_info, ButtonEntityDescription(
        key=str(ZYXEL_BUTTON_REBOOT).lower().replace(" ", "_"),
        name=ZYXEL_BUTTON_REBOOT,
        icon="mdi:restart",
        device_class="restart",
    )))

    return buttons


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configura i sensori da una config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    zyxel = coordinator.zyxel

    device_manufacturer = DEVICE_MANUFACTURER
    device_name = await zyxel.get_name()
    device_model = await zyxel.get_model()
    device_sw_version = await zyxel.get_sw_version()
    device_id = await zyxel.get_id()

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
        manufacturer=device_name,
        model=device_model,  # Modello del modem (aggiorna con il modello corretto)
        sw_version=device_sw_version,  # Versione del software, può essere dinamico se riesci a recuperarlo dal modem
        via_device=(DOMAIN, config_entry.entry_id),
    )

    buttons = await get_buttons(coordinator, device_info)

    async_add_entities(buttons)

