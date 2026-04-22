from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTITY_ROOT = REPO_ROOT / "entity"


class Models:
    REASONING = "claude-opus-4-7"
    DEFAULT = "claude-sonnet-4-6"
    FAST = "claude-haiku-4-5"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    worker_poll_interval: float = Field(10.0, alias="WORKER_POLL_INTERVAL")

    repo_root: Path = REPO_ROOT
    entity_root: Path = ENTITY_ROOT

    @property
    def birth_path(self) -> Path:
        return self.repo_root / "BIRTH.md"

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
    def tasks_dir(self) -> Path:
        return self.entity_root / "tasks"

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
    def identity_history_path(self) -> Path:
        return self.entity_root / "IDENTITY_HISTORY.md"

    @property
    def self_image_path(self) -> Path:
        return self.entity_root / "self_image.txt"


def load_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
