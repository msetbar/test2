import json
import os
import pandas as pd
import sys
from unittest import TestCase
from unittest.mock import call, MagicMock, patch


source_path = os.path.join(os.path.dirname(__file__), "..", "..", "src", "evaluation_framework")
sys.path.append(source_path)
from services.experiment_data_manager import ExperimentDataManager


class TestDownloadRawDataIfNotExists(TestCase):
    def test_happy_path_with_file_not_exists(self):
        # arrange
        dataset_name = "test"
        dataset_version = "v1"
        container_client = MagicMock()

        base_output_dir = "./output"

        experiment_data_manager = ExperimentDataManager(
            dataset_name,
            dataset_version,
            container_client
        )

        expected_raw_dataset_path = f"datasets/{dataset_name}/{dataset_version}/raw"
        expected_local_output_dir = os.path.normpath(os.path.join(base_output_dir, expected_raw_dataset_path))

        with patch("services.experiment_data_manager.os.path.exists") as mock_path_exists, \
                patch("services.experiment_data_manager.os.makedirs") as mock_makedirs:
            mock_path_exists.return_value = False

            # act
            actual_output_path = experiment_data_manager.download_raw_data_if_not_exists(base_output_dir)

        # assert
        assert actual_output_path == expected_local_output_dir
        mock_path_exists.assert_called_once_with(expected_local_output_dir)
        mock_makedirs.assert_called_once_with(expected_local_output_dir, exist_ok=True)
        container_client.download_files.assert_called_once_with(expected_raw_dataset_path, expected_local_output_dir)

    def test_happy_path_with_file_exists(self):
        # arrange
        dataset_name = "test"
        dataset_version = "v1"
        container_client = MagicMock()

        base_output_dir = "./output"

        experiment_data_manager = ExperimentDataManager(
            dataset_name,
            dataset_version,
            container_client
        )

        expected_raw_dataset_path = f"datasets/{dataset_name}/{dataset_version}/raw"
        expected_local_output_dir = os.path.normpath(os.path.join(base_output_dir, expected_raw_dataset_path))

        with patch("services.experiment_data_manager.os.path.exists") as mock_path_exists, \
                patch("services.experiment_data_manager.os.makedirs") as mock_makedirs:
            mock_path_exists.return_value = True

            # act
            actual_output_path = experiment_data_manager.download_raw_data_if_not_exists(base_output_dir)

        # assert
        assert actual_output_path == expected_local_output_dir
        mock_path_exists.assert_called_once_with(expected_local_output_dir)
        mock_makedirs.assert_not_called()
        container_client.download_files.assert_not_called()


class TestDownloadGroundTruthDf(TestCase):
    def test_happy_path_when_file_not_exists(self):
        # arrange
        dataset_name = "test"
        dataset_version = "v1"
        container_client = MagicMock()

        download_content = b"content"
        container_client.download_file.return_value = download_content

        base_output_dir = "./output"

        experiment_data_manager = ExperimentDataManager(
              dataset_name,
              dataset_version,
              container_client
        )

        expected_ground_truth_dataset_path = f"datasets/{dataset_name}/{dataset_version}/ground_truth.csv"
        expected_local_path = os.path.normpath(os.path.join(base_output_dir, expected_ground_truth_dataset_path))

        with patch("services.experiment_data_manager.pd") as mock_pd, \
                patch("services.experiment_data_manager.os.path.exists") as mock_os_path_exists, \
                patch("services.experiment_data_manager._create_parent_folder_path"), \
                patch("services.experiment_data_manager.io.BytesIO") as mock_BytesIO:
            mock_df = MagicMock()
            mock_pd.read_csv.return_value = mock_df
            mock_os_path_exists.return_value = False

            # act
            actual_df = experiment_data_manager.download_ground_truth_df_if_not_exists(
                base_output_dir
            )

        # assert
        assert actual_df == mock_df
        mock_os_path_exists.assert_called_once_with(
            expected_local_path
        )
        container_client.download_file.assert_called_once_with(
            expected_ground_truth_dataset_path
        )
        mock_pd.read_csv.assert_called_once_with(
            mock_BytesIO.return_value
        )
        mock_df.to_csv.assert_called_once_with(
            expected_local_path,
            index=False
        )
        mock_BytesIO.assert_called_once_with(
            download_content
        )

    def test_happy_path_when_path_exists(self):
        # arrange
        dataset_name = "test"
        dataset_version = "v1"
        container_client = MagicMock()

        download_content = b"content"
        container_client.download_file.return_value = download_content

        base_output_dir = "./output"

        experiment_data_manager = ExperimentDataManager(
              dataset_name,
              dataset_version,
              container_client
        )

        expected_ground_truth_dataset_path = f"datasets/{dataset_name}/{dataset_version}/ground_truth.csv"
        expected_local_path = os.path.normpath(os.path.join(base_output_dir, expected_ground_truth_dataset_path))

        with patch("services.experiment_data_manager.pd") as mock_pd, \
                patch("services.experiment_data_manager.os.path.exists") as mock_os_path_exists:
            mock_df = MagicMock()
            mock_pd.read_csv.return_value = mock_df
            mock_os_path_exists.return_value = True

            # act
            actual_df = experiment_data_manager.download_ground_truth_df_if_not_exists(
                base_output_dir
            )

        # assert
        assert actual_df == mock_df
        mock_os_path_exists.assert_called_once_with(
            expected_local_path
        )
        container_client.download_file.assert_not_called()
        mock_pd.read_csv.assert_called_once_with(expected_local_path)
        mock_df.to_csvs.assert_not_called()


class TestUploadExperimentResults(TestCase):
    def test_happy_path(self):
        # arrange
        dataset_name = "test"
        dataset_version = "v1"
        container_client = MagicMock()

        experiment_data_manager = ExperimentDataManager(
            dataset_name,
            dataset_version,
            container_client)

        base_output_dir = "./output"
        experiment_id = "experiment_1"

        blob_content = "test1,test2"
        content = MagicMock()
        content.to_csv.side_effect = [None, blob_content]

        expected_result_path = f"experiments/{dataset_name}/{dataset_version}/{experiment_id}/result.csv"
        expected_local_output_path = os.path.normpath(os.path.join(base_output_dir, expected_result_path))

        with patch("services.experiment_data_manager._create_parent_folder_path") as mock_create_parent_folder_path:
            # act
            experiment_data_manager.upload_experiment_results(base_output_dir, experiment_id, content)

        # assert
        mock_create_parent_folder_path.assert_called_once_with(expected_local_output_path)
        container_client.upload_document.assert_called_once_with(blob_content, expected_result_path)

class TestUploadExperimentConfig(TestCase):
    def test_happy_path(self):
        # arrange
        dataset_name = "test"
        dataset_version = "v1"
        container_client = MagicMock()

        experiment_data_manager = ExperimentDataManager(
            dataset_name,
            dataset_version,
            container_client)

        base_output_dir = "./output"
        experiment_id = "experiment_1"

        content = {"test": "test"}
        stringified_content = json.dumps(content)

        expected_config_path = f"experiments/{dataset_name}/{dataset_version}/{experiment_id}/config.json"
        expected_local_output_path = os.path.normpath(os.path.join(base_output_dir, expected_config_path))

        with patch("services.experiment_data_manager._create_parent_folder_path") as mock_create_parent_folder_path, \
                patch("services.experiment_data_manager.write_data") as mock_write_data:
            # act
            experiment_data_manager.upload_experiment_config(base_output_dir, experiment_id, content)

        # assert
        mock_create_parent_folder_path.assert_called_once_with(expected_local_output_path)
        mock_write_data.assert_called_once_with(stringified_content, expected_local_output_path, "w")
        container_client.upload_document.assert_called_once_with(stringified_content, expected_config_path)


class TestGetCloudExperimentArtifactsPath(TestCase):
    def test_happy_path(self):
        # arrange
        dataset_name = "test_ds"
        dataset_version = "v1"
        experiment_data_manager = ExperimentDataManager(dataset_name, dataset_version, None)

        experiment_id = "sample_id"

        # act
        actual_path = experiment_data_manager.get_cloud_experiment_artifacts_path(experiment_id)

        # assert
        assert actual_path == f"experiments/{dataset_name}/{dataset_version}/{experiment_id}"


class TestGetLocalExperimentArtifactsPath(TestCase):
    def test_happy_path(self):
        # arrange
        dataset_name = "test_ds"
        dataset_version = "v1"
        experiment_data_manager = ExperimentDataManager(dataset_name, dataset_version, None)

        base_output_dir = "./output"
        experiment_id = "sample_id"

        # act
        actual_path = experiment_data_manager.get_local_experiment_artifacts_path(base_output_dir, experiment_id)

        # assert
        assert actual_path == f"./output/experiments/{dataset_name}/{dataset_version}/{experiment_id}"


class TestUpdateLeaderboard(TestCase):
    def test_when_file_not_exists_then_uploads_current_df(self):
        # arrange
        dataset_name = "test_ds"
        dataset_version = "v1"
        container_client = MagicMock()
        container_client.file_exists.return_value = False

        experiment_data_manager = ExperimentDataManager(dataset_name, dataset_version, container_client)

        base_output_dir = "./output"
        experiment_id = "experiment_1"
        df = pd.DataFrame({
            "id": [experiment_id], "metric_1": [1], "metric_2": [1]
        })
        df_stringified = df.to_csv(index=False)

        df.to_csv = MagicMock()
        df.to_csv.side_effect = [
            None,
            df_stringified,
            None
        ]

        expected_leaderboard_path = f"experiments/{dataset_name}/{dataset_version}/leaderboard.csv"
        expected_leaderboard_row_path = f"experiments/{dataset_name}/{dataset_version}/leaderboard_rows/leaderboard_{experiment_id}.csv"

        expected_local_leaderboard_path = os.path.normpath(os.path.join(base_output_dir, expected_leaderboard_path))
        expected_local_leaderboard_rows_path = os.path.normpath(os.path.join(base_output_dir, expected_leaderboard_row_path))

        with patch("services.experiment_data_manager._create_parent_folder_path"):
            # act
            experiment_data_manager.update_leaderboard(base_output_dir, experiment_id, df)

        # assert
        df.to_csv.assert_has_calls([
            call(expected_local_leaderboard_rows_path, index=False),
            call(index=False),
            call(expected_local_leaderboard_path, index=False)
        ])
        container_client.upload_document.assert_has_calls([
            call(df_stringified, expected_leaderboard_row_path),
            call(df_stringified, expected_leaderboard_path)
        ])
        container_client.file_exists.assert_called_once_with(expected_leaderboard_path)

    def test_when_file_exists_then_uploads_concatenated_df(self):
        # arrange
        leaderboard_df = pd.DataFrame({
            "id": ["experiment_0"], "metric_1": [0], "metric_2": [0]
        })
        leaderboard_df_stringified = leaderboard_df.to_csv(index=False)

        dataset_name = "test_ds"
        dataset_version = "v1"
        container_client = MagicMock()
        container_client.file_exists.return_value = True
        container_client.download_file.return_value = str.encode(leaderboard_df_stringified)

        experiment_data_manager = ExperimentDataManager(dataset_name, dataset_version, container_client)

        base_output_dir = "./output"
        experiment_id = "experiment_1"
        df = pd.DataFrame({
            "id": [experiment_id], "metric_1": [1], "metric_2": [1]
        })
        df_stringified = df.to_csv(index=False)

        df.to_csv = MagicMock()
        df.to_csv.side_effect = [
            None,
            df_stringified,
            None
        ]

        updated_leaderboard_df = pd.concat([leaderboard_df, df], axis=0)
        updated_leaderboard_df_stringified = updated_leaderboard_df.to_csv(index=False)
        updated_leaderboard_df.to_csv = MagicMock()
        updated_leaderboard_df.to_csv.side_effect = [
            None,
            updated_leaderboard_df_stringified
        ]

        expected_leaderboard_path = f"experiments/{dataset_name}/{dataset_version}/leaderboard.csv"
        expected_leaderboard_row_path = f"experiments/{dataset_name}/{dataset_version}/leaderboard_rows/leaderboard_{experiment_id}.csv"

        expected_local_leaderboard_path = os.path.normpath(os.path.join(base_output_dir, expected_leaderboard_path))
        expected_local_leaderboard_rows_path = os.path.normpath(os.path.join(base_output_dir, expected_leaderboard_row_path))

        with patch("services.experiment_data_manager._create_parent_folder_path"), \
                patch("services.experiment_data_manager.pd.concat") as mock_pd_concat:
            mock_pd_concat.return_value = updated_leaderboard_df
            # act
            experiment_data_manager.update_leaderboard(base_output_dir, experiment_id, df)

        # assert
        df.to_csv.assert_has_calls([
            call(expected_local_leaderboard_rows_path, index=False),
            call(index=False),
        ])
        container_client.upload_document.assert_has_calls([
            call(df_stringified, expected_leaderboard_row_path),
            call(updated_leaderboard_df_stringified, expected_leaderboard_path)
        ])
        container_client.file_exists.assert_called_once_with(expected_leaderboard_path)
        container_client.download_file.assert_called_once_with(expected_leaderboard_path)
        mock_pd_concat.assert_called_once()
        updated_leaderboard_df.to_csv.assert_has_calls([
            call(expected_local_leaderboard_path, index=False),
            call(index=False)
        ])

