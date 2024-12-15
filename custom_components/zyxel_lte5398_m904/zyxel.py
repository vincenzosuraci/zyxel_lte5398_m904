import asyncio
import aiohttp
import async_timeout
import base64
import os
import time
import json as JSON

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

    def __init__(
        self,
        params = {}
    ):
        self._ip_address = params.get("ip_address", None)
        self._username = params.get("username", None)
        self._password = params.get("password", None)

        self._BasicInformation = None
        self._RSAPublicKey = None
        self._UserLogin = None
        self._CellStatus = None
        self._CellStatusTimestamp = None

        self._session = None
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
        return await self._get_cell_status()

    async def test_connection(self):
        data = await self.fetch_data()
        return data is not None

    async def reboot(self):

        if self.getBasicInformation() is None:
            return None

        if self.getRSAPublickKey() is None:
            return None

        if self._UserLogin is None:
            self.getUserLogin()

        if self._UserLogin is not None:
            url = "http://" + self.ip_address + "/cgi-bin/Reboot"

            # session keeping cookies
            session = self.get_session()

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

            # Effettua la richiesta POST
            response = session.post(
                url,
                headers=headers
            )

            # get http status code
            http_status_code = response.status_code

            # check response is okay
            if http_status_code != 200:
                self.error("Reboot page (" + url + ") error: " + str(http_status_code))
                # get html in bytes
                self.debug(str(response.content))
                return None

            json_str = response.text

            zyxel_json = json_lib.loads(json_str)

            self.info(zyxel_json)

            decoded_zyxel_str = self.dxc(
                zyxel_json.get("content"),
                self.aes_key,
                zyxel_json.get("iv")
            )

            decoded_zyxel_json = json_lib.loads(decoded_zyxel_str)

            reboot_result = decoded_zyxel_json.get("result")

            if reboot_result == self.ZCFG_SUCCESS:
                return True

        return False

    # ------------------------------------------------------------------------------------------------------------------
    # Do methods
    # ------------------------------------------------------------------------------------------------------------------

    async def _do_reboot(self):


    # ------------------------------------------------------------------------------------------------------------------
    # Get methods
    # ------------------------------------------------------------------------------------------------------------------

    async def _get_cell_status(self, num_retries=MAX_NUM_RETRIES):

        if self._CellStatusTimestamp is None or time.time() > self._CellStatusTimestamp + self.MIN_INTERVAL_S:

            self._CellStatusTimestamp = time.time()

            if await self._get_user_login() is not None:

                cell_status_data = None

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
                        await self._async_init_session()
                        async with self._session.get(url, headers=headers, cookies=self._cookies) as response:
                            zyxel_json = await response.json()
                            if response.status == 200:
                                decoded_zyxel_str = self.dxc(
                                    zyxel_json.get("content"),
                                    self._aes_key,
                                    zyxel_json.get("iv")
                                )
                                decoded_zyxel_json = JSON.loads(decoded_zyxel_str)
                                if decoded_zyxel_json.get("result") == "ZCFG_SUCCESS":
                                    cell_status_data = decoded_zyxel_json
                                else:
                                    msg = 'Cell Status (' + url + ') error: ' + str(zyxel_json)
                                    code = 403
                                    raise ZyxelError(msg, code)
                                await self._async_close_session()
                            else:
                                if num_retries > 0:
                                    self._UserLogin = None
                                    await self._async_close_session()
                                    cell_status_data = await self._get_cell_status(num_retries - 1)
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

                if cell_status_data is not None:
                    cell_status_data_object = cell_status_data.get("Object")
                    if cell_status_data_object is not None:
                        self._CellStatus = cell_status_data_object[0]
                        self.debug(self._CellStatus)

        return self._CellStatus

    async def _get_user_login(self):
        if self._UserLogin is None:
            if await self._get_rsa_public_key() is not None:
                url = 'http://' + self._ip_address + '/UserLogin'
                data = self._get_content_key_iv()
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
                        await self._async_init_session()
                        async with self._session.post(url, json=data, headers=headers) as response:
                            zyxel_json = await response.json()
                            if response.status == 200:
                                self._UserLogin = zyxel_json
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
            await self._async_init_session()  # Inizializza la sessione se non esiste già
            url = 'http://' + self._ip_address + '/getBasicInformation'
            try:
                async with async_timeout.timeout(10):  # Timeout di 10 secondi
                    async with self._session.get(url) as response:
                        if response.status == 200:
                            zyxel_json = await response.json()
                            if zyxel_json.get("result") == "ZCFG_SUCCESS":
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
                    await self._async_init_session()  # Inizializza la sessione se non esiste già
                    async with self._session.get(url) as response:
                        if response.status == 200:
                            zyxel_json = await response.json()
                            if zyxel_json.get("result") != "ZCFG_SUCCESS":
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

    def _get_content_key_iv(self):

        # Converte la password in bytes
        password_bytes = self._password.encode('utf-8')

        # Codifica la password (in bytes) in base64
        password_base64_bytes = base64.b64encode(password_bytes)

        # Converte il risultato da bytes a stringa
        base64_password = password_base64_bytes.decode('utf-8')

        s = {
            "Input_Account": self._username,
            "Input_Passwd": base64_password,
            "currLang": "en",
            "RememberPassword": 0,
            "SHA512_password": False
        }

        s_str = JSON.dumps(s, separators=(',', ':'))

        # Initilization Vector - iv
        iv32 = os.urandom(32)  # Vettore di inizializzazione di 32 byte
        iv = base64.b64encode(iv32).decode('utf-8')

        # Chiave AES
        aes_key = os.urandom(32)  # Chiave AES di 32 bytes (256 bit)
        self._aes_key = base64.b64encode(aes_key).decode('utf-8')

        # Crittografia dei dati con AES
        iv16 = iv32[:16]  # Vettore di inizializzazione di 16 byte
        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv16)
        encrypted_data = cipher_aes.encrypt(pad(s_str.encode('utf-8'), AES.block_size))
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
    # Session related methods
    # ------------------------------------------------------------------------------------------------------------------

    async def _async_init_session(self):
        """ Init session """
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self.debug("Session started")

    async def _async_close_session(self):
        """ Close session """
        if self._session:
            await self._session.close()
            self._session = None
            self.debug("Session closed")


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