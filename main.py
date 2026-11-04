from settings_loader import Settings
from get_sub_data import get_subscription_data
from logger_logic import write_log
from transforms import transform
import json


def main():
    settings = Settings()
    subs_data: dict[str, str] = {}
    for source in settings.sources:
        try:
            subs_data[source] = get_subscription_data(settings.sources[source], settings.headers)
        except Exception as err:
            write_log(err, settings.log_file, f"problem with source: {source}")

    for download in settings.downloads:
        if download.source not in subs_data:
            continue
        try:
            sub_data = subs_data[download.source]
            transform(sub_data, download.type, download.replace_routing, download.file, settings.log_file)
        except Exception as err:
            write_log(err, settings.log_file,
                      f"problem with download:\n{json.dumps(download.to_dict(), ensure_ascii=False, indent=2)}")
    return


if __name__ == "__main__":
    main()
