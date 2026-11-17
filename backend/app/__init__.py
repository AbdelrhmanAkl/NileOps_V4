"""NileOps Backend Application Package."""

import sys

# Provide graceful fallback for Windows Smart App Control when native C-extensions (.pyd)
# such as ujson are blocked by OS security policy.
if sys.platform == "win32":
    try:
        import ujson  # noqa: F401
    except (ImportError, Exception):
        sys.modules["ujson"] = None

__version__ = "1.0.0"
