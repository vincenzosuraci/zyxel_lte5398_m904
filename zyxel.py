import base64

import requests

import json as json_lib

import os

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Util.Padding import pad, unpad

import json

# ----------------------------------------------------------------------------------------------------------------------
#
# HO.MOBILE CRAWLER
#
# ----------------------------------------------------------------------------------------------------------------------

class ZyXEL_LTE5398_M904_Crawler:

    # Per ottenere questi dati:
    # 1) accedere alla pagina di login del router ZyXEL e attivare l'ispezione del codice
    # 2) eseguire il login e cercare in "network" una pagina chiamata "UserLogin"
    # 3) aprire il tab "Payload" e cliccare su "view source"
    # 4) copiare i dati e incollarli in basso
    CONTENT = 'Iwb47Odxd5B2pNHeWa7bR3M03R6/RPNFwjZ/8PqDtht6N7hlNIzm3GZbwi3MAkfeKKvyxUAstbfO50sjqCJ+6tt61TSLPwa5s3dAEY6PDMCHnyqpFW6IpwzyHqig65Vfw1CqYjrK4HUAgqtM4hqF9ZMgl35D6aYNsCGYSypptXQ='
    KEY = 'Cy8Xo9UL9L1cIpfZ7cHbP0+VvCkjm2C/ij66DEvZxvpG4v1xBaCIFCsN6wLcwXZMegySFIhGVMPl+KqXiIxEEDRbZrzuxxW83fJmHLHm8uQXvsV2UHm9ErDblxiM8UspGL7WY3FgJjAwNmcdgSlTo/b4SKtZfKIxYimwIna8eniyDZ2jbmrvBOLrGoNh3pohYju9UtJgUg3RNT2l67H+jsm/QhV/MTXTp03FhMjEgmjJ2ByyWy+KjmNqwbaWz9nKR4MZZdGSngXs4ad+pkJY8QdQ1ESKFOMtWdU2lzgqB1ZuXVhoXcLub+B5hZm4pSlzOYlEKM4L3WNfed6eBWcqzw=='
    IV = 'Es8+IC4u2QnhRX27bbdPReuo8s4i0wVJnDeCqjTULxQ='

    # Per ottenere LA AES_KEY:
    # 1) eseguire la versione dell'hack di miononno e vedere nella console
    AES_KEY = '490qltHlIA0iXoYgsHKqhyyq931dgM2CU+WIRcf3X5M='

    def __init__(
        self,
        ip_address,
        username,
        password,
        dynamic = False
    ):
        self._ip_address = ip_address
        self._username = username
        self._password = password
        self._dynamic = dynamic

        self._BasicInformation = None
        self._RSAPublicKey = None
        self._UserLogin = None
        self._CellStatus = None

        self._session = None

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def credit(self):
        return self._credit

    @property
    def dynamic(self):
        return self._dynamic

    @property
    def session(self):
        return self._session

    def debug(self, msg):
        print(msg)

    def info(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

    @staticmethod
    def save_info(pnk, v, attributes):
        pass

    def get_session(self):
        if self.session is None:
            # session keeping cookies
            self._session = requests.Session()
        return self.session

    def get_data(self):

        # --------------------------------------------------------------------------------------------------------------
        #
        # FASE 1 - getBasicInformation
        #
        # --------------------------------------------------------------------------------------------------------------

        if self.getBasicInformation() is None:
            return None

        # ------------------------------------------------------------------------------------------------------
        #
        # FASE 2 - getRSAPublickKey
        #
        # ------------------------------------------------------------------------------------------------------

        if self.getRSAPublickKey() is None:
            return None

        # --------------------------------------------------------------------------------------------------------------
        #
        # FASE 3 - UserLogin
        #
        # --------------------------------------------------------------------------------------------------------------

        if self.getUserLogin() is None:
            return None

        # --------------------------------------------------------------------------------------------------------------
        #
        # FASE 4 - Cell Status
        #
        # --------------------------------------------------------------------------------------------------------------

        if self.getCellStatus() is None:
            return None

        self.info(self._CellStatus)


    def getCellStatus(self):

        url = "http://" + self.ip_address + "/cgi-bin/DAL?oid=cellwan_status"

        # session keeping cookies
        session = self.get_session()

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'http://' + self.ip_address + '/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

        # Effettua la richiesta GET
        response = session.get(url, headers=headers, verify=False)

        # get http status code
        http_status_code = response.status_code

        # check response is okay
        if http_status_code != 200:
            self.error('Cell Status page (' + url + ') error: ' + str(http_status_code))

            # get html in bytes
            self.debug(str(response.content))

            return None

        json_str = response.text

        zyxel_json = json_lib.loads(json_str)

        iv = zyxel_json.get("iv")
        encrypted_data = zyxel_json.get("content")

        self._CellStatus = self.dxc(encrypted_data, self.AES_KEY, iv)

        return self._CellStatus

    def getUserLogin(self):

        # login url
        url = 'http://' + self.ip_address + '/UserLogin'

        # session keeping cookies
        session = self.get_session()

        # Recupero dei dati
        data = self.get_content_key_iv(
            dynamic=self.dynamic
        )

        # Definizione degli headers personalizzati
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'If-Modified-Since': 'Thu, 01 Jun 1970 00:00:00 GMT',
            'Origin': 'http://' + self.ip_address,
            'Pragma': 'no-cache',
            'Referer': 'http://' + self.ip_address + '/login',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

        response = session.post(
            url,
            json=data,
            headers=headers,
            verify=False
        )

        # get http status code
        http_status_code = response.status_code

        # check response is okay
        if http_status_code != 200:

            self.error('User login page (' + url + ') error: ' + str(http_status_code))

            # get html in bytes
            self.debug(str(response.content))

            return None

        json_str = response.text

        self._UserLogin = json_lib.loads(json_str)

        return self._UserLogin

    def getBasicInformation(self):

        # login url
        url = 'http://' + self.ip_address + '/getBasicInformation'

        # session keeping cookies
        session = self.get_session()

        response = session.get(url)

        # get http status code
        http_status_code = response.status_code

        # check response is okay
        if http_status_code != 200:
            self.error('basic information page (' + url + ') error: ' + str(http_status_code))

            # get html in bytes
            self.debug(str(response.content))

            return None

        json_str = response.text

        zyxel_json = json_lib.loads(json_str)

        # check response is successful
        if zyxel_json.get("result") != "ZCFG_SUCCESS":
            self.error('basic information page (' + url + ') error: ' + str(zyxel_json))
            # get html in bytes
            self.error(str(response.content))
            return None

        self._BasicInformation = zyxel_json

        return self._BasicInformation

    def getRSAPublickKey(self):

        session = self.get_session()

        # login url
        url = 'http://' + self.ip_address + '/getRSAPublickKey'

        response = session.get(url)

        # get http status code
        http_status_code = response.status_code

        # check response is okay
        if http_status_code != 200:
            self.error('RSA Publick Key page (' + url + ') error: ' + str(http_status_code))

            # get html in bytes
            self.debug(str(response.content))

            return None

        json_str = response.text

        zyxel_json = json_lib.loads(json_str)

        if zyxel_json.get("result") != "ZCFG_SUCCESS":
            self.error('RSA Public Key page (' + url + ') error: ' + str(zyxel_json))

            # get html in bytes
            self.error(str(response.content))

            return None

        self._RSAPublicKey = zyxel_json.get("RSAPublicKey")

        return self._RSAPublicKey


    def get_content_key_iv(self, dynamic=False, args={}):

        if dynamic:

            # Converte la password in bytes
            password_bytes = self.password.encode('utf-8')

            # Codifica la password (in bytes) in base64
            password_base64_bytes = base64.b64encode(password_bytes)

            # Converte il risultato da bytes a stringa
            base64_password = password_base64_bytes.decode('utf-8')

            s = {
                "Input_Account": self.username,
                "Input_Passwd": base64_password,
                "currLang": "en",
                "RememberPassword": 0,
                "SHA512_password": 0
            }

            # Recupero dei dati DINAMICO
            data = self.aes_rsa_encrypt(
                json.dumps(s),
                self._RSAPublicKey,
                args
            )

        else:

            data = {
                'content': self.CONTENT,
                'key': self.KEY,
                'iv': self.IV
            }

        return data


    # Con questa funzione provo a testare la bontà della funzione aes_rsa_encrypt()
    def test_aes_rsa_encrypt(self):
        static_get_content_key_iv = self.get_content_key_iv(
            dynamic=False
        )
        self.getRSAPublickKey()
        args = {
            'aes_key': base64.b64decode(self.AES_KEY),
            'iv': base64.b64decode(self.IV)
        }
        dynamic_get_content_key_iv = self.get_content_key_iv(
            dynamic=True,
            args=args
        )
        self.info("Static:")
        self.info(static_get_content_key_iv)
        self.info("Dynamic:")
        self.info(dynamic_get_content_key_iv)

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

    def aes_rsa_encrypt(
        self,
        data,
        public_key,
        args = {}
    ):

        # Genera una chiave AES casuale
        aes_key = args.get('aes_key', os.urandom(32))  # Chiave AES di 256 bit
        iv = args.get('iv', os.urandom(32))  # Vettore di inizializzazione di 16 byte

        # Crittografia dei dati con AES
        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv[:16])
        encrypted_data = cipher_aes.encrypt(pad(data.encode('utf-8'), AES.block_size))

        # Crittografia della chiave AES con RSA utilizzando PKCS1_OAEP
        rsa_key = RSA.import_key(public_key)
        cipher_rsa = PKCS1_OAEP.new(rsa_key)
        encrypted_aes_key = cipher_rsa.encrypt(aes_key)

        # Restituisce i dati cifrati e la chiave AES cifrata
        return {
            'content': base64.b64encode(encrypted_data).decode('utf-8'),
            'key': base64.b64encode(encrypted_aes_key).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8')
        }
