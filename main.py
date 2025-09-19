import json

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

    # Recuperiamo il sito (VETRALLA o ARIANO)
    site = os.getenv("SITE")

    params = {
        "username": os.getenv(f"USER_{site}"),
        "password": os.getenv(f"PASS_{site}"),
        "ip_address": os.getenv(f"ADDR_{site}")
    }

    from custom_components.zyxel_lte5398_m904.zyxel import Zyxel
    zyxel = Zyxel(
        params=params
    )

    import asyncio
    import time

    actions = [
        #"get_sim_info",
        #"get_sim_status",
        #"get_last_sms",
        "get_traffic_status",
        #"reboot",
    ]

    sleep = False

    for action in actions:

        if action == "get_sim_info":

            # ----------------------------------------------------------------------------------------------------------
            # SIM info
            # ----------------------------------------------------------------------------------------------------------
            if sleep:
                time.sleep(5)
            sleep = True
            sim_info = asyncio.run(zyxel.get_sim_info())

        elif action == "get_sim_status":

            # ----------------------------------------------------------------------------------------------------------
            # SIM status
            # ----------------------------------------------------------------------------------------------------------
            if sleep:
                time.sleep(5)
            sleep = True
            sim_status = asyncio.run(zyxel.get_sim_status())
            print(json.dumps(sim_status))

        elif action == "get_last_sms":

            # ----------------------------------------------------------------------------------------------------------
            # last SMS info
            # ----------------------------------------------------------------------------------------------------------
            if sleep:
                time.sleep(5)
            sleep = True
            last_sms = asyncio.run(zyxel.get_last_sms())

        elif action == "get_traffic_status":

            # ----------------------------------------------------------------------------------------------------------
            # Traffic Status info
            # ----------------------------------------------------------------------------------------------------------
            if sleep:
                time.sleep(5)
            sleep = True
            traffic_status = asyncio.run(zyxel.get_traffic_status())
            print(json.dumps(traffic_status))

        elif action == "reboot":

            # ----------------------------------------------------------------------------------------------------------
            # Reboot
            # ----------------------------------------------------------------------------------------------------------
            if sleep:
                time.sleep(5)
            sleep = True
            asyncio.run(zyxel.reboot())




