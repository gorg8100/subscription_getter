import urllib.request


def get_subscription_data(source: str, headers: dict[str, str]) -> str:
    if source.startswith("http"):
        return web_get(source, headers)
    else:
        return file_get(source)


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
