from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    refresh_secret_key: str
    algorithm: str
    access_expire_minutes: int
    refresh_expire_minutes: int
    database_test_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings(_env_file=".env", extra="ignore")
