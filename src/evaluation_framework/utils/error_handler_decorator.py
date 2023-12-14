import pandas as pd
from loguru import logger as log

class ErrorHandlerDecorator(object):
    def __init__(self, df: pd.DataFrame, error_key: str, num_exceptions: int = 5):
        self._df = df
        self._error_key = error_key
        self._num_exceptions = num_exceptions

    def error_handler_decorator(self, func):
        def decorator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                log.warning(f"Error in function {func.__name__}: {str(ex)}")
                index=kwargs.get("index")
                self._df.at[index, self._error_key] += str(ex) + "\n"
                self._num_exceptions -= 1
                if self._num_exceptions <= 0:
                    raise Exception("Error Threshold met... Terminating program.")
        return decorator
