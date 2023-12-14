import json
import io
import os
import pandas as pd
from .container_client import ContainerClient
from utils.fs_utils import write_data
import pathlib


def _create_parent_folder_path(file_path: str):
    parent_path = os.path.dirname(file_path)
    os.makedirs(parent_path, exist_ok=True)


class ExperimentDataManager(object):
    _dataset_name: str
    _dataset_version: str
    _container_client: ContainerClient

    def __init__(
        self,
        dataset_name: str,
        dataset_version: str,
        container_client: ContainerClient,
    ):
        self._dataset_name = dataset_name
        self._dataset_version = dataset_version
        self._container_client = container_client

    def _build_dataset_path(self):
        return f"datasets/{self._dataset_name}/{self._dataset_version}"
    
    def _build_experiment_path(self):
        return f"experiments/{self._dataset_name}/{self._dataset_version}"
    
    def _build_raw_dataset_path(self):
        return f"{self._build_dataset_path()}/raw"
    
    def _build_ground_truth_dataset_path(self):
        return f"{self._build_dataset_path()}/ground_truth.csv"
    
    def _build_experiment_config_path(self, experiment_id: str):
        return f"{self._build_experiment_path()}/{experiment_id}/config.json"
    
    def _build_experiment_result_path(self, experiment_id: str):
        return f"{self._build_experiment_path()}/{experiment_id}/result.csv"
    
    def _build_leaderboard_path(self):
        return f"{self._build_experiment_path()}/leaderboard.csv"
    
    def _build_dashboard_path(self):
        return f"{self._build_experiment_path()}/dashboard.xlsx"

    def _build_leaderboard_row_path(self, experiment_id: str):
        return f"{self._build_experiment_path()}/leaderboard_rows/leaderboard_{experiment_id}.csv"

    def download_raw_data_if_not_exists(self, base_output_dir: str):
        raw_dataset_path = self._build_raw_dataset_path()
        local_output_dir = os.path.normpath(os.path.join(base_output_dir, raw_dataset_path))

        if os.path.exists(local_output_dir):
            print(f"Data already downloaded to path {local_output_dir}. Skipping downloading from blob...")
            return local_output_dir
        
        print("Downloading the files from blob storage...")
        os.makedirs(local_output_dir, exist_ok=True)
        self._container_client.download_files(raw_dataset_path, local_output_dir)
        return local_output_dir

    def download_ground_truth_df_if_not_exists(self, base_output_dir: str):
        ground_truth_dataset_name = self._build_ground_truth_dataset_path()
        local_output_path = os.path.normpath(os.path.join(base_output_dir, ground_truth_dataset_name))
        if os.path.exists(local_output_path):
            print(f"Ground truth data already downloaded to path {local_output_path}. Skipping downloading from blob...")
            return pd.read_csv(local_output_path)

        content = self._container_client.download_file(ground_truth_dataset_name)
        df = pd.read_csv(io.BytesIO(content))

        # create the parent folder of local output path if not exists
        _create_parent_folder_path(local_output_path)
        df.to_csv(local_output_path, index=False)
        return df

    def upload_experiment_results(self, base_output_dir: str, experiment_id: str, content: pd.DataFrame):
        path = self._build_experiment_result_path(experiment_id)
        local_output_path = os.path.normpath(os.path.join(base_output_dir, path))

        print(
            "Uploading Experiment Results to the following paths:\n" +
            f"Local Storage: {local_output_path}\n" + 
            f"Cloud Storage: {path}\n"
        )

        # create the parent folder of local output path if not exists
        _create_parent_folder_path(local_output_path)
        content.to_csv(local_output_path, index=False)
        blob_content = content.to_csv(index=False)

        self._container_client.upload_document(blob_content, path)

    def upload_experiment_config(self, base_output_dir: str, experiment_id: str, content: dict):
        path = self._build_experiment_config_path(experiment_id)
        local_output_path = os.path.normpath(os.path.join(base_output_dir, path))

        print(
            "Uploading Experiment Config to the following paths:\n" +
            f"Local Storage: {local_output_path}\n" + 
            f"Cloud Storage: {path}\n"
        )

        content = json.dumps(content)

        _create_parent_folder_path(local_output_path)
        write_data(content, local_output_path, "w")
        self._container_client.upload_document(content, path)

    def overwrite_leaderboard_exp(self, base_output_dir: str, experiment_id: str, df: pd.DataFrame):
        leaderboard_path = self._build_leaderboard_path()
        leaderboard_row_path = self._build_leaderboard_row_path(experiment_id)

        local_leaderboard_path = os.path.normpath(os.path.join(base_output_dir, leaderboard_path))
        local_leaderboard_rows_path = os.path.normpath(os.path.join(base_output_dir, leaderboard_row_path))

        print(
            "Uploading Leaderboard Results to the following paths:\n" +
            f"Local Storage: {local_leaderboard_path}\n" + 
            f"Cloud Storage: {leaderboard_path}\n" +
            f"Local Storage (row): {local_leaderboard_rows_path}\n" + 
            f"Cloud Storage (row): {leaderboard_row_path}\n"
        )

        _create_parent_folder_path(local_leaderboard_rows_path)
        _create_parent_folder_path(local_leaderboard_path)

        # save rows
        df.to_csv(local_leaderboard_rows_path, index=False)
        blob_content = df.to_csv(index=False)
        self._container_client.upload_document(blob_content, leaderboard_row_path)

        # compute the leaderboard
        # check if file exists in the cloud
        if not self._container_client.file_exists(leaderboard_path):
            df.to_csv(local_leaderboard_path, index=False)
            self._container_client.upload_document(blob_content, leaderboard_path)
            return

        current_leaderboard_content = self._container_client.download_file(leaderboard_path)
        current_leaderboard_df = pd.read_csv(io.BytesIO(current_leaderboard_content))

        for col in df.columns:
            if col not in current_leaderboard_df.columns:
                current_leaderboard_df[col] = -1

        condition = (current_leaderboard_df['experiment_id'] == experiment_id)
        current_leaderboard_df.loc[condition, :] = df[df['experiment_id'] == experiment_id].astype(current_leaderboard_df.dtypes)
        current_leaderboard_df.to_csv(local_leaderboard_path, index=False)
        leaderboard_blob_content = current_leaderboard_df.to_csv(index=False)
        self._container_client.upload_document(leaderboard_blob_content, leaderboard_path)

    def update_leaderboard(self, base_output_dir: str, experiment_id: str, df: pd.DataFrame):
        leaderboard_path = self._build_leaderboard_path()
        leaderboard_row_path = self._build_leaderboard_row_path(experiment_id)

        local_leaderboard_path = os.path.normpath(os.path.join(base_output_dir, leaderboard_path))
        local_leaderboard_rows_path = os.path.normpath(os.path.join(base_output_dir, leaderboard_row_path))

        print(
            "Uploading Leaderboard Results to the following paths:\n" +
            f"Local Storage: {local_leaderboard_path}\n" + 
            f"Cloud Storage: {leaderboard_path}\n" +
            f"Local Storage (row): {local_leaderboard_rows_path}\n" + 
            f"Cloud Storage (row): {leaderboard_row_path}\n"
        )

        _create_parent_folder_path(local_leaderboard_rows_path)
        _create_parent_folder_path(local_leaderboard_path)

        # save rows
        df.to_csv(local_leaderboard_rows_path, index=False)
        blob_content = df.to_csv(index=False)
        self._container_client.upload_document(blob_content, leaderboard_row_path)

        # compute the leaderboard
        # check if file exists in the cloud
        if not self._container_client.file_exists(leaderboard_path):
            df.to_csv(local_leaderboard_path, index=False)
            self._container_client.upload_document(blob_content, leaderboard_path)
            return

        current_leaderboard_content = self._container_client.download_file(leaderboard_path)
        current_leaderboard_df = pd.read_csv(io.BytesIO(current_leaderboard_content))

        # join the data frames
        output_df = pd.concat([current_leaderboard_df, df], axis=0)
        output_df.to_csv(local_leaderboard_path, index=False)
        leaderboard_blob_content = output_df.to_csv(index=False)
        self._container_client.upload_document(leaderboard_blob_content, leaderboard_path)


        dashboard_template_xlt_file_path = (pathlib.Path(__file__).parent
                / "dashboard.xlsx"
            )
        
        dashboard_local_file = (pathlib.Path(local_leaderboard_path).parent
                / "dashboard.xlsx"
            )
        
        # clone the template dashboard
        with open(str(dashboard_template_xlt_file_path), 'rb') as dashboard_template_file:
            with open(str(dashboard_local_file), 'wb') as dashboard_file:
                dashboard_file.write(dashboard_template_file.read())

        # overwrite the leaderboard sheet
        self.write_excel(str(dashboard_local_file), 'leaderboard', output_df)

        with open(str(dashboard_local_file), "rb") as dashboard_file:
            content = dashboard_file.read()
            dashboard_path = self._build_dashboard_path()
            self._container_client.upload_document(content, dashboard_path)

    def get_cloud_experiment_artifacts_path(self, experiment_id: str):
        return f"{self._build_experiment_path()}/{experiment_id}"
    
    def get_local_experiment_artifacts_path(self, base_output_dir: str, experiment_id: str):
        return f"{base_output_dir}/{self._build_experiment_path()}/{experiment_id}"
    
    def write_excel(self, filename: str, sheetname: str, dataframe: pd.DataFrame):
        with pd.ExcelWriter(filename, engine='openpyxl', mode="a", if_sheet_exists="replace") as writer: 
            try:
                dataframe.to_excel(writer, sheet_name=sheetname, index=False)
            except Exception as ex:
                print(f"Could not write the dashboard: {ex}")
                
