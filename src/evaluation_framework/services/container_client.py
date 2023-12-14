from multiprocessing.pool import ThreadPool
import os
from typing import Optional, Union
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient as AzureContainerClient
from utils.fs_utils import write_data


_CONCURRENT_THREADS = 10


class ContainerClient(object):
    container_client: AzureContainerClient
    
    def __init__(self, container_client: AzureContainerClient):
        self.container_client = container_client

    def _list_documents(self, base_path: str):
        files = self.container_client.list_blobs(base_path)
        return [file.name for file in files if os.path.splitext(file.name)[1]] # listing only the files and not folders

    def _download_and_save_file(self, path: str, output_dir: str):
        _, file_name = os.path.split(path)
        output_file = os.path.join(output_dir, file_name)
        content = self.download_file(path)

        write_data(content, output_file, "wb")
        return output_file
    
    def file_exists(self, file_path: str):
        blob_client = self.container_client.get_blob_client(file_path)
        return blob_client.exists()

    def upload_document(self, bytes: Union[bytes, str], path: str):
        self.container_client.upload_blob(path, bytes, overwrite=True)

    def download_file(self, path: str):
        content = self.container_client.download_blob(path).readall()
        return content

    def download_files(self, base_path: str, output_dir: str):
        files = self._list_documents(base_path)
        parameters = [(file, output_dir) for file in files]
        with ThreadPool(processes=_CONCURRENT_THREADS) as pool:
            results = pool.starmap(self._download_and_save_file, parameters)
        return results

    @classmethod
    def from_credentials(
        cls,
        account_url: str,
        container_name: str,
        key: Optional[str] = None,
    ):
        credential: str | DefaultAzureCredential
        if key:
            credential = key
        else:
            credential = DefaultAzureCredential(
                exclude_workload_identity_credential=True,
                exclude_developer_cli_credential=True,
                exclude_managed_identity_credential=True,
                exclude_powershell_credential=True,
                exclude_shared_token_cache_credential=True,
                exclude_interactive_browser_credential=True
            )

        container_client = AzureContainerClient(
            account_url,
            container_name,
            credential
        )

        try:
            container_client.exists()
        except Exception:
            raise Exception("There was an error connecting to the container client." +
                            "Ensure you are logged in with the Azure CLI using 'az login'" +
                            "If you are already logged in, reach out to see if you have access to the container.")

        return cls(container_client)
