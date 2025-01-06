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

    from custom_components.zyxel_lte5398_m904.zyxel import Zyxel
    zyxel = Zyxel(
        params=params
    )

    import asyncio
    #asyncio.run(zyxel.reboot())
    asyncio.run(zyxel.retrieve_sms_messages())

    #import time
    #time.sleep(5)
    #asyncio.run(zyxel.fetch_data())






