from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json
from typing import Any, Union
from logger_logic import write_log


def multi_split(s: str, stop: list[str]) -> list[str]:
    ret = []
    sub_s = ""
    for symbol in s:
        if symbol in stop:
            ret.append(sub_s)
            sub_s = ""
            continue
        sub_s += symbol
    if sub_s:
        ret.append(sub_s)
    return ret


class FragmentUrl:
    protocol: str
    p_id: str
    host: str
    port: int
    params: dict[str, str]
    remark: str

    def __init__(self, url: str):
        parsed = urlparse(url)
        self.protocol = parsed.scheme
        netloc = multi_split(parsed.netloc, ["@", ":"])
        self.p_id = netloc[0]
        self.host = netloc[1]
        self.port = int(netloc[2])
        self.params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        self.remark = parsed.fragment
        return

    def get_param_as_list(self, item: str) -> list[str]:
        return self[item].split(",")

    def get_param_as_bool(self, item: str) -> bool:
        value = self[item]
        if value == "true":
            return True
        return False

    def get_param_as_int(self, item: str) -> int:
        return int(self[item])

    def get_param_from_json(self, item: str) -> dict:
        return json.loads(self[item])

    def try_get_param(self, param: str, key: str, d: dict[str, Any]):
        if param in self:
            d[key] = self[param]

    def try_get_param_as_list(self, param: str, key: str, d: dict[str, Any]):
        if param in self:
            d[key] = self.get_param_as_list(param)

    def try_get_param_as_bool(self, param: str, key: str, d: dict[str, Any]):
        if param in self:
            d[key] = self.get_param_as_bool(param)

    def try_get_param_as_int(self, param: str, key: str, d: dict[str, Any]):
        if param in self:
            d[key] = self.get_param_as_int(param)

    def try_get_param_from_json(self, param: str, key: str, d: dict[str, Any]):
        if param in self:
            d[key] = self.get_param_from_json(param)

    def __contains__(self, item: str) -> bool:
        return item in self.params

    def __getitem__(self, item: str) -> str:
        return self.params[item]


def get_default_json_config(outbound: dict) -> dict:
    return {
        "inbounds": [
            {
                "port": 10808,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {
                    "udp": True
                },
                "tag": "socks"
            },
            {
                "port": 10809,
                "listen": "127.0.0.1",
                "protocol": "http",
                "tag": "http"
            }
        ],
        "outbounds": [outbound]
    }


def get_default_json_outbound() -> dict:
    return {
        "streamSettings": {},
    }


def xray_url2xray_json(sub_data: str, log_file: Path, to_str: bool = True) -> Union[str, list[dict]]:
    urls = sub_data.split("\n")
    xray_json: list[dict] = []
    for url in urls:
        try:
            fragment_url = FragmentUrl(url)
            outbound = parse_url(fragment_url)
            xray_json.append(get_default_json_config(outbound))
        except Exception as err:
            write_log(err, log_file, f"problem with url:\n{url}")
    if to_str:
        return json.dumps(xray_json, indent=2, ensure_ascii=False)
    else:
        return xray_json


# ===============================

def parse_url(fragment_url: FragmentUrl) -> dict:
    outbound = get_default_json_outbound()
    stream_settings = {}
    if fragment_url.protocol in ["hysteria", "hysteria2", "hy", "hy2"]:
        outbound["protocol"] = "hysteria"
        outbound["settings"] = parse_hysteria2_settings(fragment_url)
        if "security" in fragment_url:
            parse_security(fragment_url, stream_settings)
        else:
            stream_settings["security"] = "tls"
            stream_settings["tlsSettings"] = parse_security_tls(fragment_url)
        if "type" in fragment_url:
            parse_transport_settings(fragment_url, stream_settings)
        else:
            stream_settings["method"] = "hysteria"
            stream_settings["hysteriaSettings"] = parse_transport_hysteria2(fragment_url)
    else:
        outbound["protocol"] = fragment_url.protocol
        outbound["settings"] = parse_settings(fragment_url)
        parse_security(fragment_url, stream_settings)
        parse_transport_settings(fragment_url, stream_settings)
    fragment_url.try_get_param_from_json("fm", "finalmask", stream_settings)
    outbound["streamSettings"] = stream_settings
    return outbound


# ===============================

def parse_settings(fragment_url: FragmentUrl) -> dict:
    protocol = fragment_url.protocol
    if protocol == "vless":
        return parse_vless_settings(fragment_url)
    elif protocol == "trojan":
        return parse_trojan_settings(fragment_url)
    elif protocol in ["hysteria", "hysteria2", "hy", "hy2"]:
        return parse_hysteria2_settings(fragment_url)
    else:
        raise ValueError(f"Unknown protocol: {protocol}")


def parse_vless_settings(fragment_url: FragmentUrl) -> dict:
    settings = {"address": fragment_url.host,
                "port": fragment_url.port,
                "id": fragment_url.p_id}
    if "encryption" in fragment_url:
        settings["encryption"] = fragment_url["encryption"]
    if "flow" in fragment_url:
        settings["flow"] = fragment_url["flow"]
    return settings


def parse_trojan_settings(fragment_url: FragmentUrl) -> dict:
    settings = {"address": fragment_url.host,
                "port": fragment_url.port,
                "id": fragment_url.p_id}
    return settings


def parse_hysteria2_settings(fragment_url: FragmentUrl) -> dict:
    settings = {"address": fragment_url.host,
                "port": fragment_url.port,
                "version": 2}
    return settings


# ===============================

def parse_security(fragment_url: FragmentUrl, stream_settings: dict):
    security = fragment_url["security"]
    if security == "tls":
        stream_settings["security"] = "tls"
        stream_settings["tlsSettings"] = parse_security_tls(fragment_url)
    elif security == "reality":
        stream_settings["security"] = "reality"
        stream_settings["realitySettings"] = parse_security_reality(fragment_url)
    else:
        raise ValueError(f"Unknown security: {security}")


def parse_security_tls(fragment_url: FragmentUrl) -> dict:
    tls_settings = {}
    fragment_url.try_get_param("sni", "serverName", tls_settings)
    fragment_url.try_get_param("fp", "fingerprint", tls_settings)
    fragment_url.try_get_param_as_list("alpn", "alpn", tls_settings)
    fragment_url.try_get_param_as_bool("allowInsecure", "allowInsecure", tls_settings)
    fragment_url.try_get_param("verifyPeerCertByName", "verifyPeerCertByName", tls_settings)
    return tls_settings


def parse_security_reality(fragment_url: FragmentUrl) -> dict:
    reality_settings = {}
    fragment_url.try_get_param("sni", "serverName", reality_settings)
    fragment_url.try_get_param("fp", "fingerprint", reality_settings)
    fragment_url.try_get_param("pbk", "password", reality_settings)
    fragment_url.try_get_param("sid", "shortId", reality_settings)
    fragment_url.try_get_param("spx", "spiderX", reality_settings)
    fragment_url.try_get_param("pqv", "mldsa65Verify", reality_settings)
    return reality_settings


# ===============================

def parse_transport_settings(fragment_url: FragmentUrl, stream_settings: dict):
    transport = fragment_url["type"]
    if transport in ["tcp", "raw"]:
        stream_settings["method"] = "raw"
        stream_settings["rawSettings"] = parse_transport_tcp_raw(fragment_url)
    elif transport == "xhttp":
        stream_settings["method"] = "xhttp"
        stream_settings["xhttpSettings"] = parse_transport_xhttp(fragment_url)
    elif transport == "kcp":
        stream_settings["method"] = "mkcp"
        stream_settings["kcpSettings"] = parse_transport_mkcp(fragment_url)
    elif transport == "grpc":
        stream_settings["method"] = "grpc"
        stream_settings["grpcSettings"] = parse_transport_grpc(fragment_url)
    elif transport == "ws":
        stream_settings["method"] = "websocket"
        stream_settings["wsSettings"] = parse_transport_web_socket(fragment_url)
    elif transport == "httpupgrade":
        stream_settings["method"] = "httpupgrade"
        stream_settings["httpupgradeSettings"] = parse_transport_http_upgrade(fragment_url)
    elif transport == "hysteria":
        stream_settings["method"] = "hysteria"
        stream_settings["hysteriaSettings"] = parse_transport_hysteria2(fragment_url)
    else:
        raise ValueError(f"Unknown transport: {transport}")


def parse_transport_tcp_raw(fragment_url: FragmentUrl) -> dict:
    settings = {}
    if "headerType" in fragment_url:
        header: dict[str, Any] = {"type": fragment_url["headerType"]}
        if header["type"] == "http":
            if "path" in fragment_url:
                request: dict[str, Any] = {"path": fragment_url.get_param_as_list("path")}
                if "host" in fragment_url:
                    headers: dict[str, Any] = {"Host": fragment_url.get_param_as_list("host")}
                    request["headers"] = headers
                header["request"] = request
            if "request" in fragment_url:
                header["request"] = fragment_url.get_param_from_json("request")
            if "response" in fragment_url:
                header["response"] = fragment_url.get_param_from_json("response")
        settings["header"] = header
    return settings


def parse_transport_xhttp(fragment_url: FragmentUrl) -> dict:
    settings = {}
    fragment_url.try_get_param("host", "host", settings)
    fragment_url.try_get_param("path", "path", settings)
    fragment_url.try_get_param("mode", "mode", settings)
    fragment_url.try_get_param_from_json("extra", "extra", settings)
    return settings


def parse_transport_mkcp(fragment_url: FragmentUrl) -> dict:
    settings = {}
    if "headerType" in fragment_url:
        settings["header"] = {"type": fragment_url["headerType"]}
    fragment_url.try_get_param("seed", "seed", settings)
    fragment_url.try_get_param_as_int("mtu", "mtu", settings)
    fragment_url.try_get_param_as_int("tti", "tti", settings)
    return settings


def parse_transport_grpc(fragment_url: FragmentUrl) -> dict:
    settings = {}
    fragment_url.try_get_param("serviceName", "serviceName", settings)
    if "multiMode" in fragment_url:
        if fragment_url["multiMode"] == "multi":
            settings["multiMode"] = True
        else:
            settings["multiMode"] = False
    return settings


def parse_transport_web_socket(fragment_url: FragmentUrl) -> dict:
    settings = {}
    fragment_url.try_get_param("path", "path", settings)
    fragment_url.try_get_param("host", "host", settings)
    return settings


def parse_transport_http_upgrade(fragment_url: FragmentUrl) -> dict:
    settings = {}
    fragment_url.try_get_param("path", "path", settings)
    fragment_url.try_get_param("host", "host", settings)
    return settings


def parse_transport_hysteria2(fragment_url: FragmentUrl) -> dict:
    settings = {"version": 2,
                "auth": fragment_url.p_id}
    return settings
