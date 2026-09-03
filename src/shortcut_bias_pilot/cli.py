"""Command-line entry points for setup and lightweight pilot utilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .env import configure_environment

configure_environment()

from .config import PilotConfig
from .pykt_adapter import _configure_preprocess_threads, preprocess_dataset


def _preprocess(args: argparse.Namespace) -> None:
    config = PilotConfig.from_yaml(args.config)
    config.validate()
    _configure_preprocess_threads(config.train.cpu_threads)
    data = next(item for item in config.data if item.name == args.dataset)
    output = Path(config.output_dir) / "pykt_data" / data.name
    path = preprocess_dataset(
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
    print(json.dumps({"dataset": data.name, "data_txt": str(path)}, indent=2))


def _run_phase(args: argparse.Namespace) -> None:
    """Run a configured phase; this is an explicit training workload."""
    config = PilotConfig.from_yaml(args.config)
    if config.phase != args.command:
        raise ValueError(f"Config phase {config.phase!r} does not match command {args.command!r}")
    _configure_preprocess_threads(config.train.cpu_threads)
    from .workflow import run_phase

    results = run_phase(config)
    print(json.dumps(results, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI parser."""
    parser = argparse.ArgumentParser(prog="shortcut-pilot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preprocess = subparsers.add_parser("preprocess", help="Run pyKT preprocessing")
    preprocess.add_argument("--config", required=True, type=Path)
    preprocess.add_argument("--dataset", required=True)
    preprocess.set_defaults(handler=_preprocess)
    for command in ("smoke", "screen"):
        runner = subparsers.add_parser(command, help=f"Run the {command} pilot phase")
        runner.add_argument("--config", required=True, type=Path)
        runner.set_defaults(handler=_run_phase)
    return parser


def main() -> None:
    """Execute the selected CLI command."""
    args = build_parser().parse_args()
    args.handler(args)
