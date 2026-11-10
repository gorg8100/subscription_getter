import os
import json
from typing import Literal, Union, cast
from pathlib import Path

TransformsType = Literal["raw", "x_url2x_json", "x_json2x_url", "clear_x_json"]
ConsolidationType = Literal["json", "url", "cleared_json"]
ReplaceRoutingType = Union[None, Literal["delete", "not-delete"], dict]


def read_settings_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


class DownloadSettings:
    source: str
    file: Path
    type: TransformsType
    replace_routing: Union[None, ReplaceRoutingType] = None

    def __init__(self, data: dict[str, Union[str, Union[None, ReplaceRoutingType], dict]]):
        self.source = cast(str, data["source"])
        self.file = Path(cast(str, data["file"]))
        self.type = cast(TransformsType, data["type"])
        if self.type == "clear_x_json":
            self.replace_routing = cast(Union[None, ReplaceRoutingType], data["replace_routing"])
        return

    def to_dict(self) -> Union[dict[str, str], dict[str, Union[str, dict]]]:
        if self.replace_routing is None:
            return {"source": self.source, "file": str(self.file), "type": self.type}
        else:
            return {"source": self.source, "file": str(self.file), "type": self.type,
                    "replace_routing": self.replace_routing}


class Consolidation:
    sources: dict[str, Literal["url", "json"]]
    type: ConsolidationType
    file: Path
    replace_routing: Union[None, ReplaceRoutingType] = None

    def __init__(self, data: dict[str, Union[str, dict[str, str], Union[None, ReplaceRoutingType]]]):
        self.sources = cast(dict[str, Literal["url", "json"]], data["sources"])
        self.type = cast(ConsolidationType, data["type"])
        self.file = Path(cast(str, data["file"]))
        if "replace_routing" in data:
            self.replace_routing = cast(Union[None, ReplaceRoutingType], data["replace_routing"])
        return

    def to_dict(self) -> dict[str, Union[str, dict[str, str]]]:
        return {"sources": self.sources, "type": self.type, "file": str(self.file)}


class Settings:
    log_file: Path
    headers: dict[str, str]
    sources: dict[str, str]
    downloads: list[DownloadSettings] = None
    consolidations: list[Consolidation] = None

    def __init__(self):
        path = "/etc/sub_get_settings.json"
        if os.path.isfile(path):
            data = read_settings_file(path)
        else:
            data = read_settings_file("settings.json")
        self.log_file = Path(data["log_file"])
        self.headers = data["headers"]
        self.sources = data["sources"]
        if "downloads" in data:
            self.downloads = list(map(DownloadSettings, data["downloads"]))
        if "consolidations" in data:
            self.consolidations = list(map(Consolidation, data["consolidations"]))
        return
