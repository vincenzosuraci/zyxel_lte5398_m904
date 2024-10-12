from .zyxel import ZyXEL


import logging
_LOGGER = logging.getLogger(__name__)


class ZyXEL_HomeAssistant(ZyXEL):
    def debug(self, msg):
        _LOGGER.debug(msg)

    def info(self, msg):
        _LOGGER.info(msg)

    def error(self, msg):
        _LOGGER.error(msg)
