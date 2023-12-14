import time


def time_usage(func):
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        retval = func(*args, **kwargs)
        toc = time.perf_counter()
        return retval, toc - tic
    return wrapper
