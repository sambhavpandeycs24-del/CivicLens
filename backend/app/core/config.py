from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CivicLens AI API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./civiclens_dev.db"
    jwt_secret_key: str = "unsafe-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000"
    complaint_upload_dir: str = "./complaint_uploads"
    complaint_upload_max_bytes: int = 5 * 1024 * 1024
    category_model_path: str = "data/complaint_category_model.json"
    sla_target_hours_json: str = (
        '{"priority:urgent":24,"priority:high":72,"priority:medium":168,'
        '"priority:low":336}'
    )
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
