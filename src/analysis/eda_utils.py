"""Reusable helpers for Phase 5 exploratory analysis and static figures."""

from __future__ import annotations

import hashlib
import math
import textwrap
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
PURPLE = "#7B61A8"
GREY = "#9AA0A6"
DARK = "#263238"
LIGHT_GREY = "#E8EAED"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, encoding="utf-8", lineterminator="\n", float_format="%.10g")
    temporary.replace(path)


def trimmed_mean(values: pd.Series, proportion: float = 0.10) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna().sort_values().to_numpy()
    if len(clean) == 0:
        return np.nan
    trim = int(math.floor(len(clean) * proportion))
    if trim == 0 or 2 * trim >= len(clean):
        return float(clean.mean())
    return float(clean[trim:-trim].mean())


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return np.nan, np.nan
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    half_width = z * math.sqrt(
        proportion * (1 - proportion) / total + z**2 / (4 * total**2)
    ) / denominator
    return max(0.0, centre - half_width), min(1.0, centre + half_width)


def descriptive_row(
    source_table: str,
    grain: str,
    field: str,
    values: pd.Series,
    total_rows: int,
    note: str,
) -> dict[str, Any]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    quantiles = clean.quantile([0.05, 0.25, 0.75, 0.95, 0.99]) if len(clean) else pd.Series(dtype=float)
    return {
        "source_table": source_table,
        "unit_of_analysis": grain,
        "field": field,
        "total_row_count": total_rows,
        "valid_count": len(clean),
        "missing_count": total_rows - len(clean),
        "missing_percent": (total_rows - len(clean)) / total_rows * 100 if total_rows else np.nan,
        "mean": clean.mean() if len(clean) else np.nan,
        "trimmed_mean_10_percent": trimmed_mean(clean),
        "median": clean.median() if len(clean) else np.nan,
        "standard_deviation": clean.std() if len(clean) > 1 else np.nan,
        "minimum": clean.min() if len(clean) else np.nan,
        "percentile_05": quantiles.get(0.05, np.nan),
        "percentile_25": quantiles.get(0.25, np.nan),
        "percentile_75": quantiles.get(0.75, np.nan),
        "percentile_95": quantiles.get(0.95, np.nan),
        "percentile_99": quantiles.get(0.99, np.nan),
        "maximum": clean.max() if len(clean) else np.nan,
        "interpretation_note": note,
    }


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#B0B6BA",
        "axes.labelcolor": DARK,
        "axes.titlecolor": DARK,
        "xtick.color": DARK,
        "ytick.color": DARK,
        "text.color": DARK,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.grid": False,
        "savefig.facecolor": "white",
    })


def wrap_labels(values: list[str], width: int = 22) -> list[str]:
    return [textwrap.fill(str(value), width=width) for value in values]


def finish_figure(
    fig: plt.Figure,
    path: Path,
    source_note: str,
    bottom: float = 0.13,
) -> None:
    fig.text(0.01, 0.012, source_note, ha="left", va="bottom", fontsize=8, color="#5F6368")
    fig.subplots_adjust(bottom=bottom)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.png")
    fig.savefig(
        temporary,
        dpi=160,
        bbox_inches="tight",
        metadata={"Software": "Shopee Sales Analytics Phase 5"},
    )
    plt.close(fig)
    temporary.replace(path)
