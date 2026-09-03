"""Sanity metrics for immutable natural-target predictions."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score


def natural_metrics(predictions: pd.DataFrame) -> dict[str, float | None]:
    """Compute AUC, BCE, and Brier on natural protected-target rows."""
    required = {"target_label", "prediction"}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    y = predictions["target_label"].astype(int).to_numpy()
    p = np.clip(predictions["prediction"].astype(float).to_numpy(), 1e-7, 1 - 1e-7)
    auc = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None
    return {
        "n_targets": float(len(y)),
        "auc": auc,
        "bce": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(np.mean((p - y) ** 2)),
    }
