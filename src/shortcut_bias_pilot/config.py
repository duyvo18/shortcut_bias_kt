"""Configuration loading and validation for the shortcut-bias pilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
import os

from .env import configure_environment

configure_environment()


@dataclass(frozen=True)
class DataConfig:
    """Dataset and pyKT preprocessing settings."""

    name: str
    raw_path: str
    metadata_dir: str | None = None
    task_name: str | None = None
    min_seq_len: int = 3
    maxlen: int = 200
    kfold: int = 5


@dataclass(frozen=True)
class ThresholdConfig:
    """Pre-registered defaults for opportunity and probe eligibility."""

    item_min_support: int = 30
    local_min_support: int = 3
    remote_min_support: int = 5
    prior_low_quantile: float = 0.2
    prior_high_quantile: float = 0.8
    profile_low_max: float = 0.35
    profile_high_min: float = 0.65
    min_pairs_per_stratum: int = 50
    max_probe_fraction: float = 0.25
    bootstrap_replicates: int = 1000
    max_targets: int | None = None
    iap_max_items: int | None = None


@dataclass(frozen=True)
class TrainConfig:
    """Model/training settings passed to pyKT or the wrapper."""

    models: tuple[str, ...] = ("dkt", "saint", "akt")
    seeds: tuple[int, ...] = (42,)
    fold: int = 0
    batch_size: int = 64
    epochs: int = 1
    learning_rate: float = 1e-3
    device: str = "cuda"
    emb_size: int = 128
    dropout: float = 0.2
    cpu_threads: int = 20
    cpu_interop_threads: int = 2


@dataclass(frozen=True)
class PilotConfig:
    """Complete experiment configuration."""

    phase: str
    output_dir: str = "outputs"
    data: tuple[DataConfig, ...] = field(default_factory=tuple)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PilotConfig":
        """Load a YAML config and apply explicit dataclass defaults."""
        payload: dict[str, Any] = yaml.safe_load(Path(path).read_text()) or {}
        base_dir = Path(path).resolve().parent.parent
        data_items = []
        for item in payload.get("data", []):
            item = dict(item)
            item["raw_path"] = str((base_dir / item["raw_path"]).resolve()) if not Path(item["raw_path"]).is_absolute() else item["raw_path"]
            if item.get("metadata_dir") and not Path(item["metadata_dir"]).is_absolute():
                item["metadata_dir"] = str((base_dir / item["metadata_dir"]).resolve())
            data_items.append(item)
        data = tuple(DataConfig(**item) for item in data_items)
        thresholds = ThresholdConfig(**payload.get("thresholds", {}))
        train_payload = dict(payload.get("train", {}))
        if "cpu_threads" not in train_payload and os.getenv("PILOT_CPU_THREADS"):
            train_payload["cpu_threads"] = int(os.environ["PILOT_CPU_THREADS"])
        if "cpu_interop_threads" not in train_payload and os.getenv("PILOT_CPU_INTEROP_THREADS"):
            train_payload["cpu_interop_threads"] = int(os.environ["PILOT_CPU_INTEROP_THREADS"])
        if "models" in train_payload:
            train_payload["models"] = tuple(train_payload["models"])
        if "seeds" in train_payload:
            train_payload["seeds"] = tuple(train_payload["seeds"])
        train = TrainConfig(**train_payload)
        return cls(
            phase=payload["phase"],
            output_dir=payload.get("output_dir", "outputs"),
            data=data,
            thresholds=thresholds,
            train=train,
        )

    def validate(self) -> None:
        """Raise ``ValueError`` for settings that would invalidate the pilot."""
        if self.phase not in {"smoke", "screen", "cross-check"}:
            raise ValueError(f"Unsupported phase: {self.phase}")
        if not self.data:
            raise ValueError("At least one dataset must be configured")
        if self.thresholds.prior_low_quantile >= self.thresholds.prior_high_quantile:
            raise ValueError("Prior low quantile must be below high quantile")
        if not 0 < self.thresholds.max_probe_fraction <= 1:
            raise ValueError("max_probe_fraction must be in (0, 1]")
        if self.thresholds.max_targets is not None and self.thresholds.max_targets < 1:
            raise ValueError("max_targets must be positive when provided")
        if self.thresholds.iap_max_items is not None and self.thresholds.iap_max_items < 1:
            raise ValueError("iap_max_items must be positive when provided")
        if self.train.fold < 0:
            raise ValueError("fold must be non-negative")
        if self.train.device != "cuda":
            raise ValueError("The pilot requires CUDA; set device: cuda")
        if self.train.cpu_threads < 1 or self.train.cpu_interop_threads < 1:
            raise ValueError("CPU thread settings must be positive")
        available = os.cpu_count()
        if available is not None and self.train.cpu_threads > available:
            raise ValueError(f"cpu_threads={self.train.cpu_threads} exceeds available CPUs={available}")
