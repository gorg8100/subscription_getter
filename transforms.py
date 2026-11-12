from settings_loader import TransformsType, ReplaceRoutingType
from typing import Union
from pathlib import Path
from clear_xray_json import clear_xray_json
from xray_json2_xray_url import xray_json2_xray_url
from xray_url2xray_json import xray_url2xray_json


def transform(sub_data: str, transform_type: TransformsType, replace_routing: Union[None, ReplaceRoutingType],
              file_paths: list[Path], log_file: Path):
    res_data = transforms_routing(sub_data, transform_type, replace_routing, log_file)
    for file_path in file_paths:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(res_data, encoding="utf-8")
    return


def transforms_routing(sub_data: str, transform_type: TransformsType,
                       replace_routing: Union[None, ReplaceRoutingType], log_file: Path) -> str:
    if transform_type == "raw":
        return sub_data
    elif transform_type == "x_url2x_json":
        return xray_url2xray_json(sub_data, log_file)
    elif transform_type == "x_json2x_url":
        return xray_json2_xray_url(sub_data, log_file)
    elif transform_type == "clear_x_json":
        return clear_xray_json(sub_data, replace_routing, log_file)
    else:
        raise ValueError(f"unknown transform type: {transform_type}")
