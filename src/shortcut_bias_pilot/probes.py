"""Counterfactual prefix generation for IAP-01 and LGT-01.

The input contract is a canonical per-learner event table. A target row is
represented separately and is never altered by these functions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProbeSpec:
    """Locked choices for a probe family."""

    case_id: str
    recent_k: int = 3
    remote_fraction: float = 0.5
    seed: int = 42


def _check_prefix(prefix: pd.DataFrame, target: pd.Series) -> None:
    if prefix.empty:
        raise ValueError("A probe requires a non-empty prefix")
    if target.get("target_label") is None or pd.isna(target.get("target_label")):
        raise ValueError("Target label must be recorded separately from the input")


def _replace_positions(prefix: pd.DataFrame, positions: np.ndarray, value: int) -> pd.DataFrame:
    out = prefix.copy(deep=True)
    out.iloc[positions, out.columns.get_loc("response")] = value
    return out


def build_iap_pair(
    prefix: pd.DataFrame,
    target: pd.Series,
    spec: ProbeSpec,
) -> dict[str, pd.DataFrame]:
    """Build local-good/local-poor variants while keeping target metadata fixed."""
    _check_prefix(prefix, target)
    concept = target["concept_id"]
    positions = np.flatnonzero(prefix["concept_id"].to_numpy() == concept)[-spec.recent_k :]
    if len(positions) < spec.recent_k:
        raise ValueError("Prefix does not satisfy local support for IAP-01")
    return {
        "natural": prefix.copy(deep=True),
        "plus": _replace_positions(prefix, positions, 1),
        "minus": _replace_positions(prefix, positions, 0),
    }


def build_lgt_pair(
    prefix: pd.DataFrame,
    target: pd.Series,
    spec: ProbeSpec,
) -> dict[str, pd.DataFrame]:
    """Build remote-good/remote-poor variants while preserving local history."""
    _check_prefix(prefix, target)
    concept = target["concept_id"]
    remote_positions = np.flatnonzero(prefix["concept_id"].to_numpy() != concept)
    if len(remote_positions) < 2:
        raise ValueError("Prefix does not satisfy remote support for LGT-01")
    n_changed = max(1, int(np.ceil(len(remote_positions) * spec.remote_fraction)))
    rng = np.random.default_rng(spec.seed)
    changed = np.sort(rng.choice(remote_positions, size=n_changed, replace=False))
    return {
        "natural": prefix.copy(deep=True),
        "plus": _replace_positions(prefix, changed, 1),
        "minus": _replace_positions(prefix, changed, 0),
    }


def validate_pair(
    variants: dict[str, pd.DataFrame],
    target: pd.Series,
    required_columns: tuple[str, ...] = ("question_id", "concept_id", "response"),
) -> None:
    """Validate symmetric probe invariants before model execution."""
    if set(variants) != {"natural", "plus", "minus"}:
        raise ValueError("Variants must be natural, plus, and minus")
    for name, frame in variants.items():
        missing = set(required_columns) - set(frame.columns)
        if missing:
            raise ValueError(f"{name} is missing columns: {sorted(missing)}")
        if len(frame) != len(variants["natural"]):
            raise ValueError("Probe variants must have identical prefix lengths")
    if (
        target.get("question_id") is None
        or pd.isna(target.get("question_id"))
        or target.get("concept_id") is None
        or pd.isna(target.get("concept_id"))
    ):
        raise ValueError("Target item and concept must be locked")
