import base64

import requests

import json as json_lib

import os

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.Util.Padding import pad, unpad

import json

# ----------------------------------------------------------------------------------------------------------------------
#
# ZyXEL LTE5398-M904
#
# ----------------------------------------------------------------------------------------------------------------------

class ZyXEL:

    MAX_NUM_RETRIES = 1

    def __init__(
        self,
        params = {}
    ):
        self._ip_address = params.get("ip_address", None)
        self._content = params.get("content", None)
        self._key = params.get("key", None)
        self._iv = params.get("iv", None)
        self._aes_key = params.get("aes_key", None)

        self._username = params.get("username", None)
        self._password = params.get("password", None)

        self._dynamic = params.get("dynamic", None)
        if self.dynamic is None:
            self._dynamic = self.username is not None and self.password is not None

        self._dynamic_content = self.content is None
        self._dynamic_key = self.key is None
        self._dynamic_iv = self.iv is None
        self._dynamic_aes_key = self.aes_key is None

        self._BasicInformation = None
        self._RSAPublicKey = None
        self._UserLogin = None
        self._CellStatus = None

        self._session = None

        self._model = None
        self._sw_version = None

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
    def content(self):
        return self._content

    @property
    def key(self):
        return self._key

    @property
    def model(self):
        return self._model

    @property
    def sw_version(self):
        return self._sw_version

    @property
    def iv(self):
        return self._iv

    @property
    def aes_key(self):
        return self._aes_key

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

    def get_model(self):
        if self.model is None:
            basic_information = self.getBasicInformation()
            if basic_information is not None:
                self._model = basic_information.get("ModelName")
        return self._model

    def get_sw_version(self):
        if self.sw_version is None:
            basic_information = self.getBasicInformation()
            if basic_information is not None:
                self._sw_version = basic_information.get("SoftwareVersion")
        return self._sw_version

    def update_cell_status_data(self):

        cell_status_dict = {}

        # Recuperiamo i dati presenti nella chiave "Object"
        cell_status_data = self.get_cell_status_data()

        if cell_status_data is not None:
            cell_status_data_object = cell_status_data.get("Object")
            if cell_status_data_object is not None:
                cell_status = cell_status_data_object[0]
                if cell_status is not None:

                    # self.info(str(cell_status))

                    # RSRP
                    cell_status_dict["RSRP"] = {
                        "value": int(cell_status["INTF_RSRP"]),
                        "icon": "mdi:signal",
                        "uom": "dB"
                    }
                    # RSRQ
                    cell_status_dict["RSRQ"] = {
                        "value": int(cell_status["INTF_RSRQ"]),
                        "icon": "mdi:signal",
                        "uom": "dB"
                    }
                    # SINR
                    cell_status_dict["SINR"] = {
                        "value": int(cell_status["INTF_SINR"]),
                        "icon": "mdi:signal",
                        "uom": "dB"
                    }

                    # Access_Technology
                    cell_status_dict["Access_Technology"] = {
                        "value": cell_status["INTF_Current_Access_Technology"],
                        "icon": "mdi:signal"
                    }

                    # Cell ID
                    cell_status_dict["Cell_ID"] = {
                        "value": int(cell_status["INTF_Cell_ID"]),
                        "icon": "mdi:radio-tower"
                    }
                    # PhyCell_ID
                    cell_status_dict["PhyCell_ID"] = {
                        "value": int(cell_status["INTF_PhyCell_ID"]),
                        "icon": "mdi:radio-tower"
                    }
                    # eNodeB
                    cell_status_dict["eNodeB"] = {
                        "value": cell_status["INTF_Cell_ID"] // 256,
                        "icon": "mdi:radio-tower"
                    }

                    # Main Band
                    ul = 5 * ( int(cell_status["INTF_Uplink_Bandwidth"]) - 1 )
                    dl = 5 * (int(cell_status["INTF_Downlink_Bandwidth"]) - 1)
                    cell_status_dict["Main_Band"] = {
                        "value": cell_status["INTF_Current_Band"] + "(" + str(dl) + "MHz/" + str(ul) + "MHz)" ,
                        "icon": "mdi:radio-tower"
                    }

                    # Carrier Aggregated Bands
                    CA_Bands = ""
                    for scc in cell_status["SCC_Info"]:
                        if scc["Enable"]:
                            CA_Bands += scc["Band"] + " "
                    cell_status_dict["CA_Bands"] = {
                        "value": CA_Bands,
                        "icon": "mdi:radio-tower"
                    }

        for k, v in cell_status_dict.items():
            if v["value"] is not None:
                self.info(k + ': ' + str(v["value"]))
                attributes = {
                    "icon": v.get("icon"),
                    "unit_of_measurement": v.get("uom")
                }
                self.save_info(k, v, attributes)



    def get_cell_status_data(self):

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
        # FASE 3 - Cell Status
        #
        # --------------------------------------------------------------------------------------------------------------

        return self.getCellStatus()


    def getCellStatus(self, num_retries=MAX_NUM_RETRIES):

        if self._UserLogin is None:
            self.getUserLogin()

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
        response = session.get(
            url,
            headers=headers,
            verify=False
        )

        # get http status code
        http_status_code = response.status_code

        # check response is okay
        if http_status_code != 200:
            if num_retries > 0:
                self._UserLogin = None
                self._dynamic = False
                return self.getCellStatus(num_retries-1)
            else:
                self.error('Cell Status page (' + url + ') error: ' + str(http_status_code))
                # get html in bytes
                self.debug(str(response.content))
                return None

        json_str = response.text

        zyxel_json = json_lib.loads(json_str)

        #self.info(zyxel_json)

        decoded_zyxel_str = self.dxc(
            zyxel_json.get("content"),
            self.aes_key,
            zyxel_json.get("iv")
        )

        decoded_zyxel_json = json_lib.loads(decoded_zyxel_str )

        if decoded_zyxel_json.get("result") != "ZCFG_SUCCESS":
            self.error('Cell Status page (' + url + ') error: ' + str(zyxel_json))
            # get html in bytes
            self.error(str(response.content))
            return None

        self._CellStatus = decoded_zyxel_json

        return self._CellStatus

    def getUserLogin(self):

        # login url
        url = 'http://' + self.ip_address + '/UserLogin'

        # session keeping cookies
        session = self.get_session()

        # Recupero dei dati
        data = self.get_content_key_iv()

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
            if http_status_code == 401:
                json_str = response.text
                json = json_lib.loads(json_str)
                if json.get('result') == 'Decrypt Fail':
                    self.error('User login failure, due to a Decrypt Fail')
                    return None
            else:
                self.error('User login page (' + url + ') error: ' + str(http_status_code))
                # get html in bytes
                self.debug(str(response.content))
                return None

        json_str = response.text

        self._UserLogin = json_lib.loads(json_str)

        return self._UserLogin

    def getBasicInformation(self):

        if self._BasicInformation is None:

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

        if self._RSAPublicKey is None:

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


    def get_content_key_iv(self, args=None):

        if args is None:
            args = {}

        dynamic = args.get("dynamic", self.dynamic)

        if dynamic:

            #self.info("Login con username e password")

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
                "SHA512_password": False
            }

            s_str = json.dumps(s, separators=(',', ':'))

            #self.info(s_str)

            # Recupero dei dati DINAMICO
            data = self.get_dynamic_content_key_iv(
                s_str,
                self._RSAPublicKey,
                args
            )

        else:

            #self.info("Login con content, key e iv")

            data = {
                'content': self.content,
                'key': self.key,
                'iv': self.iv
            }

        return data


    # Con questa funzione provo a testare la bontà della funzione aes_rsa_encrypt()
    def test_aes_rsa_encrypt(self):
        args = {
            'dynamic': False,
        }
        static_get_content_key_iv = self.get_content_key_iv(
            args=args
        )
        self.getRSAPublickKey()
        args = {
            'dynamic': True,
            'aes_key': base64.b64decode(self.aes_key),
            'iv': base64.b64decode(self.iv)
        }
        dynamic_get_content_key_iv = self.get_content_key_iv(
            args=args
        )
        self.info("Static (to-be):")
        self.info(static_get_content_key_iv)
        self.info("Dynamic (as-is):")
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

    def get_dynamic_content_key_iv(
        self,
        data,
        public_key,
        args = {}
    ):

        # Initilization Vector - iv
        iv32 = args.get('iv')
        if iv32 is None:
            if self._dynamic_iv:
                iv32 = os.urandom(32)  # Vettore di inizializzazione di 32 byte
            else:
                iv32 = base64.b64decode(self.iv)
        iv = base64.b64encode(iv32).decode('utf-8')

        # Chiave AES
        aes_key = args.get('aes_key')
        if aes_key is None:
            if self._dynamic_aes_key:
                aes_key = os.urandom(32)  # Chiave AES di 32 bytes (256 bit)
                self._aes_key = base64.b64encode(aes_key).decode('utf-8')
            else:
                aes_key = base64.b64decode(self.aes_key)

        # Crittografia dei dati con AES
        content = args.get('content')
        if content is None:
            if self._dynamic_content:
                iv16 = iv32[:16]  # Vettore di inizializzazione di 16 byte
                cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv16)
                encrypted_data = cipher_aes.encrypt(pad(data.encode('utf-8'), AES.block_size))
                content = base64.b64encode(encrypted_data).decode('utf-8')
            else:
                content = self.content

        # Crittografia della chiave AES con RSA
        key = args.get('key')
        if key is None:
            if self._dynamic_key:
                rsa_key = RSA.import_key(public_key)
                cipher_rsa = PKCS1_v1_5.new(rsa_key)
                encrypted_aes_key = cipher_rsa.encrypt(base64.b64encode(aes_key))
                key = base64.b64encode(encrypted_aes_key).decode('utf-8')
            else:
                key = self.key

        # Restituisce i dati cifrati e la chiave AES cifrata
        data = {
            'content': content,
            'key': key,
            'iv': iv
        }

        #self.info(data)

        return data
