import os
from loguru import logger as log
from services.file_manager import FileManager
from services.snowflake_client import SnowflakeClient
from urllib.parse import quote_plus
import argparse


_OUTPUT_FOLDER_PATH = os.path.join(os.path.dirname(__file__), "output")


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sub-folder",
        dest="sub_folder",
        type=str,
        help="The sub-folder to write the data to under the ./output folder.",
        required=True,
    )
    parser.add_argument(
        "--article-number-key",
        dest="article_number_key",
        type=str,
        help="The article number key.",
        default="ArticleNumber"
    )
    return parser.parse_args()


def main(
    sub_folder: str,
    article_number_key: str
):
    # constructing the output folder path (sub-folder)
    sub_folder_output_folder_path = os.path.join(_OUTPUT_FOLDER_PATH, sub_folder)
    os.makedirs(sub_folder_output_folder_path, exist_ok=True)

    snowflake_client = SnowflakeClient()
    cckm_results = snowflake_client.get_cckm_data()
    file_names = [quote_plus(f"{elem[article_number_key]}.json") for i, elem in enumerate(cckm_results)]
    log.info(f"Length of files {len(file_names)}... Length of distinct files {len(set(file_names))}")

    log.info("Writing the objects to disk...")
    FileManager.save_list_of_objects(
        [result for result in cckm_results],
        file_names,
        sub_folder_output_folder_path)


if __name__ == "__main__":
    args = _get_args()
    sub_folder = args.sub_folder
    article_number_key = args.article_number_key

    log.info("Starting program to get the CCKM results...")
    main(sub_folder, article_number_key)
    log.info("Finishing program....")
