"""Project-local environment loading.

The loader is intentionally small and side-effect free apart from loading a
`.env` file. It runs before NumPy, pandas, Torch, or pyKT imports so thread
and CUDA-related settings can take effect for the process.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_project_env(start: str | Path | None = None) -> Path | None:
    """Load the nearest project `.env` and return its path.

    Search starts at ``start`` (or the current working directory), then walks
    upward. If no file is found, the repository root is checked as a stable
    fallback. Existing shell variables win over values in `.env`.
    """
    start_path = Path(start or Path.cwd()).resolve()
    if start_path.is_file():
        start_path = start_path.parent
    candidates = [start_path, *start_path.parents]
    if PROJECT_ROOT not in candidates:
        candidates.append(PROJECT_ROOT)
    for directory in candidates:
        env_path = directory / ".env"
        if env_path.is_file():
            load_dotenv(env_path, override=False)
            return env_path
    return None


def configure_environment() -> None:
    """Load `.env`, then apply environment defaults used by the pilot."""
    load_project_env()
    cpu_threads = os.getenv("PILOT_CPU_THREADS", "20")
    os.environ.setdefault("PILOT_CPU_INTEROP_THREADS", "2")
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(variable, cpu_threads)
    os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")


configure_environment()
