"""NileOps Process Bootstrap & Windows Security Environment Customization.

Provides process-level environment configuration for Windows Smart App Control (SAC)
and offline execution of PaddleOCR and SentenceTransformers.
"""

import os
import sys

# 1. Configure Paddle runtime flags to disable MKLDNN/OneDNN and PIR executor issues on Windows
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# Offline mode for huggingface & transformers
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Set cache directories within the repository data folder
WORKSPACE_DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
if not os.environ.get("PADDLE_PDX_CACHE_HOME"):
    os.environ["PADDLE_PDX_CACHE_HOME"] = os.path.join(WORKSPACE_DATA, "paddlex")
if not os.environ.get("PADDLE_HOME"):
    os.environ["PADDLE_HOME"] = os.path.join(WORKSPACE_DATA, "paddle")

# 2. Provide lightweight shim for pandas ONLY on Windows and only if importing native pandas fails
if sys.platform == "win32":
    try:
        import pandas  # noqa: F401
    except (ImportError, Exception):
        from unittest.mock import MagicMock
        from importlib.machinery import ModuleSpec

        class _PandasShimFinder:
            def find_spec(self, fullname, path, target=None):
                if fullname == "pandas" or fullname.startswith("pandas."):
                    return ModuleSpec(fullname, self, is_package=True)
                return None

            def create_module(self, spec):
                mod = MagicMock()
                mod.__file__ = "<mock>"
                mod.__path__ = []
                return mod

            def exec_module(self, module):
                pass

        sys.meta_path.insert(0, _PandasShimFinder())

# 3. Ensure torch DLL directory is available on Windows before model imports
if hasattr(os, "add_dll_directory"):
    import importlib.util
    torch_spec = importlib.util.find_spec("torch")
    if torch_spec and torch_spec.origin:
        torch_lib = os.path.join(os.path.dirname(torch_spec.origin), "lib")
        if os.path.exists(torch_lib):
            try:
                os.environ["PATH"] = torch_lib + ";" + os.environ.get("PATH", "")
                os.add_dll_directory(torch_lib)
            except Exception:
                pass
