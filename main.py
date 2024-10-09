from zyxel import ZyXEL_LTE5398_M904_Crawler

from dotenv import load_dotenv

import os

# ----------------------------------------------------------------------------------------------------------------------
#
# MAIN
#
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Carica il file .env
    load_dotenv()

    params = {
        "ip_address": os.getenv("IP_ADDRESS"),
        "content": os.getenv("CONTENT"),
        "key": os.getenv("KEY"),
        "iv": os.getenv("IV"),
        "aes_key": os.getenv("AES_KEY"),
        "dynamic": False
    }

    # ------------------------------------------------------------------------------------------------------------------
    # ZyXEL LTE5398 M904
    # ------------------------------------------------------------------------------------------------------------------

    zyxel = ZyXEL_LTE5398_M904_Crawler(
        params=params
    )

    zyxel.update_cell_status_data()
    # zyxel.test_aes_rsa_encrypt()


