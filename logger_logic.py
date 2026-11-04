import traceback
from datetime import datetime
from pathlib import Path


def write_log(err: Exception, log_file_path: Path, remark: str = None):
    trace = traceback.format_exc()
    with log_file_path.open("a", encoding="utf-8") as file:
        err_msg = f"[{datetime.now().replace(microsecond=0)}]{type(err).__name__}: {err}."
        print("=" * len(str(err_msg)), file=file)
        print(err_msg, file=file)
        if remark:
            print("Remark:", remark, file=file)
        print(file=file)
        print(trace, file=file)
    return
