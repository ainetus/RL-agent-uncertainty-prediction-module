"""
Compatibility configuration loader.

Use the full configuration by default:
    python main.py

Use the smoke-test configuration for quick end-to-end checks:
    python main.py --config smoke
    CP_CONFIG=smoke python main.py
"""

import importlib
import os


CONFIG_NAME = os.environ.get("CP_CONFIG", "full").strip().lower()
CONFIG_MODULES = {
    "full": "config_full",
    "smoke": "config_smoke",
}

if CONFIG_NAME not in CONFIG_MODULES:
    raise ValueError(
        f"Unknown CP_CONFIG={CONFIG_NAME!r}. Expected one of: "
        + ", ".join(sorted(CONFIG_MODULES))
    )

_selected_config = importlib.import_module(CONFIG_MODULES[CONFIG_NAME])

for _name in dir(_selected_config):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_selected_config, _name)

