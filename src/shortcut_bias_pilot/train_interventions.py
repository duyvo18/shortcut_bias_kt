"""Deterministic IAP label-edit arms over the train partition only."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


def file_hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass(frozen=True)
class IAPArm:
    item_id: str
    arm: str
    changed_event_ids: tuple[str, ...]
    original_prior: float
    target_prior: float
    achieved_prior: float
    n_changed: int


def select_iap_arms(train_events: pd.DataFrame, item_id: object, *, seed: int) -> list[IAPArm]:
    """Select every feasible 0→1 or 1→0 edit for one item deterministically."""
    subset = train_events[train_events["question_id"].astype(str) == str(item_id)].copy()
    if subset.empty or subset["response"].nunique() < 2:
        return []
    subset = subset.sort_values("event_id", kind="stable")
    prior = float(subset["response"].mean())
    result = []
    for arm, source, replacement in (("prior_high", 0, 1), ("prior_low", 1, 0)):
        changed = subset.loc[subset["response"] == source, "event_id"].astype(str).tolist()
        achieved = float((subset["response"].sum() + (replacement - source) * len(changed)) / len(subset))
        result.append(IAPArm(str(item_id), arm, tuple(changed), prior, float(replacement), achieved, len(changed)))
    return result


def write_iap_arm(source_csv: str | Path, destination_csv: str | Path, arm: IAPArm, manifest_path: str | Path, *, test_hash: str, fold: int) -> None:
    """Write a row-level sequence arm; assert only listed train responses changed."""
    source = pd.read_csv(source_csv)
    changed = set(arm.changed_event_ids)
    # event IDs are reconstructed exactly like ``load_pykt_sequences``.
    altered = source.copy(deep=True)
    for row_index, row in altered.iterrows():
        sequence_id = f"{Path(source_csv).stem}:{row_index}"
        if "fold" in row and int(row["fold"]) == fold:
            continue  # validation portion must remain untouched
        questions = str(row["questions"]).split(",")
        responses = str(row["responses"]).split(",")
        for position, question in enumerate(questions[:len(responses)]):
            if f"{sequence_id}:{position}" in changed:
                responses[position] = "1" if arm.arm == "prior_high" else "0"
        altered.at[row_index, "responses"] = ",".join(responses)
    destination = Path(destination_csv); destination.parent.mkdir(parents=True, exist_ok=True)
    altered.to_csv(destination, index=False)
    payload = {**arm.__dict__, "changed_event_ids": list(arm.changed_event_ids), "fold": fold, "source_train_hash": file_hash(source_csv), "arm_train_hash": file_hash(destination), "test_hash": test_hash}
    Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
    Path(manifest_path).write_text(json.dumps(payload, indent=2))
