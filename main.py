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

    stand_alone = False

    if stand_alone:

        from zyxel_lte5398_m904_stand_alone import ZyXEL_LTE5398_M904_Crawler
        zyxel = ZyXEL_LTE5398_M904_Crawler(
            params=params
        )

        # zyxel.update_cell_status_data()

        zyxel.reboot()

    else:

        from custom_components.zyxel_lte5398_m904.zyxel import Zyxel
        zyxel = Zyxel(
            params=params
        )

        import asyncio
        asyncio.run(zyxel.reboot())

        #import time
        #time.sleep(5)
        #asyncio.run(zyxel.fetch_data())






