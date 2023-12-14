import json
import os
from .domain_services_request_manager import DomainServicesRequestManager


_ID_KEY = '_id'
_DOMAIN_KEY = 'domain'
_VERSION_KEY = 'version'
_CREATED_BY_KEY = 'created_by'

_CREATED_BY_TAG = 'msft-att-colab'
_DOMAIN_CONFIG_PATHS = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'domain_configs')


class DomainConfigManager(object):
    _domain: str
    _config_version: str
    _request_manager: DomainServicesRequestManager

    def __init__(
        self,
        request_manager: DomainServicesRequestManager,
        domain: str,
        config_version: str
    ):
        self._request_manager = request_manager
        self._domain = domain
        self._config_version = config_version

    def put_domain_config(self):
        local_domain_config_path = os.path.join(_DOMAIN_CONFIG_PATHS, f"{self._id}.json")
        if not os.path.exists(local_domain_config_path):
            raise Exception(f"Path does not exist {local_domain_config_path}")
        
        with open(local_domain_config_path, "r") as f:
            domain_config = json.load(f)

        domain_config[_ID_KEY] = self._id
        domain_config[_DOMAIN_KEY] = self._domain
        domain_config[_VERSION_KEY] = self._config_version
        domain_config[_CREATED_BY_KEY] = _CREATED_BY_TAG

        return self._request_manager.upload_domain_config(domain_config)

    def get_domain_config(self):
        return self._request_manager.get_domain_config()

    @property
    def _id(self):
        return f"{self._domain}-{self._config_version}"
