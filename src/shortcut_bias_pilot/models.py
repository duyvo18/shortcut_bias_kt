"""Model construction and training helpers backed by pyKT 0.0.38."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from .env import configure_environment

configure_environment()

import numpy as np


def seed_everything(seed: int) -> None:
    """Seed Python, NumPy, and PyTorch when available."""
    random.seed(seed)
    np.random.seed(seed)
    import torch

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def configure_torch_runtime(train: Any) -> None:
    """Configure CPU pools used around GPU model execution."""
    import torch

    torch.set_num_threads(train.cpu_threads)
    try:
        torch.set_num_interop_threads(train.cpu_interop_threads)
    except RuntimeError:
        # The process may have initialized the inter-op pool before this call.
        pass


def model_config(model_name: str, train: Any, data_config: dict[str, Any]) -> dict[str, Any]:
    """Return a pyKT-compatible model configuration for the pilot panel."""
    if model_name == "dkt":
        return {"emb_size": train.emb_size, "dropout": train.dropout}
    if model_name == "saint":
        return {
            "seq_len": data_config["maxlen"],
            "emb_size": train.emb_size,
            "num_attn_heads": 8,
            "dropout": train.dropout,
            "n_blocks": 1,
        }
    if model_name == "akt":
        return {
            "d_model": train.emb_size,
            "n_blocks": 2,
            "dropout": train.dropout,
            "d_ff": max(256, train.emb_size * 2),
            "kq_same": 1,
            "final_fc_dim": train.emb_size,
            "num_attn_heads": 8,
            "separate_qa": False,
            "l2": 1e-5,
        }
    raise ValueError(f"Unsupported pilot model: {model_name}")


def train_with_pykt(
    dataset_name: str,
    data_config: dict[str, Any],
    train: Any,
    seed: int,
    output_dir: str | Path,
) -> Path:
    """Train one baseline with pyKT's standard train loop.

    This is intentionally an explicit, user-invoked workload. The function
    does not run automatically during import or preprocessing.
    """
    if train.device != "cuda":
        raise ValueError("device must be cuda")
    import torch
    from pykt.datasets import init_dataset4train
    from pykt.models import init_model, train_model

    if train.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    configure_torch_runtime(train)
    seed_everything(seed)
    model_name = train.models[0] if len(train.models) == 1 else None
    if model_name is None:
        raise ValueError("Pass one model at a time to train_with_pykt")
    loaders = init_dataset4train(
        dataset_name,
        model_name,
        {dataset_name: data_config},
        train.fold,
        train.batch_size,
    )
    train_loader, valid_loader, _test_loader, _window_loader = loaders
    config = model_config(model_name, train, data_config)
    model = init_model(model_name, config, data_config, "qid")
    if next(model.parameters()).device.type != "cuda":
        raise RuntimeError("pyKT model was not initialized on CUDA")
    optimizer = torch.optim.Adam(model.parameters(), lr=train.learning_rate)
    checkpoint_dir = Path(output_dir) / dataset_name / model_name / f"seed_{seed}" / f"fold_{train.fold}"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    train_model(
        model,
        train_loader,
        valid_loader,
        train.epochs,
        optimizer,
        str(checkpoint_dir),
        test_loader=None,
        test_window_loader=None,
        save_model=True,
    )
    checkpoint = checkpoint_dir / "qid_model.ckpt"
    if not checkpoint.exists():
        raise FileNotFoundError(f"pyKT did not write expected checkpoint: {checkpoint}")
    return checkpoint


def load_pykt_model(
    model_name: str,
    data_config: dict[str, Any],
    train: Any,
    checkpoint: str | Path,
):
    """Construct a pyKT model and load a checkpoint produced by this project."""
    import torch
    from pykt.models import init_model

    model = init_model(model_name, model_config(model_name, train, data_config), data_config, "qid")
    if next(model.parameters()).device.type != "cuda":
        raise RuntimeError("pyKT checkpoint model was not initialized on CUDA")
    state = torch.load(Path(checkpoint), map_location=next(model.parameters()).device)
    model.load_state_dict(state)
    model.eval()
    return model
