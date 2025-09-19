import asyncio
import aiohttp
import async_timeout
import base64
import os
import time
import json as JSON
from datetime import datetime
from urllib.parse import quote

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.Util.Padding import pad, unpad

# ----------------------------------------------------------------------------------------------------------------------
#
# ZyXEL LTE5398-M904
#
# ----------------------------------------------------------------------------------------------------------------------

class Zyxel:

    # Massimo numero di prove di login
    MAX_NUM_RETRIES = 1

    # Minimo tempo che deve trascorre tra due interrogazioni successive al router
    MIN_INTERVAL_S = 2

    # Zyxel Config Success Message
    ZCFG_SUCCESS = "ZCFG_SUCCESS"

    def __init__(
        self,
        params = {}
    ):
        self._ip_address = params.get("ip_address", None)
        self._username = params.get("username", None)
        self._password = params.get("password", None)

        self._aes_key = None

        self._BasicInformation = None
        self._RSAPublicKey = None
        self._UserLogin = None
        self._cellwan_status = None
        self._traffic_status = None
        self._cellwan_sim = None
        self._cellwan_sms = None
        self._cellwan_status_timestamp = None
        self._sessionkey = None

        self._sms_by_YmdHMS = {}
        self._last_parsed_sms = None

        self._bytes_time = None
        self._bytes_sent = None
        self._bytes_received = None

        self._cookies = None

    @property
    def ip_address(self):
        return self._ip_address

    def debug(self, msg):
        print(msg)

    def info(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

    async def get_model(self):
        basic_information = await self._get_basic_information()
        return basic_information.get("ModelName")

    async def get_sw_version(self):
        basic_information = await self._get_basic_information()
        return basic_information.get("SoftwareVersion")

    async def fetch_data(self):
        # Recupero dei dati sulle celle
        data = await self._get_cellwan_status()
        # Recupero dei dati sul traffico
        down_up_load_speed = await self._get_down_up_load_speed()
        data["DOWNLOAD_SPEED"] = down_up_load_speed.get("download_speed")
        data["UPLOAD_SPEED"] = down_up_load_speed.get("upload_speed")
        # Recupero dei dati sull'ultimo SMS
        if self._last_parsed_sms is None:
            data["LAST_SMS_MSG"] = None
        else:
            data["LAST_SMS_MSG"] = self._last_parsed_sms.get('msg')
        return data

    async def test_connection(self):
        data = await self.fetch_data()
        return data is not None

    # ------------------------------------------------------------------------------------------------------------------
    #
    # Retrieve (SMS) Messages
    #
    # ------------------------------------------------------------------------------------------------------------------

    async def get_sim_info(self):
        return await self._get_cellwan_sim()

    async def get_sim_status(self):
        return await self._get_cellwan_status()

    async def get_traffic_status(self):
        return await self._get_traffic_status()

    async def get_sms_messages(self):
        await self._get_cellwan_sms()

    async def get_last_sms(self):
        if await self._put_cellwan_wait_state():
            if await self._put_cellwan_sms():
                while not await self._get_cellwan_wait_state():
                    await asyncio.sleep(3)
                await self._get_cellwan_sms()
                last_sms = await self._delete_all_sms_but_last()
                self._last_parsed_sms = await self._parse_sms(last_sms)
        return self._last_parsed_sms["msg"]

    # ------------------------------------------------------------------------------------------------------------------
    #
    # Reboot
    #
    # ------------------------------------------------------------------------------------------------------------------

    async def reboot(self):
        if await self._get_user_login() is not None:
            url = "http://" + self.ip_address + "/cgi-bin/Reboot"
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                'CSRFToken': self._sessionkey,
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Host': self.ip_address,
                'If-Modified-Since': 'Thu, 01 Jun 1970 00:00:00 GMT',
                'Origin': 'http://' + self.ip_address,
                'Pragma': 'no-cache',
                'Referer': 'http://' + self.ip_address + '/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }
            try:
                async with async_timeout.timeout(10):  # Timeout di 10 secondi
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, headers=headers, cookies=self._cookies) as response:
                            zyxel_json =  await response.json()

                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                reboot_result = decoded_zyxel_json.get("result")
                                if reboot_result == self.ZCFG_SUCCESS:
                                    return True
                            else:
                                msg = f"Request error {url}: {response.status}"
                                code = 502
                                raise ZyxelError(msg, code)
            except aiohttp.ClientError as err:
                msg = f"Connection error {url}: {err}"
                code = 501
                raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 500
                raise ZyxelError(msg, code)
        return False

    # ------------------------------------------------------------------------------------------------------------------
    #
    # Delete SMS
    #
    # ------------------------------------------------------------------------------------------------------------------

    async def delete_sms(self, ObjIndex=None):

        deleted = False

        if ObjIndex is not None and await self._get_user_login() is not None:

            url = "http://" + self._ip_address + "/cgi-bin/DAL?oid=cellwan_sms&objIndex=" + quote(ObjIndex)
            headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": 'keep-alive',
                "CSRFToken": self._sessionkey,
                "Host": self._ip_address,
                "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT",
                "Referer": "http://" + self._ip_address + "/Broadband",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }

            try:
                async with async_timeout.timeout(30):  # Timeout di 30 secondi
                    async with aiohttp.ClientSession() as session:
                        async with session.delete(url, headers=headers, cookies=self._cookies) as response:
                            self.debug(await response.text())                            
                            zyxel_json =  await response.json()                            
                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                if decoded_zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                    deleted = True
                                else:
                                    msg = 'Cell WAN Delete SMS (' + url + ') error: ' + str(zyxel_json)
                                    code = 803
                                    raise ZyxelError(msg, code)
                            else:
                                msg = f"Request error {url}: {response.status}"
                                code = 802
                                raise ZyxelError(msg, code)                                
            except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 801
                    raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 800
                raise ZyxelError(msg, code)

        return deleted

    # ------------------------------------------------------------------------------------------------------------------
    # Get methods
    # ------------------------------------------------------------------------------------------------------------------

    async def _get_down_up_load_speed(self):
        down_up_load_speed = {
            "download_speed": None,
            "upload_speed": None
        }
        traffic_status = await self._get_traffic_status()
        now = time.time()
        bytes_received = traffic_status["bridgingStatus"][0]["BytesReceived"]
        bytes_sent = traffic_status["bridgingStatus"][0]["BytesSent"]
        if self._bytes_time is not None:
            diff_seconds = now - self._bytes_time
            diff_bytes_received = bytes_received - self._bytes_received
            upload_speed = diff_bytes_received / ( diff_seconds * 1000 )
            down_up_load_speed["upload_speed"] = upload_speed
            diff_bytes_sent = bytes_sent - self._bytes_sent
            download_speed = diff_bytes_sent / (diff_seconds * 1000)
            down_up_load_speed["download_speed"] = download_speed
        self._bytes_time = now
        self._bytes_received = bytes_received
        self._bytes_sent = bytes_sent
        return down_up_load_speed

    async def _get_cellwan_wait_state(self):

        success = False

        if await self._get_user_login() is not None:

            url = "http://" + self._ip_address + "/cgi-bin/DAL?oid=cellwan_wait_state"
            headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "CSRFToken": self._sessionkey,
                "Cache-Control": "max-age=0",
                "Connection": 'keep-alive',
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Host": self._ip_address,
                "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT",
                "Referer": "http://" + self._ip_address + "/Broadband",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }

            try:
                async with async_timeout.timeout(30):  # Timeout di 30 secondi
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, cookies=self._cookies) as response:
                            zyxel_json =  await response.json()
                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                if decoded_zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                    WAIT_STATE_SMS = decoded_zyxel_json.get("Object")[0].get("WAIT_STATE_SMS")
                                    if WAIT_STATE_SMS == "RESUME_SUCC":
                                        success = True
                                else:
                                    msg = 'Cell WAN Wait State Get (' + url + ') error: ' + str(zyxel_json)
                                    code = 1203
                                    raise ZyxelError(msg, code)
                            else:
                                msg = f"Request error {url}: {response.status}"
                                code = 1202
                                raise ZyxelError(msg, code)
            except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 1201
                    raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 1200
                raise ZyxelError(msg, code)

        return success

    async def _put_cellwan_wait_state(self):

        success = False

        if await self._get_user_login() is not None:

            url = "http://" + self._ip_address + "/cgi-bin/DAL?oid=cellwan_wait_state"
            headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "CSRFToken": self._sessionkey,
                "Cache-Control": "max-age=0",
                "Connection": 'keep-alive',
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Host": self._ip_address,
                "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT",
                "Referer": "http://" + self._ip_address + "/Broadband",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }

            data_dict = self._get_content_key_iv({
                "WAIT_STATE_SMS":"LOADING"
            })
            data_dict["key"] = ""
            data = JSON.dumps(data_dict)

            try:
                async with async_timeout.timeout(30):  # Timeout di 30 secondi
                    async with aiohttp.ClientSession() as session:
                        async with session.put(url, headers=headers, cookies=self._cookies, data=data) as response:
                            zyxel_json =  await response.json()
                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                if decoded_zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                    self._sessionkey = decoded_zyxel_json.get("sessionkey")
                                    success = True
                                else:
                                    msg = 'Cell WAN Wait State Put (' + url + ') error: ' + str(zyxel_json)
                                    code = 1103
                                    raise ZyxelError(msg, code)
                            else:
                                msg = f"Request error {url}: {response.status}"
                                code = 1102
                                raise ZyxelError(msg, code)
            except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 1101
                    raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 1100
                raise ZyxelError(msg, code)

        return success

    async def _put_cellwan_sms(self):

        success = False

        if await self._get_user_login() is not None:

            cellwan_sms = await self._get_cellwan_sms()
            cellwan_sms["SMS_InboxRetrieve"] = True
            data_dict = self._get_content_key_iv(cellwan_sms)
            data_dict["key"] = ""
            data = JSON.dumps(data_dict)

            url = "http://" + self._ip_address + "/cgi-bin/DAL?oid=cellwan_sms"
            headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "CSRFToken": self._sessionkey,
                "Cache-Control": "max-age=0",
                "Connection": 'keep-alive',
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Host": self._ip_address,
                "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT",
                "Referer": "http://" + self._ip_address + "/Broadband",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }

            try:
                async with async_timeout.timeout(30):  # Timeout di 30 secondi
                    async with aiohttp.ClientSession() as session:
                        async with session.put(url, headers=headers, cookies=self._cookies, data=data) as response:
                            zyxel_json =  await response.json()
                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                if decoded_zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                    self._sessionkey = decoded_zyxel_json.get("sessionkey")
                                    success = True
                                else:
                                    msg = 'Cell WAN Put SMS (' + url + ') error: ' + str(zyxel_json)
                                    code = 1003
                                    raise ZyxelError(msg, code)
                            else:
                                msg = f"Request error {url}: {response.status}"
                                code = 1002
                                raise ZyxelError(msg, code)
            except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 1001
                    raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 1000
                raise ZyxelError(msg, code)

        return success

    async def _get_cellwan_sms(self, num_retries=MAX_NUM_RETRIES):

        if await self._get_user_login() is not None:

            cellwan_sms_data = None

            url = "http://" + self._ip_address + "/cgi-bin/DAL?oid=cellwan_sms"
            headers = {
                "Accept": 'application/json, text/javascript, */*; q=0.01',
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": 'keep-alive',
                "Host": self._ip_address,
                "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT",
                "Referer": "http://" + self._ip_address + "/Broadband",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }
            try:
                async with async_timeout.timeout(10):  # Timeout di 10 secondi
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, cookies=self._cookies) as response:
                            zyxel_json =  await response.json()
                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                if decoded_zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                    cellwan_sms_data = decoded_zyxel_json
                                else:
                                    msg = 'Cell WAN SMS (' + url + ') error: ' + str(zyxel_json)
                                    code = 703
                                    raise ZyxelError(msg, code)
                            else:
                                if num_retries > 0:
                                    self._UserLogin = None
                                    cellwan_sms_data = await self._get_cellwan_sms(num_retries - 1)
                                else:
                                    msg = f"Request error {url}: {response.status}"
                                    code = 702
                                    raise ZyxelError(msg, code)
            except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 701
                    raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 700
                raise ZyxelError(msg, code)

            if cellwan_sms_data is not None:
                cellwan_sms_data_object = cellwan_sms_data.get("Object")
                if cellwan_sms_data_object is not None:
                    self._cellwan_sms = cellwan_sms_data_object[0]
                    await self._parse_cellwan_sms()

        return self._cellwan_sms

    async def _get_traffic_status(self, num_retries=MAX_NUM_RETRIES):

        if await self._get_user_login() is not None:

            traffic_status_data = None

            url = "http://" + self._ip_address + "/cgi-bin/DAL?oid=Traffic_Status"
            headers = {
                "Accept": 'application/json, text/javascript, */*; q=0.01',
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": 'keep-alive',
                "Host": self._ip_address,
                "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT",
                "Referer": "http://" + self._ip_address + "/TrafficStatus",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }
            try:
                async with async_timeout.timeout(10):  # Timeout di 10 secondi
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, cookies=self._cookies) as response:
                            zyxel_json =  await response.json()
                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                if decoded_zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                    traffic_status_data = decoded_zyxel_json
                                else:
                                    msg = 'Traffic Status (' + url + ') error: ' + str(zyxel_json)
                                    code = 803
                                    raise ZyxelError(msg, code)
                            else:
                                if num_retries > 0:
                                    self._UserLogin = None
                                    cellwan_sms_data = await self._get_cellwan_sms(num_retries - 1)
                                else:
                                    msg = f"Request error {url}: {response.status}"
                                    code = 802
                                    raise ZyxelError(msg, code)
            except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 801
                    raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 800
                raise ZyxelError(msg, code)

            if traffic_status_data is not None:
                traffic_status_data_object = traffic_status_data.get("Object")
                if traffic_status_data_object is not None:
                    self._traffic_status = traffic_status_data_object[0]

        return self._traffic_status

    async def _get_cellwan_sim(self, num_retries=MAX_NUM_RETRIES):
        """

        :param num_retries:
        :return:
        'USIM_Status': 'DEVST_SIM_RDY',
        'USIM_IMSI': USIM_IMSI,
        'USIM_ICCID': USIM_ICCID,
        'USIM_PIN_Protection': False,
        'USIM_PIN_STATE': '',
        'USIM_PIN_RemainingAttempts': 3,
        'USIM_PUK_RemainingAttempts': 10
        """
        if await self._get_user_login() is not None:

            cellwan_sim_data = None

            url = "http://" + self._ip_address + "/cgi-bin/DAL?oid=cellwan_sim"
            headers = {
                "Accept": 'application/json, text/javascript, */*; q=0.01',
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": 'keep-alive',
                "Host": self._ip_address,
                "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT",
                "Referer": "http://" + self._ip_address + "/Broadband",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }
            try:
                async with async_timeout.timeout(10):  # Timeout di 10 secondi
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, cookies=self._cookies) as response:
                            zyxel_json =  await response.json()
                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                if decoded_zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                    cellwan_sim_data = decoded_zyxel_json
                                else:
                                    msg = 'Cell Wan SIM (' + url + ') error: ' + str(zyxel_json)
                                    code = 603
                                    raise ZyxelError(msg, code)
                            else:
                                if num_retries > 0:
                                    self._UserLogin = None
                                    cellwan_sim_data = await self._get_cellwan_sim(num_retries - 1)
                                else:
                                    msg = f"Request error {url}: {response.status}"
                                    code = 602
                                    raise ZyxelError(msg, code)
            except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 601
                    raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 600
                raise ZyxelError(msg, code)

            if cellwan_sim_data is not None:
                cellwan_sim_data_object = cellwan_sim_data.get("Object")
                if cellwan_sim_data_object is not None:
                    self._cellwan_sim = cellwan_sim_data_object[0]

        return self._cellwan_sim

    async def _get_cellwan_status(self, num_retries=MAX_NUM_RETRIES):

        if self._cellwan_status_timestamp is None or time.time() > self._cellwan_status_timestamp + self.MIN_INTERVAL_S:

            self._cellwan_status_timestamp = time.time()

            if await self._get_user_login() is not None:

                cellwan_status_data = None

                url = "http://" + self._ip_address + "/cgi-bin/DAL?oid=cellwan_status"
                headers = {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Pragma': 'no-cache',
                    'Referer': 'http://' + self._ip_address + '/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest',
                }
                try:
                    async with async_timeout.timeout(10):  # Timeout di 10 secondi
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, headers=headers, cookies=self._cookies) as response:
                                zyxel_json =  await response.json()
                                if response.status == 200:
                                    decoded_zyxel_str = self.dxc(
                                        zyxel_json.get("content"),
                                        self._aes_key,
                                        zyxel_json.get("iv")
                                    )
                                    decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                    if decoded_zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                        cellwan_status_data = decoded_zyxel_json
                                    else:
                                        msg = 'Cell Status (' + url + ') error: ' + str(zyxel_json)
                                        code = 403
                                        raise ZyxelError(msg, code)
                                else:
                                    if num_retries > 0:
                                        self._UserLogin = None
                                        cellwan_status_data = await self._get_cellwan_status(num_retries - 1)
                                    else:
                                        msg = f"Request error {url}: {response.status}"
                                        code = 402
                                        raise ZyxelError(msg, code)
                except aiohttp.ClientError as err:
                        msg = f"Connection error {url}: {err}"
                        code = 401
                        raise ZyxelError(msg, code)
                except asyncio.TimeoutError:
                    msg = f"Connection timeout {url}"
                    code = 400
                    raise ZyxelError(msg, code)

                if cellwan_status_data is not None:
                    cellwan_status_data_object = cellwan_status_data.get("Object")
                    if cellwan_status_data_object is not None:
                        self._cellwan_status = cellwan_status_data_object[0]

        return self._cellwan_status

    async def _get_user_login(self):
        if self._UserLogin is None:
            if await self._get_rsa_public_key() is not None:
                url = 'http://' + self._ip_address + '/UserLogin'
                data = self._get_user_login_content_key_iv()
                headers = {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'If-Modified-Since': 'Thu, 01 Jun 1970 00:00:00 GMT',
                    'Origin': 'http://' + self._ip_address,
                    'Pragma': 'no-cache',
                    'Referer': 'http://' + self._ip_address + '/login',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest',
                }
                try:
                    async with async_timeout.timeout(10):  # Timeout di 10 secondi
                        async with aiohttp.ClientSession() as session:
                            async with session.post(url, json=data, headers=headers) as response:
                                zyxel_json =  await response.json()
                                if response.status == 200:
                                    self._UserLogin = zyxel_json
                                    user_login_str = self.dxc(
                                        self._UserLogin['content'],
                                        self._aes_key,
                                        self._UserLogin['iv']
                                    )
                                    user_login_json = JSON.loads(user_login_str)
                                    self._sessionkey = user_login_json.get('sessionkey')
                                    self.info("UserLogin successfully executed")
                                    set_cookie = response.headers.get('Set-Cookie')
                                    if set_cookie:
                                        session_cookie = set_cookie.split(';')[0]
                                        cookie_name, cookie_value = session_cookie.split('=')
                                        self._cookies = {cookie_name: cookie_value}
                                else:
                                    msg = f"Request error {url}: {response.status}"
                                    code = 302
                                    raise ZyxelAuthError(msg, code)
                except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 301
                    raise ZyxelAuthError(msg, code)
                except asyncio.TimeoutError:
                    msg = f"Connection timeout {url}"
                    code = 300
                    raise ZyxelAuthError(msg, code)
        return self._UserLogin

    async def _get_basic_information(self):
        if self._BasicInformation is None:
            async with aiohttp.ClientSession() as session:  # Inizializza la sessione se non esiste già
                url = 'http://' + self._ip_address + '/getBasicInformation'
                try:
                    async with async_timeout.timeout(10):  # Timeout di 10 secondi
                        async with session.get(url) as response:
                            if response.status == 200:
                                zyxel_json =  await response.json()
                                if zyxel_json.get("result") == self.ZCFG_SUCCESS:
                                    self._BasicInformation = zyxel_json
                                    self.info("Basic Information successfully retrieved")
                                else:
                                    msg = 'Basic information (' + url + ') error: ' + str(zyxel_json)
                                    code = 203
                                    raise ZyxelError(msg, code)
                            else:
                                msg = f"Request error {url}: {response.status}"
                                code = 202
                                raise ZyxelError(msg, code)
                except aiohttp.ClientError as err:
                    msg = f"Connection error {url}: {err}"
                    code = 201
                    raise ZyxelError(msg, code)
                except asyncio.TimeoutError:
                    msg = f"Connection timeout {url}"
                    code = 200
                    raise ZyxelError(msg, code)
        return self._BasicInformation

    async def _get_rsa_public_key(self):
        if self._RSAPublicKey is None:
            await self._get_basic_information()
            url = 'http://' + self._ip_address + '/getRSAPublickKey'
            try:
                async with async_timeout.timeout(10):  # Timeout di 10 secondi
                    async with aiohttp.ClientSession() as session:  # Inizializza la sessione se non esiste già
                        async with session.get(url) as response:
                            if response.status == 200:
                                zyxel_json =  await response.json()
                                if zyxel_json.get("result") != self.ZCFG_SUCCESS:
                                    self.error('RSA Public Key (' + url + ') error: ' + str(zyxel_json))
                                    self.error(str(response.content))
                                else:
                                    self._RSAPublicKey = zyxel_json.get("RSAPublicKey")
                                    self.info("RSAPublicKey successfully retrieved")
                            else:
                                self.error(f"Errore nella richiesta {url}: {response.status}")
            except aiohttp.ClientError as err:
                msg = f"Connection error {url}: {err}"
                code = 101
                raise ZyxelError(msg, code)
            except asyncio.TimeoutError:
                self.error(f"Timeout nella connessione {url}")
                msg = f"Connection timeout {url}"
                code = 100
                raise ZyxelError(msg, code)
        return self._RSAPublicKey

    # ------------------------------------------------------------------------------------------------------------------
    # Data manipulation methods
    # ------------------------------------------------------------------------------------------------------------------

    def _get_user_login_content_key_iv(self):

        # Converte la password in bytes
        password_bytes = self._password.encode('utf-8')

        # Codifica la password (in bytes) in base64
        password_base64_bytes = base64.b64encode(password_bytes)

        # Converte il risultato da bytes a stringa
        base64_password = password_base64_bytes.decode('utf-8')

        user_login_dict = {
            "Input_Account": self._username,
            "Input_Passwd": base64_password,
            "currLang": "en",
            "RememberPassword": 0,
            "SHA512_password": False
        }

        return self._get_content_key_iv(json_dict=user_login_dict)

    def _get_content_key_iv(self, json_dict):

        json_str = JSON.dumps(json_dict, separators=(',', ':'))

        # Initialization Vector - iv
        iv32 = os.urandom(32)  # Vettore di inizializzazione di 32 byte
        iv = base64.b64encode(iv32).decode('utf-8')

        # Chiave AES
        if self._aes_key is None:
            random_aes_key = os.urandom(32)  # Chiave AES di 32 bytes (256 bit)
            self._aes_key = base64.b64encode(random_aes_key).decode('utf-8')
        aes_key = base64.b64decode(self._aes_key)

        # Crittografia dei dati con AES
        iv16 = iv32[:16]  # Vettore di inizializzazione di 16 byte
        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv16)
        encrypted_data = cipher_aes.encrypt(pad(json_str.encode('utf-8'), AES.block_size))
        content = base64.b64encode(encrypted_data).decode('utf-8')

        # Crittografia della chiave AES con RSA
        rsa_key = RSA.import_key(self._RSAPublicKey)
        cipher_rsa = PKCS1_v1_5.new(rsa_key)
        encrypted_aes_key = cipher_rsa.encrypt(base64.b64encode(aes_key))
        key = base64.b64encode(encrypted_aes_key).decode('utf-8')

        # Restituisce i dati cifrati e la chiave AES cifrata
        data = {
            'content': content,
            'key': key,
            'iv': iv
        }

        return data

    def dxc(
        self,
        encrypted_data,
        aes_key,
        iv
    ):

        # Decodifica le stringhe in Base64
        encrypted_data = base64.b64decode(encrypted_data)
        aes_key = base64.b64decode(aes_key)
        iv = base64.b64decode(iv)
        iv = iv[:16]

        # Crea il cifrario AES in modalità CBC
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)

        # Decrittografa i dati
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        # Restituisce i dati decrittografati come stringa UTF-8
        return decrypted_data.decode('utf-8')

    # ------------------------------------------------------------------------------------------------------------------
    # SMS related methods
    # ------------------------------------------------------------------------------------------------------------------

    async def _delete_all_sms_but_last(self):
        delete = False
        last_sms = None
        for YmdHMS in list(self._sms_by_YmdHMS.keys()):
            sms = self._sms_by_YmdHMS[YmdHMS]
            if delete:
                parsed_sms = await self._parse_sms(sms)
                self.debug(f"Deleting sms: {parsed_sms}")
                sms_obj_index = str(sms.get("ObjIndex"))
                if await self.delete_sms(ObjIndex=sms_obj_index):
                    self._sms_by_YmdHMS.pop(YmdHMS)
            else:
                last_sms = sms
                delete = True
        return last_sms

    async def _parse_cellwan_sms(self):
        if self._cellwan_sms is not None:
            self._sms_by_YmdHMS = {}
            cellwan_sms_inbox = self._cellwan_sms.get("SMS_Inbox")
            if cellwan_sms_inbox is not None:
                for inbox_sms in cellwan_sms_inbox:
                    inbox_sms_timestamp = await self._get_sms_timestamp(inbox_sms)
                    if inbox_sms_timestamp is not None:
                        # Store SMS
                        self._sms_by_YmdHMS[inbox_sms_timestamp] = inbox_sms
                self._sms_by_YmdHMS = dict(sorted(self._sms_by_YmdHMS.items(), reverse=True))

    async def _get_sms_timestamp(self, inbox_sms, output_format="%Y%m%d%H%M%S"):
        sms_timestamp = None
        inbox_sms_timestamp = inbox_sms.get("TimeStamp")
        if inbox_sms_timestamp is not None:
            inbox_sms_timestamp = inbox_sms_timestamp + "00"
            input_format = "%y/%m/%d,%H:%M:%S%z"
            inbox_sms_datetime = datetime.strptime(inbox_sms_timestamp, input_format)
            sms_timestamp = inbox_sms_datetime.strftime(output_format)
        return sms_timestamp

    async def _parse_sms(self, inbox_sms):

        # SMS ObjIndex
        inbox_sms_obj_index = inbox_sms.get("ObjIndex")

        # SMS From
        inbox_sms_encoded_from = inbox_sms.get("From")
        inbox_sms_from = ''.join(
            chr(int(inbox_sms_encoded_from[i:i + 2], 16)) for i in range(0, len(inbox_sms_encoded_from), 2))

        # SMS TimeStamp
        inbox_sms_timestamp = inbox_sms.get("TimeStamp")
        inbox_sms_timestamp = inbox_sms_timestamp + "00"
        input_format = "%y/%m/%d,%H:%M:%S%z"
        inbox_sms_datetime = datetime.strptime(inbox_sms_timestamp, input_format)
        output_format = "%d/%m/%Y %H:%M:%S"
        inbox_sms_timestamp = inbox_sms_datetime.strftime(output_format)

        # SMS Message
        inbox_sms_encoded_content = inbox_sms.get("Content", "")
        try:
            # tentativo di decodifica esadecimale (ogni 4 caratteri = UTF-16)
            inbox_sms_content_hex = [inbox_sms_encoded_content[i:i + 4]
                                     for i in range(0, len(inbox_sms_encoded_content), 4)]
            inbox_sms_msg = ''.join(chr(int(char, 16)) for char in inbox_sms_content_hex)
        except ValueError:
            # se non è hex valido, uso direttamente il contenuto
            inbox_sms_msg = inbox_sms_encoded_content

        return {
            "from": inbox_sms_from,
            "timestamp": inbox_sms_timestamp,
            "msg": inbox_sms_msg
        }



class ZyxelAuthError(Exception):
    """Eccezione personalizzata che accetta un messaggio e un codice di errore."""

    def __init__(self, message, code):
        # Chiama il costruttore della classe base (Exception) con il messaggio di errore
        super().__init__(message)
        self.code = code

    def __str__(self):
        # Ritorna una rappresentazione stringa dell'errore, includendo il codice
        return f"[Zyxel Authentication Error {self.code}]: {self.args[0]}"


class ZyxelError(Exception):
    """Eccezione personalizzata che accetta un messaggio e un codice di errore."""

    def __init__(self, message, code):
        # Chiama il costruttore della classe base (Exception) con il messaggio di errore
        super().__init__(message)
        self.code = code

    def __str__(self):
        # Ritorna una rappresentazione stringa dell'errore, includendo il codice
        return f"[Zyxel Error {self.code}]: {self.args[0]}"