import functools
from settings import DATA_LOGS_PATH
import sys
from datetime import datetime
if sys.version_info.minor < 10:
    from typing import TypeVar, Callable, Literal
    from typing_extensions import ParamSpec
else:
    from typing import TypeVar, Callable, Literal, ParamSpec


def write_log(record_type: Literal["Error", "RepeatError"], error: Exception, func_name: str):
    try:
        with open(DATA_LOGS_PATH, "a") as file:
            print(
                f"[{datetime.now().replace(microsecond=0)}][{record_type}]{type(error).__name__}: {error}. In {func_name}.",
                file=file)
    except Exception as err:
        raise RuntimeError(f"error when opening a file to write to the log at the path {DATA_LOGS_PATH}. {err}")


F_Spec = ParamSpec("F_Spec")
F_Return = TypeVar("F_Return")


def logg(repeat: int = 1) -> Callable[[Callable[F_Spec, F_Return]], Callable[F_Spec, F_Return]]:
    if repeat < 1:
        raise RuntimeError('Repeat must be greater than 0')

    def decorator_logg(func: Callable[F_Spec, F_Return]) -> Callable[F_Spec, F_Return]:
        @functools.wraps(func)
        def wrapper(*args: F_Spec.args, **kwargs: F_Spec.kwargs) -> F_Return:
            error = None
            for i in range(repeat):
                try:
                    original_result = func(*args, **kwargs)
                    return original_result
                except Exception as err:
                    if i != repeat - 1:
                        write_log(record_type="RepeatError", error=err, func_name=func.__name__)
                    else:
                        error = err
            write_log(record_type="Error", error=error, func_name=func.__name__)
            raise error

        return wrapper

    return decorator_logg
