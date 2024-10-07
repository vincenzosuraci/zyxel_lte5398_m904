import base64

import requests

import json as json_lib

import os

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Util.Padding import pad

import json

# ----------------------------------------------------------------------------------------------------------------------
#
# HO.MOBILE CRAWLER
#
# ----------------------------------------------------------------------------------------------------------------------

class ZyXEL_LTE5398_M904_Crawler:

    def __init__(
        self,
        ip_address,
        username,
        password
    ):
        self._ip_address = ip_address
        self._username = username
        self._password = password
        self._credit = {}

        self._BasicInformation = None
        self._RSAPublicKey = None


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

    def debug(self, msg):
        print(msg)

    def info(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

    @staticmethod
    def save_info(pnk, v, attributes):
        pass

    def get_data(self):

        # --------------------------------------------------------------------------------------------------------------
        # FASE 1 - getBasicInformation
        # --------------------------------------------------------------------------------------------------------------

        # login url
        url = 'http://' + self.ip_address + '/getBasicInformation'

        # session keeping cookies
        session = requests.Session()

        response = session.get(url)

        # get http status code
        http_status_code = response.status_code

        # check response is okay
        if http_status_code != 200:

            self.error('basic information page (' + url + ') error: ' + str(http_status_code))

            # get html in bytes
            self.debug(str(response.content))

        else:

            json_str = response.text

            zyxel_json = json_lib.loads(json_str)

            if zyxel_json.get("result") != "ZCFG_SUCCESS":

                self.error('basic information page (' + url + ') error: ' + str(zyxel_json))

                # get html in bytes
                self.error(str(response.content))

            else:

                # ------------------------------------------------------------------------------------------------------
                # FASE 2 - getRSAPublickKey
                # ------------------------------------------------------------------------------------------------------

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

                else:

                    json_str = response.text

                    zyxel_json = json_lib.loads(json_str)

                    if zyxel_json.get("result") != "ZCFG_SUCCESS":

                        self.error('RSA Publick Key page (' + url + ') error: ' + str(zyxel_json))

                        # get html in bytes
                        self.error(str(response.content))

                    else:

                        self._RSAPublicKey = zyxel_json.get("RSAPublicKey")

                        # ----------------------------------------------------------------------------------------------
                        # FASE 3 - UserLogin
                        # ----------------------------------------------------------------------------------------------

                        # login url
                        url = 'http://' + self.ip_address + '/UserLogin'

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


                        data = self.aes_rsa_encrypt(
                            json.dumps(s),
                            self._RSAPublicKey
                        )

                        base64_encoded_aes_key = 'TIuhVauTJSF/G1qwx/u60pUgivXZuypgcuAUJNckx8jlFkd+08COrNK5Z4zVi48F35tpMGI7PJp8XO+AN4hqjpkpR7LQMeH9JjyAaGl7lgEf3HLYkZydOUNq3Ft9CbPqJZHvReGRguTt7xOgONvpU1EX8nYRe/5wxIYenO3DJEh+3rVxGzzAtHxOBJCaS2h1s/es/eAxhH8bDs+dvrgeKHeU1KDs/WkHe+drQItiWm1YVap5bXyQ8y1SHdUK2uXX5Bo/iEd9JjyVmOjZC9cjivzxp4YthpPxwIWJuPMgHcBTuYVsBP8CtQLBjFsAfMhRpf68RpUtAMTbqVSKkisFlA=='

                        data = {
                            'content': 'FsSSrmypE+/oxm/j3rr3I5gG4ytDh266seRU8Ix5K/3jm0eOS4Fom4peK1J0x0aDbjHd0f0BWa0d6XXcqurJWuzzFfUUwuTlFr59gZD5P5GwKLbSX2C0fpx+7MMFUWfaiZBbLUYcS2kbR1Qt3TS65Scnshel3C7wXqHwO39qPFA=',
                            'key': base64_encoded_aes_key,
                            'iv': '4wxpWNR2txl1FcyE9pn+r/4b5PtCyuqUIGhrOfdQzys='
                        }

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

                        else:

                            json_str = response.text

                            zyxel_json = json_lib.loads(json_str)

                            self.info(zyxel_json)

                            # ------------------------------------------------------------------------------------------
                            # FASE 4 - Cell Status
                            # ------------------------------------------------------------------------------------------

                            url = "http://" + self.ip_address + "/cgi-bin/DAL?oid=cellwan_status"
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

                            else:

                                json_str = response.text

                                zyxel_json = json_lib.loads(json_str)

                                iv = zyxel_json.get("iv")
                                encrypted_data = zyxel_json.get("content")

                                # Decodifica la stringa Base64
                                aes_key_decoded_bytes = base64.b64decode(base64_encoded_aes_key)

                                # Converte i byte in una stringa
                                aes_key = aes_key_decoded_bytes.decode('utf-8', errors='ignore')

                                data = self.dxc(encrypted_data, aes_key, iv)

                                self.info(data)

    def dxc(self, encrypted_data, aes_key, iv):
        # Decodifica le stringhe in Base64
        encrypted_data = base64.b64decode(encrypted_data)
        aes_key = base64.b64decode(aes_key)
        iv = base64.b64decode(iv)

        # Crea il cifrario AES in modalità CBC
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)

        # Decrittografa i dati
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        # Restituisce i dati decrittografati come stringa UTF-8
        return decrypted_data.decode('utf-8')

    def aes_rsa_encrypt(
        self,
        data,
        public_key
    ):

        # Genera una chiave AES casuale
        aes_key = os.urandom(32)  # Chiave AES di 256 bit
        iv = os.urandom(16)  # Vettore di inizializzazione di 16 byte

        # Crittografia dei dati con AES
        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
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