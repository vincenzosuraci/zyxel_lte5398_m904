from zyxel_lte5398_m904.zyxel import ZyXEL_LTE5398_M904_Crawler

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

    zyxel = ZyXEL_LTE5398_M904_Crawler(
        params=params
    )

    zyxel.update_cell_status_data()


