"""Canonical records built from pyKT-generated sequence files.

pyKT owns raw-data preprocessing and fold generation. This module only
flattens the resulting sequence CSVs into an analysis table with stable event
identifiers needed by source profiles and probes.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CANONICAL_COLUMNS = (
    "sequence_id",
    "position",
    "event_id",
    "learner_id",
    "question_id",
    "concept_id",
    "concept_ids",
    "response",
    "timestamp",
    "fold",
)


def _split_values(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [str(part) for part in str(value).split(",")]


def load_pykt_sequences(path: str | Path, *, include_fold: int | None = None) -> pd.DataFrame:
    """Flatten a pyKT ``*_sequences.csv`` or original split CSV.

    ``pyKT`` represents one learner sequence per row and stores fields as
    comma-separated strings. Padded values (``-1``) are removed. Multi-KC
    values may encode multiple KCs using ``_``.  ``concept_id`` remains the
    deterministic model-facing KC required by pyKT; ``concept_ids`` is the
    complete raw-event KC list and is mandatory for all eligibility decisions.
    """
    source = Path(path)
    frame = pd.read_csv(source)
    if include_fold is not None and "fold" in frame.columns:
        frame = frame[frame["fold"] == include_fold]

    records: list[dict[str, object]] = []
    for row_number, row in frame.reset_index(drop=True).iterrows():
        questions = _split_values(row.get("questions"))
        concepts = _split_values(row.get("concepts"))
        responses = _split_values(row.get("responses"))
        timestamps = _split_values(row.get("timestamps"))
        learner = str(row.get("uid", row.get("learner_id", row_number)))
        length = min(len(concepts), len(responses))
        for position in range(length):
            if concepts[position] == "-1" or responses[position] == "-1":
                continue
            question = questions[position] if position < len(questions) else "NA"
            if question == "NA":
                continue
            timestamp = timestamps[position] if position < len(timestamps) else "NA"
            sequence_id = f"{source.stem}:{row_number}"
            concept_ids = tuple(part for part in concepts[position].split("_") if part and part != "-1")
            if not concept_ids:
                continue
            records.append(
                {
                    "sequence_id": sequence_id,
                    "position": position,
                    "event_id": f"{sequence_id}:{position}",
                    "learner_id": learner,
                    "question_id": question,
                    "concept_id": concept_ids[0],
                    "concept_ids": concept_ids,
                    "response": int(float(responses[position])),
                    "timestamp": timestamp,
                    "fold": int(row["fold"]) if "fold" in row and pd.notna(row["fold"]) else -1,
                }
            )
    result = pd.DataFrame.from_records(records, columns=CANONICAL_COLUMNS)
    if result.empty:
        raise ValueError(f"No valid interactions found in {source}")
    return result


def split_prefix_target(sequence: pd.DataFrame, target_position: int) -> tuple[pd.DataFrame, pd.Series]:
    """Return a strict prefix and a target row from one canonical sequence."""
    ordered = sequence.sort_values("position").reset_index(drop=True)
    if target_position <= 0 or target_position >= len(ordered):
        raise ValueError("target_position must leave at least one prefix event and one target")
    target = ordered.iloc[target_position].copy()
    target["target_label"] = int(target["response"])
    return ordered.iloc[:target_position].copy(), target
