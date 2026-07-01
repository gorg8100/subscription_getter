import importlib.util
import sys
import os


def load_settings(custom_path: str = None):
    custom_path = os.environ.get("SUBSCRIPTION_GETTER_SETTINGS_FILE_PATH", custom_path)
    if custom_path and os.path.isfile(custom_path):
        try:
            spec = importlib.util.spec_from_file_location("settings", custom_path)
            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)
            sys.modules["settings"] = settings
        except Exception as err:
            raise RuntimeError(f"problems loading settings from {custom_path}. {err}")
        return settings
    else:
        import settings
        return settings
