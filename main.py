import urllib.request
from logger_logic import logg
from settings import SUBSCRIPTION_URL, USER_AGENT, HWID, DEVICE_OS, VER_OS, DEVICE_MODEL, DATA_FILE_PATH


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
    write_subscription_data(get_subscription_data())


if __name__ == "__main__":
    main()
