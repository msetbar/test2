from io import BufferedReader
import requests
from typing import Tuple


_LOCAL_ENV = "local"
_FILES_KEY = "files"


class DomainServicesRequestManager(object):
    _admin_base_url: str
    _base_url: str

    _domain: str
    _code_base_version: str
    _config_version: str
    _env: str

    def __init__(
        self,
        domain: str,
        config_version: str,
        env: str,
        code_base_version: str = "automation",
    ):
        self._domain = domain
        self._code_base_version = code_base_version
        self._config_version = config_version
        self._env = env

        if self._env.lower() == _LOCAL_ENV:
            self._admin_base_url = f"http://localhost:8802/{self._code_base_version}/domain-services/admin"
            self._base_url = f"http://localhost:8802/{self._code_base_version}/domain-services"
        else:
            self._admin_base_url = f"https://askapi.{self._env}.att.com/{self._code_base_version}/domain-services/admin"
            self._base_url = f"https://askapi.{self._env}.att.com/{self._code_base_version}/domain-services"

    def get_domain_config(self):
        url = self._domain_config_url
        params = {
            "domain": self._domain,
            "config_version": self._config_version,
        }

        res = requests.get(
            url,
            params=params
        )
        return res
    
    def upload_domain_config(self, domain_config: dict):
        url = self._upload_domain_config_url
        params = {
            "domain": self._domain,
            "config_version": self._config_version,
        }
        body = domain_config

        res = requests.post(
            url,
            params=params,
            json=body
        )
        return res

    def upload_document(
        self,
        documents: list[Tuple[str, BufferedReader]],
    ):
        files = [(_FILES_KEY, document)for document in documents]
        res = requests.post(
            url=self._upload_documents_url,
            files=files
        )
        return res
    
    def similarity_search(
        self,
        query: str,
        k_init_retrieval: int
    ):
        return self._query_request_with_k(self._similarity_search_url, query, k_init_retrieval)
    
    def chat(
        self,
        query: str
    ):
      return self._query_request(self._chat_search_url, query)  
    
    def _query_request(self, url: str, query: str):
        body = {
            "domain": self._domain,
            "config_version": self._config_version,
            "query": query
        }

        res = requests.post(
            url=url,
            json=body
        )
        return res
    
    def _query_request_with_k(self, url: str, query: str, k: int):
        body = {
            "domain": self._domain,
            "config_version": self._config_version,
            "query": query,
            "k": k
        }

        res = requests.post(
            url=url,
            json=body
        )
        return res
    
    @property
    def _chat_search_url(self):
        return f"{self._base_url}/chat"

    @property
    def _similarity_search_url(self):
        return f"{self._base_url}/similarity-search"

    @property
    def _upload_documents_url(self):
        return f"{self._base_url}/upload-documents?domain={self._domain}&config_version={self._config_version}"

    @property
    def _domain_config_url(self):
        return f"{self._admin_base_url}/get-domain-config"
    
    @property
    def _upload_domain_config_url(self):
        return f"{self._admin_base_url}/add-update-domain-config"
