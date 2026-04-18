from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTITY_ROOT = REPO_ROOT / "entity"


class Models:
    REASONING = "claude-opus-4-7"
    DEFAULT = "claude-sonnet-4-6"
    FAST = "claude-haiku-4-5"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

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
    def short_term_dir(self) -> Path:
        return self.entity_root / "memory" / "short_term"

    @property
    def long_term_dir(self) -> Path:
        return self.entity_root / "memory" / "long_term"


def load_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
