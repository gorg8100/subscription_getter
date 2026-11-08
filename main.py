from settings_loader import Settings
from get_sub_data import get_subscription_data
from logger_logic import write_log
from transforms import transform
from cons_process import consolidation_process
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

    for consolidation in settings.consolidations:
        cons_subs_data = []
        for source in consolidation.sources:
            if source in subs_data:
                cons_subs_data.append((consolidation.sources[source], subs_data[source]))
        if not cons_subs_data:
            continue
        try:
            consolidation_process()
        except Exception as err:
            write_log(err, settings.log_file,
                      f"problem with consolidation:"
                      f" {json.dumps(consolidation.to_dict(), ensure_ascii=False, indent=2)}")
    return


if __name__ == "__main__":
    main()
