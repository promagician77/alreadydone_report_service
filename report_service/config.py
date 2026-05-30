from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    REPORT_FROM_EMAIL: str = ""
    REPORT_TO_EMAIL: str = ""
    REPORT_DRY_RUN: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("REPORT_DRY_RUN", mode="before")
    @classmethod
    def parse_dry_run(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def validate_for_run(self) -> None:
        missing = []
        if not self.SUPABASE_URL.strip():
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY.strip():
            missing.append("SUPABASE_KEY")
        if not self.REPORT_DRY_RUN:
            if not self.SENDGRID_API_KEY.strip():
                missing.append("SENDGRID_API_KEY")
            if not self.REPORT_FROM_EMAIL.strip():
                missing.append("REPORT_FROM_EMAIL")
            if not self.REPORT_TO_EMAIL.strip():
                missing.append("REPORT_TO_EMAIL")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


settings = Settings()
