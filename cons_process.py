from typing import Literal, Union
from pathlib import Path
import json
from settings_loader import ConsolidationType, ReplaceRoutingType, Consolidation
from xray_url2xray_json import xray_url2xray_json
from xray_json2_xray_url import xray_json2_xray_url
from clear_xray_json import clear_xray_json
from logger_logic import write_log


def consolidation_process(subs_data: list[tuple[Literal["url", "json"], str]],
                          log_file: Path, consolidation: Consolidation):
    accumulator = []
    for cons_type, sub_data in subs_data:
        try:
            acc_update(accumulator, cons_type, sub_data, consolidation.type, log_file, consolidation.replace_routing)
        except Exception as err:
            write_log(err, log_file,
                      f"problem in consolidation:"
                      f" {json.dumps(consolidation.to_dict(), ensure_ascii=False, indent=2)}")
    if consolidation.type in ("json", "cleared_json"):
        data = json.dumps(accumulator, indent=2, ensure_ascii=False)
    elif consolidation.type == "url":
        data = "\n".join(accumulator)
    else:
        raise
    consolidation.file.write_text(data, encoding="utf-8")


def acc_update(accumulator: list, cons_type: Literal["url", "json"], sub_data: str,
               out_type: ConsolidationType, log_file: Path, replace_routing: Union[None, ReplaceRoutingType]):
    if cons_type == 'url':
        if out_type == "json":
            accumulator += xray_url2xray_json(sub_data, log_file, False)
        elif out_type == "url":
            accumulator += sub_data.split("\n")
        elif out_type == "cleared_json":
            jsn = xray_url2xray_json(sub_data, log_file, False)
            accumulator += clear_xray_json(jsn, replace_routing, log_file, False)
        else:
            raise ValueError(f"Unknown type: {out_type}")
    elif cons_type == "json":
        if out_type == "json":
            accumulator += json.loads(sub_data)
        elif out_type == "url":
            accumulator += xray_json2_xray_url(sub_data, log_file, False)
        elif out_type == "cleared_json":
            accumulator += clear_xray_json(sub_data, replace_routing, log_file, False)
        else:
            raise ValueError(f"Unknown type: {out_type}")
    else:
        raise ValueError(f"Unknown source type: {cons_type}")
