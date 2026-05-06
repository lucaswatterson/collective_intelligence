"""Pre-flight predicates that let the schedule pass skip enqueueing a task
when there's nothing to do — e.g. don't pay for a Sonnet+thinking turn just
to read "0 unread" out of Gmail.

Each guard is a no-arg `Callable[[], bool]`. Returning ``False`` tells the
worker to snap ``last_run`` forward and skip this fire. Any error inside a
guard is logged and treated as ``True`` (fail-open) — an LLM call is cheaper
than a missed message.

Guards are *discovered*, not hard-coded here: each `*.py` file under
`entity/guards/` is loaded as a plugin and contributes to the registry via
its top-level `GUARDS` mapping. Integrations (e.g. Google Workspace) ship
their own plugin file, which their install script copies into place. A
fresh harness with no integrations installed has an empty registry — that
is expected, not an error.
"""

import importlib.util
import logging
import sys
from collections.abc import Callable

from harness.config import load_settings


log = logging.getLogger(__name__)


def load_guards() -> dict[str, Callable[[], bool]]:
    """Scan `entity/guards/` for plugin modules and return the merged
    registry. Re-evaluated on every call so a freshly installed integration
    is picked up without restarting the entity. Fail-soft: a plugin that
    fails to import or doesn't export `GUARDS` is logged and skipped."""
    guards_dir = load_settings().guards_dir
    if not guards_dir.exists():
        return {}

    registry: dict[str, Callable[[], bool]] = {}
    for path in sorted(guards_dir.glob("*.py")):
        if path.name.startswith((".", "_")):
            continue
        module_name = f"_harness_guards_{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                log.warning("guards plugin %s: could not build spec", path)
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception:
            log.exception("guards plugin %s failed to import; skipping", path)
            continue

        plugin_guards = getattr(module, "GUARDS", None)
        if not isinstance(plugin_guards, dict):
            log.warning(
                "guards plugin %s does not export a GUARDS dict; skipping", path
            )
            continue
        for name, fn in plugin_guards.items():
            if not callable(fn):
                log.warning(
                    "guards plugin %s entry %r is not callable; skipping", path, name
                )
                continue
            if name in registry:
                log.warning(
                    "guards plugin %s redefines guard %r; overwriting", path, name
                )
            registry[str(name)] = fn
    return registry


# Snapshot at import time for any caller that prefers a plain dict reference.
# Live callers (e.g. `evaluate_guard`, the `manage_schedule` skill) call
# `load_guards()` directly to pick up plugins installed mid-session.
GUARDS: dict[str, Callable[[], bool]] = load_guards()


def evaluate_guard(name: str) -> bool:
    """Look up a guard by name and call it. Unknown names and exceptions
    fail open (return True) so a typo in SCHEDULE.md or a transient error
    can't silently disable a poller."""
    guard = load_guards().get(name)
    if guard is None:
        log.warning("guard %r is not registered; failing open", name)
        return True
    try:
        return guard()
    except Exception:
        log.exception("guard %r raised; failing open", name)
        return True
