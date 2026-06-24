from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./test.db"

    # AI配置（可选）
    doubao_api_key: str = ""
    doubao_model: str = ""
    doubao_base_url: str = ""


def get_settings():
    return Settings()