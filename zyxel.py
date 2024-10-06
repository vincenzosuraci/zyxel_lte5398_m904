import requests

import json as json_lib

from base64 import b64decode
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

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

                # ----------------------------------------------------------------------------------------------------------
                # FASE 2 - getRSAPublickKey
                # ----------------------------------------------------------------------------------------------------------

                # login url
                url = 'http://' + self.ip_address + '/getRSAPublickKey'

                # session keeping cookies
                session = requests.Session()

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

                        self._BasicInformation = zyxel_json.get("RSAPublicKey")

                        self.info(self._BasicInformation)

                        # Dati forniti
                        json_data = {
                            "content": "aO lSG F2OcodRr5ysjjyEYV05bvTVgONs2kvXFR4cgVzoXn2zTAW5H1CR3UY6yTkQ9sWOaBRqMpf0eP5gfMIQLfihlu3GPY 41xUQexFs2zRFy29iBXM0eSx4 tPMPjb3FbWHMlcb0AkeTQP8/0eW4J6qvuBihzSEEFoQvh1UI: ",
                            "key": "gD1LBXT26HN15iULyjpb14UlOwxczttx2J2G5NUS9iK7 d/2Fkj/0SRBnBsUjsRRa5O2G5u5avNx9td3bCynL1WfAlwFv2czN/tPaSyjjVVdlsQsTezyhGoIU61sYDbILhp1zb2JqLKh/UB 1/X0sW01/iC30 mlAKZnnt5OOlwk0h2Ek4uoEXbIohDv/TaruHPFzo5RyIxNC/Z78LKa0Llzo ODYY6J9IKP1e4mO43aP85YJcTsW8Jx1hQHcJX0GwUQq0E KKt yRu8ANIbYk8bc3ZiLkFg0xdcXCExGbBCZzAaudCWUd0CNac9hq9m0ncI/udLeL5Atk9FOElydw==",
                            "iv": "QcunEA1jqanSf089gkEsunBagkBkQpEsCSoaOsTrE1M="
                        }

                        # Esegui la decrittazione

                        decrypted_text = self.decrypt_data(json_data['content'], json_data['key'], json_data['iv'])

                        print("Testo decifrato: " + decrypted_text)



            """

            # ----------------------------------------------------------------------------------------------------------
            #   FASE 2 - Recupero dell'accountId dal numero di telefono
            # ----------------------------------------------------------------------------------------------------------

            # login url
            url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/checkAccount'

            # set POST https params
            json = {
                "email": None,
                "phoneNumber": phone_number,
                "channel": "WEB"
            }
            headers = {

                "Content-Type": "application/json",
                "User-Agent": "HomeAssistant",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": "https://www.ho-mobile.it/",

            }

            response = session.post(url, json=json, headers=headers)

            # get http status code
            http_status_code = response.status_code

            # check response is okay
            if http_status_code != 200:

                self.error('login page (' + url + ') error: ' + str(http_status_code))

                # get html in bytes
                self.debug(str(response.text))

            else:
                # get html in bytes
                json_str = response.text
                json = json_lib.loads(json_str)
                status = json['operationStatus']['status']
                self.debug('Phone number ' + str(phone_number) + ' status is ' + status)
                if status != 'OK':

                    diagnostic = json['operationStatus']['diagnostic']
                    errorCode = json['operationStatus']['errorCode']
                    self.debug('Phone number ' + str(phone_number) +
                               ' errorCode: ' + errorCode +
                               ' - diagnostic: ' + diagnostic
                               )

                else:

                    # --------------------------------------------------------------------------------------------------
                    #   FASE 3 - Login tramite accountId e password
                    # --------------------------------------------------------------------------------------------------

                    account_id = json['accountId']

                    # login url
                    url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/login'

                    # set POST https params
                    json = {
                        'accountId': account_id,
                        'email': None,
                        'phoneNumber': phone_number,
                        'password': self.password,
                        'channel': "WEB",
                        'isRememberMe': False
                    }

                    headers = {
                        'Referer': 'https://www.ho-mobile.it/',
                        'Content-Type': 'application/json'
                    }

                    response = session.post(url, json=json, headers=headers)

                    # get http status code
                    http_status_code = response.status_code

                    # check response is okay
                    if http_status_code != 200:

                        self.error('login page (' + url + ') error: ' + str(http_status_code))

                        # get html in bytes
                        self.debug(str(response.text))

                    else:
                        # get html in bytes
                        self.debug('Username e password inseriti CORRETTAMENTE')

                        # ----------------------------------------------------------------------------------------------
                        #   FASE 3 - Recupero del productId
                        # ----------------------------------------------------------------------------------------------

                        # login url
                        url = 'https://www.ho-mobile.it/leanfe/restAPI/CatalogInfoactivationService/getCatalogInfoactivation'

                        # set POST https params
                        json = {
                            "channel": "WEB",
                            "phoneNumber": phone_number
                        }

                        headers = {
                            'Referer': 'https://www.ho-mobile.it/',
                            'Content-Type': 'application/json'
                        }

                        response = session.post(url, json=json, headers=headers)

                        # get http status code
                        http_status_code = response.status_code

                        # check response is okay
                        if http_status_code != 200:

                            self.error(
                                'login page (' + url + ') error: ' + str(http_status_code))

                            # get html in bytes
                            self.debug(str(response.text))

                        else:

                            json_str = response.text
                            # self.debug(json_str)
                            json = json_lib.loads(json_str)

                            product_id = json['activeOffer']['productList'][0]['productId']

                            # ------------------------------------------------------------------------------------------
                            #   FASE 4 - Recupero dei contatori
                            # ------------------------------------------------------------------------------------------

                            # login url
                            url = 'https://www.ho-mobile.it/leanfe/restAPI/CountersService/getCounters'

                            # set POST https params
                            json = {
                                "channel": "WEB",
                                "phoneNumber": phone_number,
                                "productId": product_id
                            }

                            headers = {
                                'Referer': 'https://www.ho-mobile.it/',
                                'Content-Type': 'application/json'
                            }

                            response = session.post(url, json=json, headers=headers)

                            # get http status code
                            http_status_code = response.status_code

                            # check response is okay
                            if http_status_code != 200:

                                self.error('login page (' + url + ') error: ' + str(
                                    http_status_code))

                                # get html in bytes
                                self.debug(str(response.text))

                            else:

                                json_str = response.text
                                # self.debug(json_str)

                                json = json_lib.loads(json_str)

                                if phone_number not in self.credit:
                                    self.credit[phone_number] = {}

                                for item in json['countersList'][0]['countersDetailsList']:
                                    uom = item['residualUnit']
                                    if uom in ['GB', 'MB']:
                                        # ------------------------------------------------------------------------------
                                        # Recupero dei M/Gbyte residui
                                        # ------------------------------------------------------------------------------
                                        key = 'internet'
                                        value = item['residual']
                                        icon = 'mdi:web'
                                        self.credit[phone_number][key] = {
                                            'value': value,
                                            'icon': icon,
                                            'uom': uom
                                        }

                                        # ------------------------------------------------------------------------------
                                        # Recupero dei M/Gbyte totali
                                        # ------------------------------------------------------------------------------
                                        key = 'internet_threshold'
                                        value = item['threshold']
                                        icon = 'mdi:web'
                                        self.credit[phone_number][key] = {
                                            'value': value,
                                            'icon': icon,
                                            'uom': uom
                                        }

                                # ------------------------------------------------------------------------------
                                # Recupero della data di prossimo rinnovo
                                # ------------------------------------------------------------------------------

                                # Current Epoch Unix Timestamp (ad es. 1698184800000)
                                renewal_ts = json['countersList'][0]['productNextRenewalDate'] / 1000

                                key = 'internet_renewal'
                                value = datetime.fromtimestamp(renewal_ts).strftime('%d/%m/%Y')
                                icon = 'mdi:calendar-clock'
                                self.credit[phone_number][key] = {
                                    'value': value,
                                    'icon': icon,
                                    'uom': ''
                                }

                                for k, v in self.credit[phone_number].items():
                                    if v['value'] is not None:
                                        pnk = phone_number + '_' + k
                                        self.info(pnk + ': ' + str(v['value']))
                                        attributes = {
                                            'icon': v['icon'],
                                            'unit_of_measurement': v['uom']
                                        }
                                        self.save_info(pnk, v, attributes)
            """

    def add_padding(self, s):
        while len(s) % 4 != 0:
            s += '='
        return s

    def decrypt_data(self, content, key, iv):
        # Decodifica Base64
        decoded_content = b64decode(self.add_padding(content))
        decoded_key = b64decode(self.add_padding(key))
        decoded_iv = b64decode(self.add_padding(iv))

        # Crea il cifratore AES in modalità CBC con la chiave e il vettore di inizializzazione (IV)
        cipher = AES.new(decoded_key, AES.MODE_CBC, decoded_iv)

        # Decritta e rimuovi il padding PKCS7
        decrypted = unpad(cipher.decrypt(decoded_content), AES.block_size)

        # Converti il risultato in stringa UTF-8
        return decrypted.decode('utf-8')