from typing import Union, Any
import json
from urllib import parse
from pathlib import Path
from logger_logic import write_log


class XrayUrlBuilder:
    protocol: str = None
    p_id: str = None
    host: str = None
    port: int = None
    params: dict[str, Any]
    remark: str = ""

    def __init__(self):
        self.params = {}

    def set_protocol(self, protocol: str):
        self.protocol = protocol

    def set_p_id(self, p_id: str):
        self.p_id = p_id

    def set_host(self, host: str):
        self.host = host

    def set_port(self, port: int):
        self.port = port

    def set_remark(self, remark: Union[str, None]):
        self.remark = remark

    def try_set_header(self, header: str, key: str, values: dict[str, Any]):
        if key in values:
            self[header] = values[key]
        return

    def __setitem__(self, key: str, value: Any):
        if isinstance(value, list):
            self.params[key] = ",".join(value)
        elif isinstance(value, bool):
            if value:
                self.params[key] = "true"
            else:
                self.params[key] = "false"
        elif isinstance(value, dict):
            self.params[key] = json.dumps(value)
        elif value is None:
            self.params[key] = "null"
        else:
            self.params[key] = value

    def __str__(self):
        if self.remark is None:
            self.remark = self.protocol
        query = parse.urlencode(self.params)
        netloc = f"{self.p_id}@{self.host}:{self.port}"
        return parse.urlunsplit((self.protocol, netloc, "", query, self.remark))


def xray_json2_xray_url(sub_data: str, log_file: Path, to_str: bool = True) -> Union[str, list[str]]:
    json_data: list[dict] = json.loads(sub_data)
    urls = []
    for config in json_data:
        if "routing" in config:
            routing = config["routing"]
            if "balancers" in routing:
                balancers = routing["balancers"]
                if len(balancers):
                    continue
        if "outbounds" not in config:
            continue
        remark = None
        if "remarks" in config:
            remark = config["remarks"]
        for outbound in config["outbounds"]:
            try:
                if outbound["protocol"] in ("blackhole", "freedom", "dns"):
                    continue
                url = XrayUrlBuilder()
                url.set_remark(remark)
                parse_outbound(url, outbound)
                urls.append(url)
            except Exception as err:
                write_log(err, log_file,
                          f"problem with outbound:\n{json.dumps(outbound, ensure_ascii=False, indent=2)}")
    if to_str:
        return "\n".join(map(str, urls))
    else:
        return list(map(str, urls))


# ===============================

def parse_outbound(url: XrayUrlBuilder, outbound: dict):
    protocol = outbound["protocol"]
    settings = outbound["settings"]
    parse_settings(url, protocol, settings)
    stream_settings = outbound["streamSettings"]
    parse_security(url, stream_settings)
    parse_transport_settings(url, stream_settings)
    url.try_set_header("fm", "finalmask", stream_settings)
    return


# ===============================

def parse_settings(url: XrayUrlBuilder, protocol: str, settings: dict):
    url.set_protocol(protocol)
    if protocol == "vless":
        parse_vless_settings(url, settings)
    elif protocol == "trojan":
        parse_trojan_settings(url, settings)
    elif protocol == "hysteria":
        parse_hysteria2_settings(url, settings)
    else:
        raise ValueError(f"Unknown protocol: {protocol}")


def parse_vless_settings(url: XrayUrlBuilder, settings: dict):
    url.set_protocol("vless")
    if "vnext" in settings:
        vnext = settings["vnext"][0]
        address = vnext["address"]
        port = vnext["port"]
        user = vnext["users"][0]
        encryption = user.get("encryption", "none")
        url.try_set_header("flow", "flow", user)
        p_id = user["id"]
    else:
        address = settings["address"]
        port = settings["port"]
        p_id = settings["id"]
        encryption = settings.get("encryption", "none")
        url.try_set_header("flow", "flow", settings)
    url.set_host(address)
    url.set_port(port)
    url.set_p_id(p_id)
    url["encryption"] = encryption
    return


def parse_trojan_settings(url: XrayUrlBuilder, settings: dict):
    url.set_protocol("trojan")
    if "servers" in settings:
        server = settings["servers"][0]
        address = server["address"]
        port = server["port"]
        password = server["password"]
    else:
        address = settings["address"]
        port = settings["port"]
        password = settings["password"]
    url.set_host(address)
    url.set_port(port)
    url.set_p_id(password)
    return


def parse_hysteria2_settings(url: XrayUrlBuilder, settings: dict):
    address = settings["address"]
    port = settings["port"]
    version = settings["version"]
    if version == 2:
        url.set_protocol("hysteria2")
    else:
        url.set_protocol("hysteria")
    url.set_host(address)
    url.set_port(port)
    return


# ===============================

def parse_security(url: XrayUrlBuilder, stream_settings: dict):
    security = stream_settings["security"]
    if security == "tls":
        tls_settings = stream_settings["tlsSettings"]
        parse_security_tls(url, tls_settings)
    elif security == "reality":
        reality_settings = stream_settings["realitySettings"]
        parse_security_reality(url, reality_settings)
    elif security == "none":
        return
    else:
        raise ValueError(f"Unknown security: {security}")


def parse_security_tls(url: XrayUrlBuilder, tls_settings: dict):
    url["security"] = "tls"
    url.try_set_header("sni", "serverName", tls_settings)
    url.try_set_header("fp", "fingerprint", tls_settings)
    url.try_set_header("alpn", "alpn", tls_settings)
    url.try_set_header("allowInsecure", "allowInsecure", tls_settings)
    url.try_set_header("verifyPeerCertByName", "verifyPeerCertByName", tls_settings)
    return


def parse_security_reality(url: XrayUrlBuilder, reality_settings: dict):
    url["security"] = "reality"
    url.try_set_header("sni", "serverName", reality_settings)
    url.try_set_header("fp", "fingerprint", reality_settings)
    if "password" in reality_settings:
        url["pbk"] = reality_settings["password"]
    elif "publicKey" in reality_settings:
        url["pbk"] = reality_settings["publicKey"]
    url.try_set_header("sid", "shortId", reality_settings)
    url.try_set_header("spx", "spiderX", reality_settings)
    url.try_set_header("pqv", "mldsa65Verify", reality_settings)
    return


# ===============================

def parse_transport_settings(url: XrayUrlBuilder, stream_settings: dict):
    transport: str
    if "method" in stream_settings:
        transport = stream_settings["method"]
    elif "network" in stream_settings:
        transport = stream_settings["network"]
    else:
        raise ValueError(f"Cant't find transport protocol settings")
    if transport == "tcp":
        url["type"] = "tcp"
        parse_transport_tcp_raw(url, stream_settings["tcpSettings"])
    elif transport == "raw":
        url["type"] = "raw"
        parse_transport_tcp_raw(url, stream_settings["rawSettings"])
    elif transport == "xhttp":
        parse_transport_xhttp(url, stream_settings["xhttpSettings"])
    elif transport in ("mkcp", "kcp"):
        parse_transport_mkcp(url, stream_settings["kcpSettings"])
    elif transport == "grpc":
        parse_transport_grpc(url, stream_settings["grpcSettings"])
    elif transport in ("websocket", "ws"):
        parse_transport_web_socket(url, stream_settings["wsSettings"])
    elif transport == "httpupgrade":
        parse_transport_http_upgrade(url, stream_settings["httpupgradeSettings"])
    elif transport == "hysteria":
        parse_transport_hysteria2(url, stream_settings["hysteriaSettings"])
    else:
        raise ValueError(f"Unknown transport: {transport}")


def parse_transport_tcp_raw(url: XrayUrlBuilder, tcp_raw_settings: dict):
    if "header" in tcp_raw_settings:
        header = tcp_raw_settings["header"]
        if "type" in header:
            header_type = header["type"]
            url["headerType"] = header_type
            if header_type == "http":
                if "request" in header:
                    request = header["request"]
                    url.try_set_header("path", "path", request)
                    if "headers" in request:
                        headers = request["headers"]
                        url.try_set_header("host", "Host", headers)
                    url["request"] = request
                if "response" in header:
                    url["response"] = header["response"]
    return


def parse_transport_xhttp(url: XrayUrlBuilder, xhttp_settings: dict):
    url["type"] = "xhttp"
    url.try_set_header("path", "path", xhttp_settings)
    url.try_set_header("host", "host", xhttp_settings)
    url.try_set_header("mode", "mode", xhttp_settings)
    url.try_set_header("extra", "extra", xhttp_settings)
    return


def parse_transport_mkcp(url: XrayUrlBuilder, mkcp_settings: dict):
    url["type"] = "kcp"
    if "header" in mkcp_settings:
        url.try_set_header("headerType", "type", mkcp_settings["header"])
    url.try_set_header("seed", "seed", mkcp_settings)
    url.try_set_header("mtu", "mtu", mkcp_settings)
    url.try_set_header("tti", "tti", mkcp_settings)
    return


def parse_transport_grpc(url: XrayUrlBuilder, grpc_settings: dict):
    url["type"] = "grpc"
    if "serviceName" in grpc_settings:
        if grpc_settings["serviceName"] is not None:
            url["serviceName"] = grpc_settings["serviceName"]
    if "multiMode" in grpc_settings:
        multi_mode = grpc_settings["multiMode"]
        if multi_mode:
            url["mode"] = "multi"
    elif "mode" in grpc_settings:
        multi_mode = grpc_settings["mode"]
        if multi_mode:
            url["mode"] = "multi"
    url.try_set_header("authority", "authority", grpc_settings)
    return


def parse_transport_web_socket(url: XrayUrlBuilder, web_socket_settings: dict):
    url["type"] = "ws"
    url.try_set_header("path", "path", web_socket_settings)
    url.try_set_header("host", "host", web_socket_settings)
    return


def parse_transport_http_upgrade(url: XrayUrlBuilder, http_upgrade_settings: dict):
    url["type"] = "httpupgrade"
    url.try_set_header("path", "path", http_upgrade_settings)
    url.try_set_header("host", "host", http_upgrade_settings)
    return


def parse_transport_hysteria2(url: XrayUrlBuilder, hysteria2_settings: dict):
    url["type"] = "hysteria"
    url.set_p_id(hysteria2_settings["auth"])
    return
