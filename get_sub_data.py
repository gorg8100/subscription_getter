import urllib.request
from pathlib import Path
import hashlib
from typing import Union
from logger_logic import write_log


def get_subscription_data(source: str, headers: dict[str, str], log_file: Path) -> Union[str, None]:
    try:
        return get_from_source(source, headers, log_file)
    except Exception as err:
        try:
            data = get_from_cache(source)
            write_log(err, log_file, f"can't get data from source: {source} .Was taken from the cache.")
            return data
        except Exception as err:
            write_log(err, log_file, f"can't get data from source and cache: {source}")
            return None


def get_from_cache(source: str):
    cache_file = Path("cache").joinpath(hashlib.sha256(source.encode("utf-8")).hexdigest())
    return cache_file.read_text(encoding="utf-8")


def get_from_source(source: str, headers: dict[str, str], log_file: Path) -> str:
    if source.startswith("http"):
        data = web_get(source, headers)
    else:
        data = file_get(source)
    cache_path = Path("cache")
    cache_path = cache_path.joinpath(hashlib.sha256(source.encode("utf-8")).hexdigest())
    try:
        cache_path.parent.mkdir(exist_ok=True)
        cache_path.write_text(data, encoding="utf-8")
    except Exception as err:
        write_log(err, log_file, f"can't write cache to file: {cache_path}")
    return data


def web_get(subscription_url: str, headers: dict[str, str]) -> str:
    req = urllib.request.Request(subscription_url)
    for header in headers:
        req.add_header(header, headers[header])
    response = urllib.request.urlopen(req)
    text = response.read()
    return text.decode('utf-8')


def file_get(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        data = file.read()
    return data
