import os
import sys
from unittest import TestCase
from unittest.mock import MagicMock, patch


source_path = os.path.join(os.path.dirname(__file__), "..", "..", "src", "evaluation_framework")
sys.path.append(source_path)
from services.container_client import ContainerClient


class TestFileExists(TestCase):
    def test_happy_path(self):
        # arrange
        blob_client = MagicMock()
        blob_client.exists.return_value = True
        azure_container_client = MagicMock()
        azure_container_client.get_blob_client.return_value = blob_client

        file_path = "./file/path"
        container_client = ContainerClient(azure_container_client)

        # act
        result = container_client.file_exists(file_path)

        # assert
        assert result == True
        azure_container_client.get_blob_client.asset_called_once_with(file_path)



class TestUploadDocuments(TestCase):
    def test_happy_path(self):
        # arrange
        azure_container_client = MagicMock()

        bytes = b'test'
        path = './test/path'

        container_client = ContainerClient(azure_container_client)

        # act
        container_client.upload_document(bytes, path)

        # assert
        azure_container_client.upload_blob.assert_called_once_with(
            path,
            bytes,
            overwrite=True
        )

class TestDownloadFile(TestCase):
    def test_happy_path(self):
        # arrange
        azure_container_client = MagicMock()
        path = "./test/path"

        download_content = b'test'
        download_response = MagicMock()
        download_response.readall.return_value = download_content

        azure_container_client.download_blob.return_value = download_response
        container_client = ContainerClient(azure_container_client)

        # act
        actual_content = container_client.download_file(path)

        # assert
        assert actual_content == download_content
        azure_container_client.download_blob.assert_called_once_with(
            path
        )

class TestDownloadFiles(TestCase):
    def test_with_documents_listed_then_downloads_multiple_items(self):
        # arrange
        azure_container_client = MagicMock()

        file1 = MagicMock()
        file1.name = "test/path/file1.html"
        file2 = MagicMock()
        file2.name = "test/path/file2.txt"
        file3 = MagicMock()
        file3.name = "test/path"
        azure_container_client.list_blobs.return_value = [
            file1,
            file2,
            file3
        ]

        def download_blob_side_effect(path: str):
            res = MagicMock()
            res.readall.return_value = b'{path}'
            return res

        azure_container_client.download_blob.side_effect = download_blob_side_effect

        base_path = 'test/path'
        output_dir = "./output"

        container_client = ContainerClient(azure_container_client)

        expected_result = [
            os.path.join(output_dir, "file1.html"),
            os.path.join(output_dir, "file2.txt")
        ]

        # act
        with patch("services.container_client.write_data"):
            result = container_client.download_files(base_path, output_dir)

        # assert
        assert result == expected_result

    def test_with_documents_not_listed_then_no_downloads(self):
        # arrange
        azure_container_client = MagicMock()
        azure_container_client.list_blobs.return_value = []

        base_path = 'test/path'
        output_dir = "./output"

        container_client = ContainerClient(azure_container_client)

        expected_result = []

        # act
        result = container_client.download_files(base_path, output_dir)

        # assert
        assert result == expected_result
