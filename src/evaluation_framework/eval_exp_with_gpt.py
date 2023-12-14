import os
import pandas as pd
from loguru import logger as log
from config.config import config
from evaluation.evaluator import evaluator
from services.experiment_data_manager import ExperimentDataManager
from services.container_client import ContainerClient

os.environ["OPENAI_API_TYPE"] = config.oai_api_type
os.environ["OPENAI_API_BASE"] = config.oai_api_base
os.environ["OPENAI_API_KEY"] = config.oai_api_key
os.environ["OPENAI_API_VERSION"] = config.oai_api_version

dataset_name = "cckm_3700"
dataset_version = "v3"

container_client = ContainerClient.from_credentials(
    config.storage_account_url,
    config.storage_account_container

)

experiment_data_manager = ExperimentDataManager(
    dataset_name,
    dataset_version,
    container_client
)

src_path = __file__.split("evaluation_framework")[0]
_BASE_OUTPUT_DIR = os.path.normpath(os.path.join(src_path, "data"))

experiment_id = '99ea6f7c-4a29-4dce-a743-18d86bc48d3b'
gpt_model = 'gpt-4-32k'

path = experiment_data_manager._build_experiment_result_path(experiment_id)
local_output_path = os.path.normpath(os.path.join(_BASE_OUTPUT_DIR, path))
leaderboard_path = experiment_data_manager._build_leaderboard_path()
local_leaderboard_path = os.path.normpath(os.path.join(_BASE_OUTPUT_DIR, leaderboard_path))

leader_df = pd.read_csv(local_leaderboard_path)
leader_df = leader_df.filter(regex='^(?!Unnamed)')

data_df = pd.read_csv(local_output_path)

log.info(f'Loaded local experiment results for experiment {experiment_id}. Starting evaluation with {gpt_model}...')

data_df = data_df.filter(regex='^(?!Unnamed)')
data_df = evaluator.score_llm_with_gpt(data_df=data_df, gpt=gpt_model)

experiment_data_manager.upload_experiment_results(
    _BASE_OUTPUT_DIR,
    experiment_id,
    data_df
)

if f'{gpt_model}_score' not in leader_df.columns:
    leader_df[f'{gpt_model}_score'] = -1

leader_df.loc[leader_df['experiment_id'] == experiment_id, f'{gpt_model}_score'] = data_df[f'{gpt_model}_score'].mean()
leader_df.loc[leader_df['experiment_id'] == experiment_id, f'{gpt_model}_score>5'] = float((len(data_df[data_df[f'{gpt_model}_score'] >5])/len(data_df))*100)
metric_df = leader_df[leader_df['experiment_id'] == experiment_id].copy()

experiment_data_manager.overwrite_leaderboard_exp(
    _BASE_OUTPUT_DIR,
    experiment_id,
    metric_df
)