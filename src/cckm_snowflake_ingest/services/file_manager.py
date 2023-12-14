import json
import os
from tqdm import tqdm


class FileManager(object):
    @staticmethod
    def save_list_of_objects(objs: list, file_names: list, output_dir: str):
        assert len(objs) == len(file_names)

        os.makedirs(output_dir, exist_ok=True)
        for obj, file_name in tqdm(zip(objs, file_names), total=len(objs)):
            output_file_path = os.path.join(output_dir, file_name)
            with open(output_file_path, "w") as f:
                json.dump(obj, f)
