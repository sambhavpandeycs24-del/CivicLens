from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CivicLens AI API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = False
    allowed_hosts: str = "*"
    database_url: str = "sqlite:///./civiclens_dev.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800
    jwt_secret_key: str = "unsafe-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000"
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    trusted_proxy_count: int = 1
    complaint_upload_dir: str = "./complaint_uploads"
    complaint_upload_max_bytes: int = 5 * 1024 * 1024
    complaint_image_storage: str = "local"
    s3_bucket: str = ""
    s3_region: str = ""
    s3_endpoint_url: str = ""
    s3_public_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    category_model_path: str = "data/complaint_category_model.json"
    sla_target_hours_json: str = (
        '{"priority:urgent":24,"priority:high":72,"priority:medium":168,'
        '"priority:low":336}'
    )
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

settings = Settings()
