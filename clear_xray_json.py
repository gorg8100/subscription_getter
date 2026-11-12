import json
from typing import Union
from pathlib import Path
from settings_loader import ReplaceRoutingType
from logger_logic import write_log


def clear_xray_json(sub_data: Union[str, list[dict]], replace_routing: Union[None, ReplaceRoutingType],
                    log_file: Path, to_str: bool = True) -> Union[str, list[dict]]:
    if isinstance(sub_data, str):
        json_data = json.loads(sub_data)
    else:
        json_data = sub_data
    for config in json_data:
        try:
            clear_config(config, replace_routing)
        except Exception as err:
            write_log(err, log_file, f"problem with config:\n{json.dumps(config, ensure_ascii=False, indent=2)}")
    if to_str:
        return json.dumps(json_data, indent=4, ensure_ascii=False)
    else:
        return json_data


def clear_config(config: dict, replace_routing: Union[None, ReplaceRoutingType]):
    config.pop("log", None)
    if "inbounds" in config:
        inbound: dict
        for inbound in config["inbounds"]:
            inbound.pop("listen", None)
            if "sniffing" in inbound:
                inbound["sniffing"] = {"enabled": True}
            if "settings" in inbound:
                inbound["settings"] = {"auth": "noauth", "udp": True}

    if "outbounds" in config:
        outbound: dict
        for outbound in config["outbounds"]:
            if "streamSettings" in outbound:
                stream_settings: dict = outbound["streamSettings"]
                stream_settings.pop("finalmask", None)
                stream_settings.pop("sockopt", None)
                stream_settings.pop("tcpSettings", None)
                if not len(stream_settings):
                    outbound.pop("streamSettings", None)
            if "protocol" in outbound:
                if outbound["protocol"] == "freedom":
                    outbound["tag"] = "direct"
                if outbound["protocol"] == "blackhole":
                    outbound["tag"] = "block"
        config["outbounds"] = list(filter(lambda x: x.get("protocol") != "dns", config["outbounds"]))
    config.pop("dns", None)
    if "routing" in config and len(config["routing"].get("balancers", [])):
        routing: dict = config["routing"]
        routing.pop("domainMatcher", None)
        routing["domainStrategy"] = "AsIs"
        routing["rules"] = list(filter(lambda x: "balancerTag" in x, routing["rules"]))
    else:
        if isinstance(replace_routing, dict):
            config["routing"] = replace_routing
        elif replace_routing == "delete":
            config.pop("routing", None)
        elif replace_routing == "not-delete" or replace_routing is None:
            pass
        else:
            raise TypeError("REPLACE_ROUTING must be either 'delete', 'not-delete', json or null")
