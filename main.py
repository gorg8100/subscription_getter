from settings_loader import load_settings

settings = load_settings("/etc/subscription_getter_settings.py")

import urllib.request # noqa
from logger_logic import logg # noqa
from clear_logic import clear_data # noqa
from settings import SUBSCRIPTION_URL, USER_AGENT, HWID, DEVICE_OS, VER_OS, DEVICE_MODEL, DATA_FILE_PATH, CLEARED_DATA # noqa


@logg()
def write_subscription_data(text) -> None:
    with open(DATA_FILE_PATH, "w", encoding="utf-8") as file:
        file.write(text)


@logg(5)
def get_subscription_data() -> str:
    req = urllib.request.Request(SUBSCRIPTION_URL)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('x-hwid', HWID)
    req.add_header('x-device-os', DEVICE_OS)
    req.add_header('x-ver-os', VER_OS)
    req.add_header('x-device-model', DEVICE_MODEL)
    response = urllib.request.urlopen(req)
    text = response.read()
    return text.decode('utf-8')


def main():
    data = get_subscription_data()
    write_subscription_data(data)
    if CLEARED_DATA:
        clear_data(data)


if __name__ == "__main__":
    main()
