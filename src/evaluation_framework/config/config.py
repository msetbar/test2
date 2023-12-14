import os
from typing import Optional
from pydantic import BaseSettings, Field

_env_file = os.path.join(os.path.dirname(__file__), "dev.env")

class Config(BaseSettings):
    storage_account_url: str = Field(..., env="STORAGE_ACCOUNT_URL")
    storage_account_container: str = Field(..., env="STORAGE_ACCOUNT_CONTAINER")
    oai_api_base: Optional[str] = Field(None, env="OPENAI_API_BASE")
    oai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    oai_api_version: Optional[str] = Field(None, env="OPENAI_API_VERSION")
    oai_api_type: Optional[str] = Field(None, env="OPENAI_API_TYPE")

    class Config:
        env_file = _env_file

config = Config()
