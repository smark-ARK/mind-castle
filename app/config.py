from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: int
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    refresh_secret_key: str
    algorithm: str
    access_expire_minutes: int
    refresh_expire_minutes: int


settings = Settings(_env_file=".env")
