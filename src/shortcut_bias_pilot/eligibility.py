"""Build target-level eligible populations for the two pilot cases."""

from __future__ import annotations

import pandas as pd
from .concept_relations import ConceptRelations

from .profiles import ItemPriorProfile


def make_targets(
    sequences: pd.DataFrame,
    item_profile: ItemPriorProfile,
    *,
    local_min_support: int = 3,
    remote_min_support: int = 5,
    max_targets: int | None = None,
    relations: ConceptRelations | None = None,
) -> tuple[pd.DataFrame, dict[str, tuple[pd.DataFrame, pd.Series]]]:
    """Create natural targets and strict prefixes from canonical test events.

    The source table must contain test events only. Prefixes are derived within
    one sequence, so no future event or target response is used in features.
    """
    target_rows: list[dict] = []
    context: dict[str, tuple[pd.DataFrame, pd.Series]] = {}
    relations = relations or ConceptRelations.exact_only()
    for sequence_id, sequence in sequences.groupby("sequence_id", sort=False):
        sequence = sequence.sort_values("position").reset_index(drop=True)
        local_events: list[pd.Series] = []
        total_sum = 0
        for position in range(1, len(sequence)):
            target = sequence.iloc[position].copy()
            target_skills = tuple(target["concept_ids"])
            prefix = sequence.iloc[:position]
            local_mask = prefix["concept_ids"].map(lambda values: bool(set(values) & set(target_skills)))
            local = prefix[local_mask]
            remote_mask = prefix.apply(lambda event: str(event["question_id"]) != str(target["question_id"]) and relations.event_is_unrelated(event["concept_ids"], target_skills)[0], axis=1)
            remote = prefix[remote_mask]
            n_local, n_remote = len(local), len(remote)
            recent = local.tail(local_min_support)["response"].tolist()
            remote_sum = int(remote["response"].sum())
            eligible_iap = n_local >= local_min_support
            eligible_lgt = n_remote >= remote_min_support and n_local < local_min_support
            if not eligible_iap and not eligible_lgt:
                response = int(target["response"])
                continue
            event_id = str(target["event_id"])
            row = target.to_dict()
            row.update(
                {
                    "base_target_id": event_id,
                    "target_label": int(target["response"]),
                    "n_local": n_local,
                    "n_remote": n_remote,
                    "r_local": float(sum(recent) / len(recent)) if recent else None,
                    "g_global": float(remote_sum / n_remote) if n_remote else None,
                    "eligible_iap": eligible_iap,
                    "eligible_lgt": eligible_lgt,
                }
            )
            target_rows.append(row)
            context[event_id] = (sequence, position)
            response = int(target["response"])
    targets = pd.DataFrame(target_rows)
    if targets.empty:
        raise ValueError("No eligible natural test targets found")
    targets = item_profile.attach(targets)
    if max_targets is not None and len(targets) > max_targets:
        targets = targets.sort_values("event_id", kind="stable").head(max_targets).reset_index(drop=True)
        context = {event_id: context[event_id] for event_id in targets["event_id"]}
    return targets, context
