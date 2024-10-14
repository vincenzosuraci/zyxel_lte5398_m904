from .zyxel import Zyxel

from .const import *

import logging
_LOGGER = logging.getLogger(__name__)


class ZyxelDevice(Zyxel):
    def debug(self, msg):
        _LOGGER.debug(msg)

    def info(self, msg):
        _LOGGER.info(msg)

    def warning(self, msg):
        _LOGGER.warning(msg)

    def error(self, msg):
        _LOGGER.error(msg)

    async def get_name(self):
        model = await self.get_model()
        return f"{DEVICE_MANUFACTURER} {model}"

    async def get_title(self):
        name = await self.get_name()
        return f"{name} - {self.ip_address}"

    async def fetch_data(self):

        data = None

        raw_data = super().fetch_data()

        if raw_data is not None:

            data = {}

            if "INTF_RSRP" in raw_data:
                data[ZYXEL_SENSOR_RSRP] = int(raw_data.get("INTF_RSRP"))

            if "INTF_RSRQ" in raw_data:
                data[ZYXEL_SENSOR_RSRQ] = int(raw_data.get("INTF_RSRQ"))

            if "INTF_SINR" in raw_data:
                data[ZYXEL_SENSOR_SINR] = int(raw_data.get("INTF_SINR"))

            if "INTF_Current_Access_Technology" in raw_data:
                data[ZYXEL_SENSOR_ACCESS_TECH] = raw_data.get("INTF_Current_Access_Technology")

            if "INTF_Cell_ID" in raw_data:
                data[ZYXEL_SENSOR_CELL_ID] = int(raw_data.get("INTF_Cell_ID"))
                data[ZYXEL_SENSOR_ENB] = int(raw_data.get("INTF_Cell_ID")) // 256

            if "INTF_PhyCell_ID" in raw_data:
                data[ZYXEL_SENSOR_PHY_CELL_ID] = int(raw_data.get("INTF_PhyCell_ID"))

            if "INTF_Uplink_Bandwidth" in raw_data and "INTF_Downlink_Bandwidth" in raw_data and "INTF_Current_Band" in raw_data:
                ul = 5 * (int(raw_data["INTF_Uplink_Bandwidth"]) - 1)
                dl = 5 * (int(raw_data["INTF_Downlink_Bandwidth"]) - 1)
                data[ZYXEL_SENSOR_MAIN_BAND] = raw_data["INTF_Current_Band"] + "(" + str(dl) + "MHz/" + str(ul) + "MHz)"

            if "SCC_Info" in raw_data:
                CA_Bands = []
                for scc in raw_data["SCC_Info"]:
                    if scc["Enable"]:
                        CA_Bands.append(scc["Band"])
                data[ZYXEL_SENSOR_CA_BANDS] = ' '.join(CA_Bands)

        return data