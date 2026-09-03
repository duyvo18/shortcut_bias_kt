"""Build target-level eligible populations for the two pilot cases."""

from __future__ import annotations

import pandas as pd

from .profiles import ItemPriorProfile


def make_targets(
    sequences: pd.DataFrame,
    item_profile: ItemPriorProfile,
    *,
    local_min_support: int = 3,
    remote_min_support: int = 5,
    max_targets: int | None = None,
) -> tuple[pd.DataFrame, dict[str, tuple[pd.DataFrame, pd.Series]]]:
    """Create natural targets and strict prefixes from canonical test events.

    The source table must contain test events only. Prefixes are derived within
    one sequence, so no future event or target response is used in features.
    """
    target_rows: list[dict] = []
    context: dict[str, tuple[pd.DataFrame, pd.Series]] = {}
    for sequence_id, sequence in sequences.groupby("sequence_id", sort=False):
        sequence = sequence.sort_values("position").reset_index(drop=True)
        local_counts: dict[object, int] = {}
        local_sums: dict[object, int] = {}
        local_recent: dict[object, list[int]] = {}
        total_sum = 0
        for position in range(1, len(sequence)):
            target = sequence.iloc[position].copy()
            concept = target["concept_id"]
            n_local = local_counts.get(concept, 0)
            n_remote = position - n_local
            local_sum = local_sums.get(concept, 0)
            remote_sum = total_sum - local_sum
            recent = local_recent.get(concept, [])
            eligible_iap = n_local >= local_min_support
            eligible_lgt = n_remote >= remote_min_support and n_local < local_min_support
            if not eligible_iap and not eligible_lgt:
                response = int(target["response"])
                total_sum += response
                local_counts[concept] = n_local + 1
                local_sums[concept] = local_sum + response
                local_recent[concept] = (recent + [response])[-local_min_support:]
                continue
            if not eligible_iap and not eligible_lgt:
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
            total_sum += response
            local_counts[concept] = n_local + 1
            local_sums[concept] = local_sum + response
            local_recent[concept] = (recent + [response])[-local_min_support:]
    targets = pd.DataFrame(target_rows)
    if targets.empty:
        raise ValueError("No eligible natural test targets found")
    targets = item_profile.attach(targets)
    if max_targets is not None and len(targets) > max_targets:
        targets = targets.sort_values("event_id", kind="stable").head(max_targets).reset_index(drop=True)
        context = {event_id: context[event_id] for event_id in targets["event_id"]}
    return targets, context
