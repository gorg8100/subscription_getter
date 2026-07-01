from logger_logic import logg
import json
from settings import REPLACE_ROUTING, CLEARED_DATA_FILE_PATH


@logg()
def clear_config(config: dict):
    config.pop("log", None)
    if "inbounds" in config:
        inbound: dict
        for inbound in config["inbounds"]:
            inbound.pop("listen", None)
            if "sniffing" in inbound:
                inbound["sniffing"] = {"enabled": True}
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
        if isinstance(REPLACE_ROUTING, dict):
            config["routing"] = REPLACE_ROUTING
        elif REPLACE_ROUTING == "delete":
            config.pop("routing", None)
        elif REPLACE_ROUTING != "not-delete":
            raise TypeError("REPLACE_ROUTING must be either 'delete', 'not-delete' or json")


@logg()
def clear_data(data: str):
    json_data = json.loads(data)
    # print(json.dumps(json_data[5], indent=4, ensure_ascii=False))
    # clear_config(json_data[5])
    # print("===========")
    # print(json.dumps(json_data[5], indent=4, ensure_ascii=False))
    for config in json_data:
        clear_config(config)
    write_json_data(json_data)


@logg()
def write_json_data(json_data):
    with open(CLEARED_DATA_FILE_PATH, 'w', encoding="utf-8") as f:
        f.write(json.dumps(json_data, indent=4, ensure_ascii=False))


# with open('data.json', "r", encoding="utf-8") as f:
#    templates = f.read()
# clear_data(templates)
