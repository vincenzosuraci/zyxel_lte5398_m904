import logging
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription, ButtonDeviceClass
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
        self._attr_name = description.name
        self._attr_unique_id = f"{device_info["name"]}_{description.key}"
        self._attr_icon = description.icon
        self._attr_device_info = device_info

    async def async_press(self):
        if self._attr_name == ZYXEL_BUTTON_REBOOT:
            await self.reboot()
        elif self._attr_name == ZYXEL_BUTTON_UPDATE_LAST_SMS:
            await self.update_last_sms()

    async def reboot(self):
        """Esegue l'azione di reboot."""
        notification_title = "Riavvio - " + DEVICE_MANUFACTURER
        notification_message = ""
        try:
            # Accedi al dispositivo tramite il coordinatore
            if await self.coordinator.zyxel_device.reboot():
                notification_message += "Reboot avviato con successo."
            else:
                notification_message += "Errore durante il reboot"
        except Exception as e:
            notification_message += f"Errore durante il reboot: {str(e)}"
        # Notifica l'utente
        self.hass.components.persistent_notification.create(
            notification_message, title=notification_title
        )

    async def update_last_sms(self):
        """Esegue l'azione di aggiornamento dell'ultimo SMS ricevuto."""
        notification_title = "Aggiornamento dell'ultimo SMS ricevuto - " + DEVICE_MANUFACTURER
        notification_message = ""
        try:
            last_sms = await self.coordinator.zyxel_device.get_last_sms()
            # Accedi al dispositivo tramite il coordinatore
            if last_sms is not None:
                notification_message += f"Ultimo SMS ricevuto aggiornato con successo: {str(last_sms.get('msg'))}"
            else:
                notification_message += "Errore durante l'aggiornamento dell'ultimo SMS ricevuto"
        except Exception as e:
            notification_message += f"Errore durante l'aggiornamento dell'ultimo SMS ricevuto: {str(e)}"
        # Notifica l'utente
        self.hass.components.persistent_notification.create(
            notification_message, title=notification_title
        )


async def get_buttons(coordinator: ZyxelCoordinator, device_info: DeviceInfo):
    buttons = []
    # Reboot button
    buttons.append(ZyxelButton(coordinator, device_info, ButtonEntityDescription(
        key=str(ZYXEL_BUTTON_REBOOT).lower().replace(" ", "_"),
        name=ZYXEL_BUTTON_REBOOT,
        icon="mdi:restart",
        device_class=ButtonDeviceClass.RESTART,
    )))
    # Update Last SMS button
    buttons.append(ZyxelButton(coordinator, device_info, ButtonEntityDescription(
        key=str(ZYXEL_BUTTON_UPDATE_LAST_SMS).lower().replace(" ", "_"),
        name=ZYXEL_BUTTON_UPDATE_LAST_SMS,
        icon="mdi:update",
        device_class=ButtonDeviceClass.UPDATE,
    )))
    return buttons


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
        manufacturer=device_name,
        model=device_model,  # Modello del modem (aggiorna con il modello corretto)
        sw_version=device_sw_version  # Versione del software, può essere dinamico se riesci a recuperarlo dal modem
    )

    buttons = await get_buttons(coordinator, device_info)

    async_add_entities(buttons)

