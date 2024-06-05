import os
from datetime import date
from pathlib import Path

from pydantic import SecretStr, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

today = date.today()
root_path = Path(os.path.abspath(__file__)).parent


class DBSettings(BaseSettings):
    driver_name: str
    username: str
    password: SecretStr
    host: str
    port: int
    echo: bool
    database: str
    model_config = SettingsConfigDict(env_file=f'{root_path}/setup/db.env', env_file_encoding='utf-8')


class MainSettings(BaseSettings, case_sensitive=True):
    telegram_admin_id: list
    bot_token: SecretStr
    vk_api_token: SecretStr
    vk_token: SecretStr
    model_config = SettingsConfigDict(env_file=f'{root_path}/setup/settings.env', env_file_encoding='utf-8')


main_settings = MainSettings()
