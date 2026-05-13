from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = Path(__file__).resolve().parent
ENTITY_ROOT = REPO_ROOT / "entity"


class Models:
    REASONING = "claude-opus-4-7"
    DEFAULT = "claude-sonnet-4-6"
    FAST = "claude-haiku-4-5"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    worker_poll_interval: float = Field(10.0, alias="WORKER_POLL_INTERVAL")
    # IANA timezone name used to interpret cron expressions in SCHEDULE.md and
    # to display next-fire times in the UI. Stored timestamps remain UTC.
    scheduler_timezone: str = Field("UTC", alias="SCHEDULER_TIMEZONE")

    web_password_hash: str = Field("", alias="WEB_PASSWORD_HASH")
    web_session_secret: str = Field("", alias="WEB_SESSION_SECRET")
    web_host: str = Field("127.0.0.1", alias="WEB_HOST")
    web_port: int = Field(8000, alias="WEB_PORT")

    repo_root: Path = REPO_ROOT
    harness_root: Path = HARNESS_ROOT
    entity_root: Path = ENTITY_ROOT

    @property
    def template_dir(self) -> Path:
        return self.harness_root / "template"

    @property
    def birth_path(self) -> Path:
        return self.harness_root / "BIRTH.md"

    @property
    def worker_log_path(self) -> Path:
        return self.entity_root / "worker.log"

    @property
    def worker_pid_path(self) -> Path:
        return self.entity_root / "worker.pid"

    @property
    def worker_status_path(self) -> Path:
        return self.entity_root / "worker_status.json"

    @property
    def identity_path(self) -> Path:
        return self.entity_root / "IDENTITY.md"

    @property
    def files_dir(self) -> Path:
        return self.entity_root / "files"

    @property
    def skills_dir(self) -> Path:
        return self.entity_root / "skills"

    @property
    def guards_dir(self) -> Path:
        return self.entity_root / "guards"

    @property
    def tasks_dir(self) -> Path:
        return self.entity_root / "tasks"

    @property
    def responsibilities_dir(self) -> Path:
        return self.entity_root / "responsibilities"

    @property
    def schedule_path(self) -> Path:
        return self.entity_root / "SCHEDULE.md"

    @property
    def scheduler_tz(self) -> ZoneInfo:
        return ZoneInfo(self.scheduler_timezone)

    @property
    def work_dir(self) -> Path:
        return self.entity_root / "work"

    @property
    def short_term_dir(self) -> Path:
        return self.entity_root / "memory" / "short_term"

    @property
    def long_term_dir(self) -> Path:
        return self.entity_root / "memory" / "long_term"

    @property
    def short_term_archive_dir(self) -> Path:
        return self.entity_root / "memory" / "short_term_archive"

    @property
    def long_term_index_path(self) -> Path:
        return self.long_term_dir / "INDEX.md"

    @property
    def knowledge_dir(self) -> Path:
        return self.entity_root / "knowledge"

    @property
    def knowledge_index_path(self) -> Path:
        return self.knowledge_dir / "INDEX.md"

    @property
    def identity_history_path(self) -> Path:
        return self.entity_root / "IDENTITY_HISTORY.md"


def load_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
