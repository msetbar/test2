import os
from pydantic import BaseSettings, Field


class SnowflakeConfig(BaseSettings):
    username: str = Field(..., env="snowflake_username")
    password: str = Field(..., env="snowflake_password")
    account: str = Field(..., env="snowflake_account")
    warehouse: str = Field(..., env="snowflake_warehouse")
    database: str = Field(..., env="snowflake_database")
    role: str = Field("PUBLIC", env="snowflake_role")

    class Config:
        case_sensitive = False

env_file_path = os.path.join(os.path.dirname(__file__), "..", ".env")
config = SnowflakeConfig(_env_file=env_file_path)
