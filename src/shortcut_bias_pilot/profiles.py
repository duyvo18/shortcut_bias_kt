"""Source-profile statistics and opportunity controls.

All functions in this module operate on canonical interaction tables. They do
not fit anything from a test label; callers must provide train-derived item
priors and learner history that ends strictly before each target.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


@dataclass(frozen=True)
class ItemPriorProfile:
    """Train-fitted item-answer prior and high/low strata thresholds."""

    table: pd.DataFrame
    low_cut: float
    high_cut: float

    def attach(self, targets: pd.DataFrame, item_col: str = "question_id") -> pd.DataFrame:
        """Attach prior/support/stratum to targets without changing row order."""
        out = targets.copy()
        lookup = self.table.rename(columns={"item_id": item_col})
        out = out.merge(lookup, on=item_col, how="left", validate="many_to_one")
        out["prior_stratum"] = np.select(
            [out["item_prior"] <= self.low_cut, out["item_prior"] >= self.high_cut],
            ["prior_low", "prior_high"],
            default="prior_middle",
        )
        return out


def fit_item_prior(
    train: pd.DataFrame,
    item_col: str = "question_id",
    response_col: str = "response",
    min_support: int = 30,
    low_quantile: float = 0.2,
    high_quantile: float = 0.8,
) -> ItemPriorProfile:
    """Fit item priors and quantile cuts using train interactions only."""
    grouped = train.groupby(item_col, dropna=False)[response_col].agg(["sum", "count"])
    grouped = grouped.rename(columns={"sum": "correct", "count": "item_support"})
    grouped = grouped[grouped["item_support"] >= min_support].copy()
    grouped["item_prior"] = grouped["correct"] / grouped["item_support"]
    if grouped.empty:
        raise ValueError("No items satisfy item_min_support")
    return ItemPriorProfile(
        table=grouped.reset_index().rename(columns={item_col: "item_id"}),
        low_cut=float(grouped["item_prior"].quantile(low_quantile)),
        high_cut=float(grouped["item_prior"].quantile(high_quantile)),
    )


def history_features(
    history: pd.DataFrame,
    learner_col: str = "learner_id",
    concept_col: str = "concept_id",
    response_col: str = "response",
    target_concept: object | None = None,
    recent_k: int = 3,
) -> dict[str, float | int | None]:
    """Compute local and remote features from a prefix ending before target."""
    if target_concept is None:
        raise ValueError("target_concept is required")
    history = history.reset_index(drop=True)
    local = history[history[concept_col] == target_concept]
    remote = history[history[concept_col] != target_concept]
    recent = local.tail(recent_k)
    return {
        "n_local": int(len(local)),
        "r_local": float(recent[response_col].mean()) if len(recent) else None,
        "recency_local": int(len(history) - 1 - local.index[-1]) if len(local) else None,
        "n_remote": int(len(remote)),
        "g_global": float(remote[response_col].mean()) if len(remote) else None,
    }


def learner_global_only(
    targets: pd.DataFrame,
    history_by_target: Iterable[pd.DataFrame],
    concept_col: str = "concept_id",
) -> pd.DataFrame:
    """Attach the remote response mean for each target as an opportunity score."""
    rows = []
    for target, history in zip(targets.itertuples(index=False), history_by_target):
        concept = getattr(target, concept_col)
        remote = history[history[concept_col] != concept]
        rows.append(
            {
                "g_global": float(remote["response"].mean()) if len(remote) else np.nan,
                "remote_support": int(len(remote)),
            }
        )
    return pd.concat([targets.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def binary_opportunity_score(y_true: pd.Series, score: pd.Series) -> float | None:
    """Return AUC for a source-only control, or ``None`` when undefined."""
    valid = y_true.notna() & score.notna()
    if valid.sum() == 0 or y_true[valid].nunique() < 2:
        return None
    return float(roc_auc_score(y_true[valid], score[valid]))
