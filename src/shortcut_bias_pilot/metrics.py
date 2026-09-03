"""Pair-level probe metrics. Probe rows are never treated as sequential labels."""

from __future__ import annotations

import numpy as np
import pandas as pd


def pair_deltas(predictions: pd.DataFrame) -> pd.DataFrame:
    """Pivot ``variant`` predictions and calculate H+ minus H- per target."""
    required = {"base_target_id", "variant", "prediction"}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"Missing prediction columns: {sorted(missing)}")
    wide = predictions.pivot_table(
        index="base_target_id", columns="variant", values="prediction", aggfunc="first"
    )
    if not {"plus", "minus"}.issubset(wide.columns):
        raise ValueError("Both plus and minus variants are required")
    result = wide.reset_index()
    result["delta"] = result["plus"] - result["minus"]
    return result


def bootstrap_mean_ci(
    values: pd.Series | np.ndarray,
    replicates: int = 1000,
    seed: int = 42,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Return mean and percentile bootstrap CI for pair-level deltas."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(replicates, len(values)), replace=True).mean(axis=1)
    alpha = (1 - confidence) / 2
    return float(values.mean()), float(np.quantile(samples, alpha)), float(
        np.quantile(samples, 1 - alpha)
    )


def summarize_deltas(
    deltas: pd.DataFrame,
    stratum_col: str | None = None,
    bootstrap_replicates: int = 1000,
) -> pd.DataFrame:
    """Summarize pair-level deltas overall or by an attached stratum."""
    groups = [("all", deltas)] if stratum_col is None else deltas.groupby(stratum_col)
    rows = []
    for name, group in groups:
        mean, low, high = bootstrap_mean_ci(group["delta"], bootstrap_replicates)
        rows.append(
            {
                "stratum": name,
                "n_pairs": int(group["delta"].notna().sum()),
                "mean_delta": mean,
                "median_delta": float(group["delta"].median()),
                "p05_delta": float(group["delta"].quantile(0.05)),
                "p95_delta": float(group["delta"].quantile(0.95)),
                "ci_low": low,
                "ci_high": high,
            }
        )
    return pd.DataFrame(rows)
