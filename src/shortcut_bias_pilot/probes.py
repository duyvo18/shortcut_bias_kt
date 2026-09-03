"""Counterfactual prefix generation for IAP-01 and LGT-01.

The input contract is a canonical per-learner event table. A target row is
represented separately and is never altered by these functions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from .concept_relations import ConceptRelations


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


def build_lgt_pair(
    prefix: pd.DataFrame,
    target: pd.Series,
    spec: ProbeSpec,
    relations: ConceptRelations | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    """Change only all-skill-unrelated, different-question history events."""
    _check_prefix(prefix, target)
    relations = relations or ConceptRelations.exact_only()
    target_skills = tuple(target["concept_ids"])
    candidates: list[int] = []
    audit: list[dict[str, object]] = []
    for position, event in prefix.reset_index(drop=True).iterrows():
        allowed, pair_relations = relations.event_is_unrelated(event["concept_ids"], target_skills)
        different_question = str(event["question_id"]) != str(target["question_id"])
        audit.append({"event_id": event["event_id"], "relations": pair_relations, "eligible": allowed and different_question})
        if allowed and different_question:
            candidates.append(position)
    remote_positions = np.asarray(candidates, dtype=int)
    if len(remote_positions) < 2:
        raise ValueError("Prefix does not satisfy remote support for LGT-01")
    n_changed = max(1, int(np.ceil(len(remote_positions) * spec.remote_fraction)))
    rng = np.random.default_rng(spec.seed)
    changed = np.sort(rng.choice(remote_positions, size=n_changed, replace=False))
    variants = {
        "natural": prefix.copy(deep=True),
        "plus": _replace_positions(prefix, changed, 1),
        "minus": _replace_positions(prefix, changed, 0),
    }
    return variants, {"changed_event_ids": prefix.iloc[changed]["event_id"].astype(str).tolist(), "relation_mode": relations.mode, "relation_audit": audit}


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
