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

    # ------------------------------------------------------------------------------------------------------------------
    # Reboot
    # ------------------------------------------------------------------------------------------------------------------
    # asyncio.run(zyxel.reboot())

    # ------------------------------------------------------------------------------------------------------------------
    # SIM info
    # ------------------------------------------------------------------------------------------------------------------
    # time.sleep(5)
    #asyncio.run(zyxel.retrieve_sim_info())

    # ------------------------------------------------------------------------------------------------------------------
    # SMS info
    # ------------------------------------------------------------------------------------------------------------------
    #time.sleep(5)
    asyncio.run(zyxel.get_last_sms())

    # ------------------------------------------------------------------------------------------------------------------
    # Procedura di recupero degli SMS
    # ------------------------------------------------------------------------------------------------------------------
    # 1) PUT http://192.168.0.1/cgi-bin/DAL?oid=cellwan_wait_state in cui manda il payload
    # {"WAIT_STATE_SMS":"LOADING"}
    # ricevendo come risposta
    # {"result":"ZCFG_SUCCESS","ReplyMsg":"WAIT_STATE_SMS","ReplyMsgMultiLang":"","sessionkey":"6fWmCYM5kEZmJ3viw3P4eTJsZf41CgqxjdHJZjEaMrmliHrFy7xAO6TDaNsCRJXY"}
    # 2) PUT http://192.168.0.1/cgi-bin/DAL?oid=cellwan_sms in cui manda il payload ottenuto dalla lettura degli SMS
    # {"SMS_Enable":false,"SMS_UsedSpace":4,"SMS_TotalSpace":20,"SMS_Inbox":[ ... ],"SMS_InboxRetrieve":true}
    # Ricevendo come risposta:
    # {"result":"ZCFG_SUCCESS","ReplyMsg":"SMS_Enable","ReplyMsgMultiLang":"","sessionkey":"203F4cTuiodL9KtpoBICeY8oMffT4QnWEerye9SklTWlrdyFE45GQ3Us9Xc1DnN5"}
    # 3) Richiedere periodicamente un GET http://192.168.0.1/cgi-bin/DAL?oid=cellwan_wait_state
    # 3a) se la risposta è:
    # {"result":"ZCFG_SUCCESS","ReplyMsg":"WAIT_STATE_SMS","ReplyMsgMultiLang":"","Object":[{"WAIT_STATE_SMS":"LOADING"}]}
    # bisogna riprovare
    # 3b) se la risposta, invece, è:
    # {"result":"ZCFG_SUCCESS","ReplyMsg":"WAIT_STATE_SMS","ReplyMsgMultiLang":"","Object":[{"WAIT_STATE_SMS":"RESUME_SUCC"}]}
    # si possono caricare i messaggi
    #encrypted_data = "KChRDuHtWJfQDIiTv+Zo0WwjRzrO2+AcW\/U8owud1rR1u\/S0HVkvW\/a2RC7dIR9\/8QZAgoyKrpaG7uHsP7PxAVLiiOlPH39t6Zy\/cNV\/hfY82v\/m4rsn1pe2X\/n7eeGyEq3JeclxjTjRQTDgIRjQiDCvytKiufVQtF8xxWi8kydzygJs\/yryULr\/iflqa1QkaM+kxVPWtXXfCQBd6CFM9A=="
    #iv = "7Mc9\/XD4LYpvtayEqQ2V5aSsWCTNb61XauQRGBNPkP8="
    #aes_key = "CCOOZBueAZ3zv03A/zMWLoLf/xyfzp3EW/AKjaHCSMs="
    #res = zyxel.dxc(encrypted_data, aes_key, iv)
    #print(res)




