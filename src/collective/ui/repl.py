import sys

from collective.entity import Entity


BANNER_BORN = "\n[entity online — type 'exit' to quit]\n"
BANNER_BIRTH = (
    "\n[entity unborn — beginning birth conversation]\n"
    "[say hello to begin; the entity will write IDENTITY.md when ready]\n"
)


def run_repl(entity: Entity) -> None:
    entity.begin_session()
    sys.stdout.write(BANNER_BIRTH if entity.in_birth else BANNER_BORN)
    sys.stdout.flush()

    while True:
        try:
            user_input = input("\nyou › ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write("\n[disconnecting]\n")
            return

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            sys.stdout.write("[disconnecting]\n")
            return

        sys.stdout.write("\nentity › ")
        sys.stdout.flush()
        entity.turn(user_input, on_text=_stream_to_stdout)
        sys.stdout.write("\n")
        sys.stdout.flush()


def _stream_to_stdout(chunk: str) -> None:
    sys.stdout.write(chunk)
    sys.stdout.flush()
