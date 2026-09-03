"""End-to-end orchestration for preprocessing, smoke, and screen workloads."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import PilotConfig
from .data import load_pykt_sequences, split_prefix_target
from .eligibility import make_targets
from .metrics import pair_deltas, summarize_deltas
from .models import configure_torch_runtime, load_pykt_model, train_with_pykt
from .natural_metrics import natural_metrics
from .profiles import fit_item_prior
from .probes import ProbeSpec, build_iap_pair, build_lgt_pair, validate_pair
from .predictions import collect_probe_predictions, predict_target
from .pykt_adapter import load_generated_config, preprocess_dataset


def prepare_dataset(config: PilotConfig, dataset_name: str) -> tuple[Path, dict]:
    """Preprocess one configured dataset and return its output/config paths."""
    data = next(item for item in config.data if item.name == dataset_name)
    configure_torch_runtime(config.train)
    output = Path(config.output_dir) / "pykt_data" / data.name
    data_txt = preprocess_dataset(
        data.name,
        data.raw_path,
        output,
        metadata_dir=data.metadata_dir,
        task_name=data.task_name or "task_3_4",
        min_seq_len=data.min_seq_len,
        maxlen=data.maxlen,
        kfold=data.kfold,
        cpu_threads=config.train.cpu_threads,
    )
    return data_txt, load_generated_config(output / "pykt_data_config.json", data.name)


def run_probe_case(
    model,
    model_name: str,
    targets: pd.DataFrame,
    context: dict,
    case_id: str,
    output_path: Path,
    *,
    seed: int = 42,
    recent_k: int = 3,
    remote_fraction: float = 0.5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build and evaluate one case for one checkpoint."""
    probes = {}
    for _, target in targets.iterrows():
        if case_id == "IAP-01" and not target["eligible_iap"]:
            continue
        if case_id == "LGT-01" and not target["eligible_lgt"]:
            continue
        sequence, position = context[target["event_id"]]
        prefix, locked_target = split_prefix_target(sequence, position)
        spec = ProbeSpec(case_id, recent_k=recent_k, remote_fraction=remote_fraction, seed=seed)
        variants = build_iap_pair(prefix, locked_target, spec) if case_id == "IAP-01" else build_lgt_pair(prefix, locked_target, spec)
        validate_pair(variants, locked_target)
        probes[target["event_id"]] = variants
    if not probes:
        raise ValueError(f"No eligible targets for {case_id}")
    predictions = collect_probe_predictions(model, model_name, probes, targets)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output_path, index=False)
    deltas = pair_deltas(predictions)
    merged = deltas.merge(targets[["base_target_id", "prior_stratum", "n_local", "n_remote"]], on="base_target_id", how="left")
    return predictions, summarize_deltas(merged, "prior_stratum" if case_id == "IAP-01" else None)


def collect_natural_predictions(
    model,
    model_name: str,
    targets: pd.DataFrame,
    context: dict,
    output_path: Path,
) -> pd.DataFrame:
    """Collect one natural prediction per eligible protected target."""
    rows = []
    for _, target in targets.iterrows():
        sequence, position = context[target["event_id"]]
        prefix, locked_target = split_prefix_target(sequence, position)
        rows.append(
            {
                "event_id": target["event_id"],
                "question_id": target["question_id"],
                "concept_id": target["concept_id"],
                "target_label": target["target_label"],
                "prediction": predict_target(model, model_name, prefix, locked_target),
            }
        )
    result = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result


def run_model(
    config: PilotConfig,
    dataset_name: str,
    model_name: str,
    seed: int,
    *,
    run_training: bool = True,
) -> dict[str, str]:
    """Train/load a checkpoint and execute both protected-target cases."""
    data = next(item for item in config.data if item.name == dataset_name)
    configure_torch_runtime(config.train)
    root = Path(config.output_dir)
    pykt_dir = root / "pykt_data" / dataset_name
    generated = load_generated_config(pykt_dir / "pykt_data_config.json", dataset_name)
    train = config.train
    train = type(train)(
        models=(model_name,),
        seeds=train.seeds,
        fold=train.fold,
        batch_size=train.batch_size,
        epochs=train.epochs,
        learning_rate=train.learning_rate,
        device=train.device,
        emb_size=train.emb_size,
        dropout=train.dropout,
    )
    checkpoint = root / "checkpoints" / dataset_name / model_name / f"seed_{seed}" / f"fold_{train.fold}" / "qid_model.ckpt"
    if run_training:
        checkpoint = train_with_pykt(dataset_name, generated, train, seed, root / "checkpoints")
    model = load_pykt_model(model_name, generated, train, checkpoint)
    train_seq = load_pykt_sequences(pykt_dir / "train_valid_sequences_quelevel.csv")
    test_seq = load_pykt_sequences(pykt_dir / "test_sequences_quelevel.csv")
    profile = fit_item_prior(train_seq, min_support=config.thresholds.item_min_support)
    targets, context = make_targets(
        test_seq,
        profile,
        local_min_support=config.thresholds.local_min_support,
        remote_min_support=config.thresholds.remote_min_support,
        max_targets=config.thresholds.max_targets,
    )
    target_path = root / "targets" / dataset_name / f"seed_{seed}.csv"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    targets.to_csv(target_path, index=False)
    result = {"checkpoint": str(checkpoint), "targets": str(target_path)}
    natural_path = root / "predictions_natural" / dataset_name / model_name / f"seed_{seed}.csv"
    collect_natural_predictions(model, model_name, targets, context, natural_path)
    result["natural_predictions"] = str(natural_path)
    natural_summary_path = natural_path.with_name(natural_path.stem + "_metrics.json")
    natural_summary_path.write_text(json.dumps(natural_metrics(pd.read_csv(natural_path)), indent=2))
    result["natural_metrics"] = str(natural_summary_path)
    for case_id in ("IAP-01", "LGT-01"):
        pred_path = root / "predictions_probe" / dataset_name / model_name / f"seed_{seed}" / f"{case_id}.csv"
        _, summary = run_probe_case(model, model_name, targets, context, case_id, pred_path, seed=seed)
        summary_path = pred_path.with_name(f"{case_id}_summary.csv")
        summary.to_csv(summary_path, index=False)
        result[case_id] = str(summary_path)
    return result


def run_phase(config: PilotConfig, *, run_training: bool = True) -> list[dict[str, str]]:
    """Run configured model/dataset/seed combinations explicitly."""
    config.validate()
    results = []
    for data in config.data:
        prepare_dataset(config, data.name)
        for model_name in config.train.models:
            for seed in config.train.seeds:
                results.append(run_model(config, data.name, model_name, seed, run_training=run_training))
    manifest = Path(config.output_dir) / f"{config.phase}_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(results, indent=2))
    return results
