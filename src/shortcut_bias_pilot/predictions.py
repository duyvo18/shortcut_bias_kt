"""Natural and protected-target prediction collection for pyKT models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _device_for(model):
    import torch

    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def predict_target(model, model_name: str, prefix: pd.DataFrame, target: pd.Series) -> float:
    """Predict one target using the same shifted convention as pyKT evaluate.

    The prefix contains observed interactions only. The target item/concept is
    appended as the query position, while its response is never passed in.
    For AKT/SAINT, the query position is scored from the shifted output. DKT
    scores the target concept from the final prefix state.
    """
    import torch

    if prefix.empty:
        raise ValueError("A prefix is required")
    device = _device_for(model)
    concepts = torch.tensor(prefix["concept_id"].astype(int).tolist(), dtype=torch.long, device=device).unsqueeze(0)
    target_concept = torch.tensor([[int(target["concept_id"])]], dtype=torch.long, device=device)
    questions = torch.tensor(prefix["question_id"].astype(int).tolist(), dtype=torch.long, device=device).unsqueeze(0)
    target_question = torch.tensor([[int(target["question_id"])]], dtype=torch.long, device=device)
    responses = torch.tensor(prefix["response"].astype(int).tolist(), dtype=torch.long, device=device).unsqueeze(0)
    with torch.no_grad():
        if model_name == "dkt":
            # DKT consumes the complete observed prefix. Its final hidden
            # state is mapped to the protected target concept.
            values = model(concepts, responses)
            return float(values[0, -1, int(target["concept_id"])].detach().cpu())
        if model_name == "saint":
            values = model(torch.cat((questions, target_question), dim=1), torch.cat((concepts, target_concept), dim=1), responses)
            return float(values[0, -1].detach().cpu())
        if model_name == "akt":
            values, _ = model(torch.cat((concepts, target_concept), dim=1), torch.cat((responses, torch.ones_like(target_concept)), dim=1), torch.cat((questions, target_question), dim=1))
            return float(values[0, -1].detach().cpu())
    raise ValueError(f"Unsupported model: {model_name}")


def collect_probe_predictions(
    model,
    model_name: str,
    probes: dict[str, dict[str, pd.DataFrame]],
    targets: pd.DataFrame,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Collect natural/plus/minus predictions and preserve target metadata."""
    rows: list[dict[str, Any]] = []
    for base_target_id, variants in probes.items():
        target = targets.loc[targets["event_id"] == base_target_id]
        if len(target) != 1:
            raise ValueError(f"Target metadata missing or duplicated: {base_target_id}")
        target = target.iloc[0]
        for variant, prefix in variants.items():
            rows.append(
                {
                    "base_target_id": base_target_id,
                    "variant": variant,
                    "prediction": predict_target(model, model_name, prefix, target),
                    "question_id": target["question_id"],
                    "concept_id": target["concept_id"],
                    "target_label": target["target_label"],
                }
            )
    result = pd.DataFrame(rows)
    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False)
    return result
