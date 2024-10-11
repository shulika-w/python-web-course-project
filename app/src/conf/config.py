import pathlib

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=pathlib.Path(__file__).resolve().parent.parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",


    )

    api_name: str
    api_protocol: str
    api_host: str = "localhost"
    api_port: int = 8000
    secret_key_length: int
    algorithm: str
    sqlalchemy_database_url_sync: str
    sqlalchemy_database_url_async: str
    redis_url: str
    redis_expire: int
    rate_limiter_times: int
    rate_limiter_seconds: int
    mail_server: str
    mail_port: int
    mail_username: str
    mail_password: str
    mail_from: str
    mail_from_name: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    test: bool


settings = Settings()