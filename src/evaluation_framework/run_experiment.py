import concurrent
import os
from uuid import uuid4
from requests import Response
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import datetime
import json
from loguru import logger as log
import numpy as np
import pandas as pd
from evaluation.evaluator import evaluator
from config.config import config
from services.container_client import ContainerClient
from services.domain_config_manager import DomainConfigManager
from services.domain_services_request_manager import DomainServicesRequestManager
from services.experiment_data_manager import ExperimentDataManager
from utils.error_handler_decorator import ErrorHandlerDecorator
from utils.time_usage_decorator import time_usage

now = datetime.datetime.now()
curr_datetime = now.strftime("%Y%m%d-%H%M%S")

## EXPERIMENT CONSTANTS

src_path = __file__.split("evaluation_framework")[0]
_BASE_OUTPUT_DIR = os.path.normpath(os.path.join(src_path, "data"))

# Column keys used in groundtruth + experiment result CSVs

_CODE_BASE_VERSION_FIELD = "code_base_version"
_CONFIG_FIELD = "config"
_DATE_FIELD = "date"
_DATASET_NAME_FIELD = "dataset"
_DATASET_VERSION_FIELD = "version"
_ENVIRONMENT_FIELD = "environment"
_EXPERIMENT_ID_FIELD = "experiment_id"
_NOTES_FIELD = "notes"
_NUMBER_OF_ERRORS_FIELD = "number_of_errors"

_MEAN_SIMILARITY_SEARCH_TIME_SEC = 'similarity_search_time_in_sec_mean'
_MEAN_CHAT_QUERY_TIME_SEC = 'chat_query_time_in_sec_mean'
_75TH_PERCENTILE_SIMILARITY_SEARCH_TIME_SEC = 'similarity_search_time_in_sec_75th_percentile'
_75TH_PERCENTILE_CHAT_QUERY_TIME_SEC = 'chat_query_time_in_sec_75th_percentile'
_MEDIAN_SIMILARITY_SEARCH_TIME_SEC = 'similarity_search_time_in_sec_median'
_MEDIAN_CHAT_QUERY_TIME_SEC = 'chat_query_time_in_sec_median'

_ERROR_KEY = "run_errors"

_GROUNDTRUTH_QUESTION_KEY = "bcss_question"
_GENERATED_ANSWER_KEY = "generated_answer"
_INIT_CHUNKS_KEY = "init_chunks"
_RERANKER_CHUNKS_KEY = "reranker_chunks"
_DOC_CATEGORY_1_KEY = "BW_TXNMY_GRP_1"
_DOC_CATEGORY_2_KEY = "BW_TXNMY_GRP_2"
_DOC_CATEGORY_3_KEY = "BW_TXNMY_GRP_3"

# Keys to extract information from DomainServices API JSON responses
_RESPONSE_KEY = 'response'
_CITATIONS_KEY = 'citations'
_PAGE_CONTENT_KEY = 'page_content'
_METADATA_KEY = 'metadata'
_ARTICLE_NUMBER_KEY = 'ArticleNumber'

## USER INPUT: Define config + configurable options for experiment runs
ingest_data = False
env = "dev"
domain = "user_mn5253_qcconcat_1"
domain_config_version = "2023-11-28"
metrics_to_calculate = ["chunks", "rouge", "bert"]
run_chat = True # Set to False to disable chat step
batch_size = 5
concurrency = 3
exception_limit = 5
experiment_notes = ""

# domain config variables
should_upload_domain_config = False

# setting up the dataset
dataset_name = "test_cckm_5"
dataset_version = "v2"

code_base_version = "automation"  # don't change unless we actually upgraded to something new or are doing isolated testing for new codebase
env = "web" if env == "prod" else env  # don't change this
experiment_id = str(uuid4())

## Experiment logic

print(f"Starting experiment run {experiment_id}...")

# init the dependencies
domain_services_request_manager = DomainServicesRequestManager(
    domain,
    domain_config_version,
    env,
    code_base_version
)
domain_config_manager = DomainConfigManager(
    domain_services_request_manager,
    domain,
    domain_config_version
)
container_client = ContainerClient.from_credentials(
    config.storage_account_url,
    config.storage_account_container
)
experiment_data_manager = ExperimentDataManager(
    dataset_name,
    dataset_version,
    container_client
)
# upload the config if boolean set
if should_upload_domain_config:
    log.info('Uploading/updating domain config...')
    res = domain_config_manager.put_domain_config()
    res.raise_for_status()

domain_params = domain_config_manager.get_domain_config().json()
k_init_retrieval = domain_params.get("k_milvus", 10)
is_reranker_enabled = domain_params.get("reranker_class_name", None) is not None and domain_params.get("k_reranker", 1000) < domain_params.get("k_milvus", 0)

def send_post_request_with_files(post_files: list[str]) -> tuple[Response, int]:
    files_post_list = []
    files_to_close = []
    for el in post_files:
        opened_file = open(fr"{documents_dir_location}/{el}", "rb")
        files_post_list.append((el, opened_file))
        files_to_close.append(opened_file)

    res = domain_services_request_manager.upload_document(files_post_list)
    for entry in files_to_close:
        entry.close()
    return res, len(post_files)

def _try_get_failed_files(response: Response, files: list[str]):
    """
    Here the response should not indicate success.
    We ned to try to get the failed files and return from the function
    """
    log.warning(f"There was an error processing the request: {response.content}")
    if response.status_code == 206: # partial commit and has the failed files key
        json_content = response.json()
        failed_files = [file['file'] for file in json_content['failed']]
        return failed_files
    else:
        return files

# Ingest documents
if ingest_data:
    failed_files = []

    documents_dir_location = experiment_data_manager.download_raw_data_if_not_exists(_BASE_OUTPUT_DIR)
    local_files = os.listdir(documents_dir_location)
    pbar_total = len(local_files)
    with tqdm(total=pbar_total, desc=rf"Uploading {domain} documents..") as pbar:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            files = []
            future_files_mapping = {}
            for _file in local_files:
                files.append(_file)
                if len(files) % batch_size == 0:
                    future = executor.submit(send_post_request_with_files, files)
                    futures.append(future)
                    future_files_mapping[future] = files
                    files = []
            if len(files) > 0:
                future = executor.submit(send_post_request_with_files, files)
                futures.append(future)
                future_files_mapping[future] = files
            for future in concurrent.futures.as_completed(futures):
                response, files_size = future.result()
                if response.status_code != 200:
                    files = future_files_mapping[future]
                    failed_files += _try_get_failed_files(response, files)
                pbar.update(files_size)

    log.info("Finished processing files.\n" +
             f"Number of files unprocessed: {len(failed_files)};\n" +
             f"Percent of files unprocessed: {round(len(failed_files)/len(local_files), 4)};")

## Note: the below is to get the initial chunks from a simple similarity search, without 
groundtruth_df = experiment_data_manager.download_ground_truth_df_if_not_exists(
    _BASE_OUTPUT_DIR
)
groundtruth_df[_ERROR_KEY] = ""
questions_to_test = groundtruth_df[_GROUNDTRUTH_QUESTION_KEY]
decorator = ErrorHandlerDecorator(groundtruth_df, _ERROR_KEY, exception_limit)

@time_usage
@decorator.error_handler_decorator
def _perform_similarity_search_request(query: str, index: int):
    sim_search_response = domain_services_request_manager.similarity_search(query, k_init_retrieval)
    sim_search_response.raise_for_status()

    chunks_per_response = []
    for _, citation in enumerate(sim_search_response.json()[_RESPONSE_KEY]):
        chunks_per_response.append((citation[0][_PAGE_CONTENT_KEY], os.path.basename(citation[0][_METADATA_KEY][_ARTICLE_NUMBER_KEY]),(citation[2])))
    groundtruth_df.at[index, _INIT_CHUNKS_KEY] = str(chunks_per_response)

@time_usage
@decorator.error_handler_decorator
def _perform_chat_request(query: str, index: int):
    llm_response = domain_services_request_manager.chat(query)
    llm_response.raise_for_status()
    groundtruth_df.at[index, _GENERATED_ANSWER_KEY] = llm_response.json()[_RESPONSE_KEY]

    chunks_per_response = []
    for citation in llm_response.json()[_CITATIONS_KEY]:
        chunks_per_response.append((citation[_PAGE_CONTENT_KEY], os.path.basename(citation[_METADATA_KEY][_ARTICLE_NUMBER_KEY])))
    groundtruth_df.at[index, _RERANKER_CHUNKS_KEY] = str(chunks_per_response)

def _augment_query_with_groundtruth_categories_optional(query: str, should_augment: bool = False, doc_category_1: str = "", doc_category_2: str = "", doc_category_3: str = ""):
    if not should_augment:
        return query
    
    # augmented_query = doc_category_1 + " " + query # exp 1 - complete
    # augmented_query = doc_category_1 + " " + doc_category_2 + query # exp 2 - complete
    # augmented_query = doc_category_1 + " " + doc_category_2 + " " + doc_category_3 + " " + query # exp 3 - complete
    augmented_query = query + " " + doc_category_1 + " " + doc_category_2 + " " + doc_category_3 # exp 4 - complete, best results so far
    # augmented_query = query + " " + doc_category_1 + " " + doc_category_2 # exp 5 - complete
    # augmented_query = query + " " + doc_category_1 # exp 6 - complete
    # augmented_query = doc_category_3 + " " + query # exp 7 - complete
    # augmented_query = query + " " + doc_category_3 # exp 8 - complete
    return augmented_query

# Call similarity search endpoint to get initial chunks retrieved, which we need to compute
# full evaluation metrics at each stage of the experiment pipeline.
# Note that this is also retrieved as a part of the chat endpoint, but their current API contract
# does not expose those as output. For time purposes to enable current experimentation workflow
# without making a PR to update DomainServices API contracts, we're taking this approach here -
# this is still a possible next step on our radar as well as updating the contract to do a similarity 
# search and rerank the results (as we want to be able to evaluate each step separately).
print("Sending questions to similarity search endpoint...")
number_of_questions_to_test = len(questions_to_test)
elapsed_time_similarity_search = []
with tqdm(total=number_of_questions_to_test, desc=rf"Running {domain} queries against vector DB..") as pbar:
    groundtruth_df[_INIT_CHUNKS_KEY] = "" 
    for index, row in groundtruth_df.iterrows():
        query = row[_GROUNDTRUTH_QUESTION_KEY]
        groundtruth_df[_GENERATED_ANSWER_KEY] = ""

        # Update for task 116785
        doc_category_1 = row[_DOC_CATEGORY_1_KEY] if pd.notna(row[_DOC_CATEGORY_1_KEY]) else "" 
        doc_category_2 = row[_DOC_CATEGORY_2_KEY] if pd.notna(row[_DOC_CATEGORY_2_KEY]) else ""
        doc_category_3 = row[_DOC_CATEGORY_3_KEY] if pd.notna(row[_DOC_CATEGORY_3_KEY]) else ""

        # This will currently not augment the queries with the document categories and run experiments as-is
        # Pass in query, True, doc categories to run query/category concatenation experiments
        augmented_query = _augment_query_with_groundtruth_categories_optional(query) 
        
        _, elapsed_time = sim_search_response = _perform_similarity_search_request(query=augmented_query, index=index)
        elapsed_time_similarity_search.append(elapsed_time)
        pbar.update()

elapsed_time_similarity_search_np = np.array(elapsed_time_similarity_search)
elapsed_time_similarity_search_mean = elapsed_time_similarity_search_np.mean()
elapsed_time_similarity_search_median = np.median(elapsed_time_similarity_search_np)
elapsed_time_similarity_search_q3 = np.percentile(elapsed_time_similarity_search_np, [75])[0]

# There is no separate reranker endpoint - TODO: add to API? add backlog

# # Send questions to chat endpoint and store responses + citations
if run_chat:
    print("Sending questions to chat endpoint...")
    pbar_chat_len = len(questions_to_test)
    elapsed_time_chat_query = []
    with tqdm(total=pbar_chat_len, desc=rf"Running {domain} queries against LLM chat..") as pbar:
        groundtruth_df[_RERANKER_CHUNKS_KEY] = "" 
        groundtruth_df[_GENERATED_ANSWER_KEY] = "" 
        for index, row in groundtruth_df.iterrows():
            query = row[_GROUNDTRUTH_QUESTION_KEY]

            doc_category_1 = row[_DOC_CATEGORY_1_KEY] if pd.notna(row[_DOC_CATEGORY_1_KEY]) else "" 
            doc_category_2 = row[_DOC_CATEGORY_2_KEY] if pd.notna(row[_DOC_CATEGORY_2_KEY]) else ""
            doc_category_3 = row[_DOC_CATEGORY_3_KEY] if pd.notna(row[_DOC_CATEGORY_3_KEY]) else ""
            
            # This will currently not augment the queries with the document categories and run experiments as-is
            # Pass in query, True, doc categories to run query/category concatenation experiments
            augmented_query = _augment_query_with_groundtruth_categories_optional(query) 

            _, elapsed_time = _perform_chat_request(query=augmented_query, index=index)
            elapsed_time_chat_query.append(elapsed_time)
            pbar.update()

    elapsed_time_chat_query_np = np.array(elapsed_time_chat_query)
    elapsed_time_chat_query_mean = elapsed_time_chat_query_np.mean()
    elapsed_time_chat_query_median = np.median(elapsed_time_chat_query_np)
    elapsed_time_chat_query_q3 = np.percentile(elapsed_time_chat_query_np, [75])[0]

evaluation_df = groundtruth_df[groundtruth_df[_ERROR_KEY] == ""].copy()
num_success_rows = len(evaluation_df)
total_rows = len(groundtruth_df)
number_of_errors = total_rows - num_success_rows
print(f"Total number of errors: {number_of_errors}; Total Rows: {total_rows}")

# To disable reranker/initial chunks scoring, send the column name as ""
data_df, metrics_df = evaluator.calculate_metrics(
    dataframe=evaluation_df,
    metrics=metrics_to_calculate,
    is_reranker_enabled=is_reranker_enabled, 
    reranker_chunks = _RERANKER_CHUNKS_KEY, 
    init_chunks=_INIT_CHUNKS_KEY
    )

print("Saving results to storage and locally...\n\n")
# adding the experiment id to the metrics df
metrics_df.insert(0, _EXPERIMENT_ID_FIELD, [experiment_id])
metrics_df[_CONFIG_FIELD] = [json.dumps(domain_params)]
metrics_df[_NUMBER_OF_ERRORS_FIELD] = number_of_errors
metrics_df[_DATE_FIELD] = now
metrics_df[_DATASET_NAME_FIELD] = [dataset_name]
metrics_df[_DATASET_VERSION_FIELD] = [dataset_version]
metrics_df[_NOTES_FIELD] = [experiment_notes]
metrics_df[_ENVIRONMENT_FIELD] = [env]
metrics_df[_CODE_BASE_VERSION_FIELD] = [code_base_version]
metrics_df[_MEAN_SIMILARITY_SEARCH_TIME_SEC] = [elapsed_time_similarity_search_mean]
metrics_df[_MEDIAN_SIMILARITY_SEARCH_TIME_SEC] = [elapsed_time_similarity_search_median]
metrics_df[_75TH_PERCENTILE_SIMILARITY_SEARCH_TIME_SEC] = [elapsed_time_similarity_search_q3]

if run_chat:
    metrics_df[_MEAN_CHAT_QUERY_TIME_SEC] = [elapsed_time_chat_query_mean]
    metrics_df[_MEDIAN_CHAT_QUERY_TIME_SEC] = [elapsed_time_chat_query_median]
    metrics_df[_75TH_PERCENTILE_CHAT_QUERY_TIME_SEC] = [elapsed_time_chat_query_q3]

experiment_data_manager.upload_experiment_config(
    _BASE_OUTPUT_DIR,
    experiment_id,
    domain_params
)
experiment_data_manager.upload_experiment_results(
    _BASE_OUTPUT_DIR,
    experiment_id,
    data_df
)
experiment_data_manager.update_leaderboard(
    _BASE_OUTPUT_DIR,
    experiment_id,
    metrics_df
)
