import asyncio

from zyxel import ZyXEL

from dotenv import load_dotenv

import os

# ----------------------------------------------------------------------------------------------------------------------
#
# MAIN - To be used for tests only!
#
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Load the .env file
    load_dotenv()

    params = {
        "username": os.getenv("USER"),
        "password": os.getenv("PASS"),
        "ip_address": os.getenv("ADDR")
    }

    # ------------------------------------------------------------------------------------------------------------------
    # ZyXEL LTE5398 M904
    # ------------------------------------------------------------------------------------------------------------------

    zyxel = ZyXEL(
        params=params
    )

    asyncio.run(zyxel.async_update_cell_status_data())


