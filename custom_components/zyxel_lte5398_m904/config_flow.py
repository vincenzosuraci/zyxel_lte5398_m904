import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD, CONF_MODEL, CONF_SW_VERSION, CONF_NAME, MANUFACTURER
from .zyxel import ZyXEL

class ZyXEL_LTE5398_M904_ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il flusso di configurazione per il modem ZyXEL."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Primo passo: richiedi l'indirizzo IP, username e password."""
        errors = {}

        if user_input is not None:
            # Verifica se l'input è valido (opzionale: potresti fare un controllo sulla connessione qui)
            ip_address = user_input[CONF_IP_ADDRESS]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            if ip_address and username and password:

                params = {
                    "username": username,
                    "password": password,
                    "ip_address": ip_address
                }

                zyxel = ZyXEL(
                    params=params
                )

                # Prova a ottenere il modello del modem ZyXEL dinamicamente
                try:

                    model = zyxel.model
                    name = f"{MANUFACTURER} {model}"
                    title = name

                    user_input[CONF_MODEL] = model
                    user_input[CONF_SW_VERSION] = zyxel.sw_version
                    user_input[CONF_NAME] = name

                    return self.async_create_entry(
                        title=title,
                        data=user_input
                    )

                except Exception:
                    errors["base"] = "cannot_connect"

            else:
                errors["base"] = "missing_input"

        # Se non ci sono input o ci sono errori, mostra il form
        data_schema = vol.Schema({
            vol.Required(CONF_IP_ADDRESS): cv.string,
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ZyXEL_LTE5398_M904_OptionsFlow(config_entry)

class ZyXEL_LTE5398_M904_OptionsFlow(config_entries.OptionsFlow):
    """Gestione delle opzioni aggiuntive per ZyXEL Modem."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Gestisci le opzioni aggiuntive."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Mostra il form delle opzioni."""
        data_schema = vol.Schema({
            vol.Optional(CONF_IP_ADDRESS, default=self.config_entry.data.get(CONF_IP_ADDRESS)): cv.string,
            vol.Optional(CONF_USERNAME, default=self.config_entry.data.get(CONF_USERNAME)): cv.string,
            vol.Optional(CONF_PASSWORD, default=self.config_entry.data.get(CONF_PASSWORD)): cv.string,
        })

        if user_input is not None:
            self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
            return self.async_create_entry(title="", data=None)

        return self.async_show_form(step_id="user", data_schema=data_schema)