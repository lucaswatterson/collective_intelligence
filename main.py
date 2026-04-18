from collective.config import load_settings
from collective.entity import Entity
from collective.ui.repl import run_repl


def main() -> None:
    settings = load_settings()
    entity = Entity(settings)
    run_repl(entity)


if __name__ == "__main__":
    main()
