def write_data(data, path: str, mode: str="wb"):
     with open(path, mode) as f:
        f.write(data)
