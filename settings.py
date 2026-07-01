from typing import Union, Literal

SUBSCRIPTION_URL = ""

USER_AGENT = "Happ/3.13.0 (Android 14; Pixel 8 Pro)"
HWID = "5F0A4453542220203920AC1520201E448454046B459429294B43F"
DEVICE_OS = "Android 14"
VER_OS = "14"
DEVICE_MODEL = "Pixel 8 Pro"

DATA_FILE_PATH = "data.json"
DATA_LOGS_PATH = "logs.txt"

CLEARED_DATA = True
CLEARED_DATA_FILE_PATH = "cleared_json_data.json"
REPLACE_ROUTING: Union[dict, Literal["delete", "not-modify"]] = {"domainStrategy": "AsIs",
                                                                 "rules": [
                                                                     {
                                                                         "domain": [
                                                                             "geosite:category-ads-all"
                                                                         ],
                                                                         "outboundTag": "block"
                                                                     },
                                                                     {
                                                                         "domain": [
                                                                             "geosite:category-ru"
                                                                         ],
                                                                         "outboundTag": "direct"
                                                                     }
                                                                 ]}
