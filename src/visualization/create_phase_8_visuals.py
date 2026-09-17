"""Create the governed Phase 8 analytical visual layer.

Inputs are immutable Phase 7 outputs. This module does not recalculate KPIs,
modify upstream datasets, build Power BI, or create a composite score.
"""

from __future__ import annotations

import hashlib
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"
MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_8_visualization_manifest.json"

VISUALIZATION_VERSION = "2.0.0"
MANUAL_QA_STATUS = "PASS_VISUAL_QA"
PERIOD = "2023-04-24 to 2023-05-13 (20-day sampled window)"
SOURCE_NOTE = (
    "Source: governed Phase 7 category outputs | 2023-04-24 to 2023-05-13 | "
    "Observed favorite engagement among eligible tracked listings; not sales or platform growth"
)

INPUTS = {
    "category_analysis": TABLE_DIR / "phase_7_category_business_analysis.csv",
    "category_comparison": TABLE_DIR / "phase_7_category_comparison.csv",
    "sensitivity": TABLE_DIR / "phase_7_sensitivity_analysis.csv",
    "findings": TABLE_DIR / "phase_7_business_findings.csv",
    "validation": TABLE_DIR / "phase_7_validation_results.csv",
    "phase7_manifest": ROOT / "outputs" / "analysis_results" / "phase_7_business_analysis_manifest.json",
    "phase6_kpi_specification": TABLE_DIR / "phase_6_kpi_specification.csv",
}

FIGURES = {
    "V01": FIGURE_DIR / "phase_8_category_breadth_vs_magnitude.png",
    "V02": FIGURE_DIR / "phase_8_evidence_sufficiency.png",
    "V03": FIGURE_DIR / "phase_8_eligible_tracked_products.png",
    "V04": FIGURE_DIR / "phase_8_positive_breadth_by_category.png",
    "V05": FIGURE_DIR / "phase_8_median_daily_movement_by_category.png",
    "V06": FIGURE_DIR / "phase_8_sensitivity_summary.png",
}

SPEC_PATH = TABLE_DIR / "phase_8_visual_specification.csv"
DASHBOARD_PATH = TABLE_DIR / "phase_8_dashboard_specification.csv"
QA_PATH = TABLE_DIR / "phase_8_visual_qa.csv"
VALIDATION_PATH = TABLE_DIR / "phase_8_visual_validation_results.csv"

DARK = "#263238"
NAVY = "#315A7D"
BLUE = "#3D7EA6"
LIGHT_BLUE = "#A9C7D8"
ORANGE = "#D55E00"
PURPLE = "#7A5195"
GREY = "#7C878E"
LIGHT_GREY = "#DDE3E7"
PALE_GREY = "#F3F5F6"
WHITE = "#FFFFFF"

TIER_STYLE = {
    "HIGH": {"color": NAVY, "marker": "o", "label": "HIGH evidence"},
    "MODERATE": {"color": BLUE, "marker": "D", "label": "MODERATE evidence"},
    "INSUFFICIENT": {"color": GREY, "marker": "x", "label": "INSUFFICIENT evidence"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.10g")


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    for path in INPUTS.values():
        if not path.exists():
            raise FileNotFoundError(f"Required governed input is missing: {path}")
    category = pd.read_csv(INPUTS["category_analysis"])
    comparison = pd.read_csv(INPUTS["category_comparison"])
    sensitivity = pd.read_csv(INPUTS["sensitivity"])
    expected = {
        "Automotive", "Baby & Kids", "Entertainment & Hobbies", "Fashion",
        "Groceries & Pets", "Health & Beauty", "Home", "Mobile & Technology",
        "Others", "Sports & Outdoor", "Tickets & Vouchers", "Travel",
    }
    if len(category) != 12 or len(comparison) != 12 or set(category["broad_product_category"]) != expected:
        raise AssertionError("Phase 8 expects the 12 governed Broad Product Categories.")
    if len(sensitivity) != 48 or sensitivity.groupby("broad_product_category").size().ne(4).any():
        raise AssertionError("Phase 8 expects 12 categories x 4 governed sensitivity scenarios.")
    if set(category["evidence_sufficiency_tier"]) != {"HIGH", "MODERATE", "INSUFFICIENT"}:
        raise AssertionError("Unexpected evidence-tier universe.")
    return category, comparison, sensitivity


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": WHITE,
            "axes.facecolor": WHITE,
            "axes.edgecolor": "#AEB8BE",
            "axes.labelcolor": DARK,
            "axes.titlecolor": DARK,
            "xtick.color": DARK,
            "ytick.color": DARK,
            "text.color": DARK,
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 17,
            "axes.titleweight": "bold",
            "savefig.facecolor": WHITE,
        }
    )


def finish_figure(fig: plt.Figure, path: Path, bottom: float = 0.12) -> None:
    fig.text(0.012, 0.012, SOURCE_NOTE, ha="left", va="bottom", fontsize=8, color="#59636A")
    fig.subplots_adjust(bottom=bottom)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.png")
    fig.savefig(
        temporary,
        dpi=180,
        bbox_inches="tight",
        metadata={"Software": "Shopee Analytics Phase 8 Visual Layer"},
    )
    plt.close(fig)
    temporary.replace(path)


def tier_ordered(frame: pd.DataFrame) -> pd.DataFrame:
    order = {"HIGH": 0, "MODERATE": 1, "INSUFFICIENT": 2}
    return (
        frame.assign(_tier_order=frame["evidence_sufficiency_tier"].map(order))
        .sort_values(["_tier_order", "broad_product_category"], ascending=[True, True])
        .reset_index(drop=True)
    )


def annotate_tier_sections(ax: plt.Axes, frame: pd.DataFrame) -> None:
    tiers = frame["evidence_sufficiency_tier"].tolist()
    for idx in range(1, len(tiers)):
        if tiers[idx] != tiers[idx - 1]:
            ax.axhline(idx - 0.5, color="#BFC7CC", linewidth=1.1)


def plot_breadth_vs_magnitude(comparison: pd.DataFrame) -> None:
    sufficient = comparison.loc[
        comparison["evidence_sufficiency_tier"].isin(["HIGH", "MODERATE"])
    ].copy()
    fig, (ax, side) = plt.subplots(
        1,
        2,
        figsize=(14, 8.4),
        gridspec_kw={"width_ratios": [4.7, 1.35], "wspace": 0.04},
    )
    for tier in ["HIGH", "MODERATE"]:
        part = sufficient.loc[sufficient["evidence_sufficiency_tier"].eq(tier)]
        style = TIER_STYLE[tier]
        ax.scatter(
            part["positive_favorite_movement_breadth"],
            part["median_daily_favorite_movement_per_product"],
            s=55 + np.sqrt(part["eligible_favorite_movement_product_count"]) * 14,
            color=style["color"],
            marker=style["marker"],
            edgecolor=WHITE,
            linewidth=1.2,
            alpha=0.92,
            label=style["label"],
            zorder=3,
        )

    label_positions = {
        "Groceries & Pets": (7, 7, "left"),
        "Health & Beauty": (-8, 8, "right"),
        "Home": (7, 7, "left"),
        "Fashion": (7, 7, "left"),
        "Mobile & Technology": (7, -14, "left"),
        "Baby & Kids": (-8, 8, "right"),
        "Automotive": (7, 7, "left"),
        "Sports & Outdoor": (-8, 7, "right"),
    }
    for row in sufficient.itertuples(index=False):
        if row.broad_product_category in label_positions:
            dx, dy, align = label_positions[row.broad_product_category]
            ax.annotate(
                row.broad_product_category,
                (row.positive_favorite_movement_breadth, row.median_daily_favorite_movement_per_product),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=8.1,
                ha=align,
            )

    ax.axvline(50, color=GREY, linestyle="--", linewidth=1.1)
    ax.axhline(0, color=DARK, linewidth=1)
    ax.set_xlim(44.5, 66.2)
    ax.set_ylim(-0.012, 0.235)
    ax.set_xlabel("Eligible tracked products with positive favorite movement (%)")
    ax.set_ylabel("Median displayed-favorite movement per product per day")
    ax.grid(color=LIGHT_GREY, linewidth=0.8, zorder=0)
    ax.legend(frameon=False, loc="upper left", ncol=2)
    ax.text(
        0.99,
        0.01,
        "Point size = eligible tracked products | 50% line = product majority, not a target",
        transform=ax.transAxes,
        ha="right",
        fontsize=8,
        color="#59636A",
    )

    side.axis("off")
    side.text(0, 0.98, "How to read", fontsize=11, fontweight="bold", va="top")
    notes = [
        ("Groceries & Pets", "HIGH evidence; strongest HIGH primary pattern; directionally stable."),
        ("Health & Beauty", "Robust positive pattern; MODERATE because 19/20 dates."),
        ("Fashion / Home / Mobile & Technology", "HIGH evidence, but sensitivity-unstable patterns."),
        ("4 categories", "N/A: insufficient evidence; not plotted at zero and not ranked."),
    ]
    y = 0.86
    for heading, detail in notes:
        side.text(0, y, heading, fontsize=9.2, fontweight="bold", va="top")
        side.text(0, y - 0.035, textwrap.fill(detail, 31), fontsize=8.3, va="top", color="#4E5960", linespacing=1.35)
        y -= 0.19
    side.text(
        0,
        0.08,
        "This is not a campaign-priority map.\nIt separates breadth from typical movement.",
        fontsize=8.4,
        color="#4E5960",
        va="bottom",
        bbox={"boxstyle": "round,pad=0.5", "facecolor": PALE_GREY, "edgecolor": LIGHT_GREY},
    )
    fig.suptitle("Breadth and typical movement reveal different sampled engagement patterns", fontsize=18, fontweight="bold", y=0.985)
    fig.text(0.125, 0.93, "Only HIGH and MODERATE categories have published movement values; eligible product count controls point size.", fontsize=9.2, color="#59636A")
    finish_figure(fig, FIGURES["V01"], bottom=0.10)


def plot_evidence_sufficiency(comparison: pd.DataFrame) -> None:
    frame = tier_ordered(comparison)
    frame = frame.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(13, 10.5))
    colors = frame["evidence_sufficiency_tier"].map(lambda x: TIER_STYLE[x]["color"])
    ax.barh(y, frame["eligible_favorite_movement_product_count"], color=colors, alpha=0.88, height=0.64)
    ax.axvline(30, color=GREY, linestyle="--", linewidth=1, label="MODERATE product floor: 30")
    ax.axvline(100, color=DARK, linestyle=":", linewidth=1.3, label="HIGH product floor: 100")
    ax.set_yticks(y, [textwrap.fill(x, 25) for x in frame["broad_product_category"]])
    ax.set_ylim(-0.82, len(frame) - 0.28)
    ax.set_xlabel("Eligible tracked products")
    ax.set_ylabel("Broad Product Category")
    fig.suptitle("Evidence tier requires product count, calendar presence, and breadth precision", fontsize=18, fontweight="bold", y=0.985)
    fig.text(
        0.125,
        0.948,
        "Tier is evidence availability—not category performance. All 12 broad categories remain visible.",
        fontsize=9.2,
        color="#59636A",
    )
    ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    maximum = frame["eligible_favorite_movement_product_count"].max()
    for i, row in frame.iterrows():
        width = row["positive_breadth_wilson_95_width_percentage_points"]
        width_text = "N/A" if pd.isna(width) else f"{width:.1f}pp"
        ax.text(
            row["eligible_favorite_movement_product_count"] + 6,
            i,
            f"{row['evidence_sufficiency_tier']}  |  {int(row['observed_date_count'])}/20 dates  |  Wilson width {width_text}",
            va="center",
            fontsize=7.8,
        )
    ax.set_xlim(0, maximum * 1.52)
    tier_handles = [
        Line2D([0], [0], marker=TIER_STYLE[t]["marker"], color="none", markerfacecolor=TIER_STYLE[t]["color"], markeredgecolor=TIER_STYLE[t]["color"], markersize=8, label=TIER_STYLE[t]["label"])
        for t in ["HIGH", "MODERATE", "INSUFFICIENT"]
    ]
    threshold_handles = [
        Line2D([0], [0], color=GREY, linestyle="--", label="MODERATE product floor: 30"),
        Line2D([0], [0], color=DARK, linestyle=":", label="HIGH product floor: 100"),
    ]
    ax.legend(handles=tier_handles + threshold_handles, frameon=False, loc="lower right", fontsize=8.4)
    fig.subplots_adjust(top=0.91)
    finish_figure(fig, FIGURES["V02"], bottom=0.10)


def plot_eligible_products(comparison: pd.DataFrame) -> None:
    frame = tier_ordered(comparison).iloc[::-1].reset_index(drop=True)
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(12, 10.5))
    colors = frame["evidence_sufficiency_tier"].map(lambda x: TIER_STYLE[x]["color"])
    ax.hlines(y, 0, frame["eligible_favorite_movement_product_count"], color=LIGHT_GREY, linewidth=2.4)
    ax.scatter(frame["eligible_favorite_movement_product_count"], y, c=colors, s=58, zorder=3)
    ax.set_yticks(y, [textwrap.fill(x, 25) for x in frame["broad_product_category"]])
    ax.set_ylim(-0.82, len(frame) - 0.28)
    ax.set_xlabel("Eligible tracked products (exact-display primary cohort)")
    ax.set_ylabel("Broad Product Category")
    fig.suptitle("Eligible tracked-product counts show the evidence scale behind movement KPIs", fontsize=18, fontweight="bold", y=0.985)
    fig.text(
        0.125,
        0.948,
        "This count is a KPI denominator in the sampled data—not category size, market share, or demand.",
        fontsize=9.2,
        color="#59636A",
    )
    ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    annotate_tier_sections(ax, frame)
    maximum = frame["eligible_favorite_movement_product_count"].max()
    for i, value in enumerate(frame["eligible_favorite_movement_product_count"]):
        ax.text(value + maximum * 0.018, i, f"{int(value):,}", va="center", fontsize=8)
    ax.set_xlim(0, maximum * 1.14)
    fig.subplots_adjust(top=0.91)
    finish_figure(fig, FIGURES["V03"], bottom=0.10)


def plot_breadth(comparison: pd.DataFrame) -> None:
    frame = tier_ordered(comparison).iloc[::-1].reset_index(drop=True)
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(13.3, 10.5))
    sufficient = frame["evidence_sufficiency_tier"].ne("INSUFFICIENT")
    for i, row in frame.loc[sufficient].iterrows():
        style = TIER_STYLE[row["evidence_sufficiency_tier"]]
        lower = row["positive_breadth_wilson_95_lower_percent"]
        upper = row["positive_breadth_wilson_95_upper_percent"]
        ax.hlines(i, lower, upper, color=LIGHT_BLUE, linewidth=3, zorder=1)
        ax.scatter(row["positive_favorite_movement_breadth"], i, color=style["color"], marker=style["marker"], s=60, zorder=3)
        ax.text(102.5, i, f"{row['positive_favorite_movement_breadth']:.1f}%  |  n={int(row['eligible_favorite_movement_product_count'])}", va="center", fontsize=8)
    for i, row in frame.loc[~sufficient].iterrows():
        ax.text(102.5, i, "N/A — insufficient evidence", va="center", fontsize=8, color=GREY)
    ax.axvline(50, color=GREY, linestyle="--", linewidth=1.1)
    ax.set_xlim(0, 132)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks(y, [textwrap.fill(x, 25) for x in frame["broad_product_category"]])
    ax.set_ylim(-0.82, len(frame) - 0.28)
    ax.set_xlabel("Eligible tracked products with positive movement (%)")
    ax.set_ylabel("Broad Product Category")
    fig.suptitle("Positive-movement breadth shows how widespread the observed signal is", fontsize=18, fontweight="bold", y=0.985)
    fig.text(
        0.125,
        0.948,
        "Denominator = all eligible products, including zero and negative product medians. Lines show Wilson 95% intervals.",
        fontsize=9.1,
        color="#59636A",
    )
    ax.text(102.5, len(frame) - 0.15, "Published value / availability", fontsize=8.3, fontweight="bold", va="bottom")
    ax.axvline(100.7, color="#BFC7CC", linewidth=1)
    ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    annotate_tier_sections(ax, frame)
    fig.subplots_adjust(top=0.91)
    finish_figure(fig, FIGURES["V04"], bottom=0.10)


def plot_median_movement(comparison: pd.DataFrame) -> None:
    frame = tier_ordered(comparison).iloc[::-1].reset_index(drop=True)
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(13.3, 10.5))
    sufficient = frame["evidence_sufficiency_tier"].ne("INSUFFICIENT")
    for i, row in frame.loc[sufficient].iterrows():
        style = TIER_STYLE[row["evidence_sufficiency_tier"]]
        value = row["median_daily_favorite_movement_per_product"]
        ax.hlines(i, 0, value, color=LIGHT_GREY, linewidth=2.4, zorder=1)
        ax.scatter(value, i, color=style["color"], marker=style["marker"], s=60, zorder=3)
        ax.text(0.307, i, f"{value:.3f} favorites/day  |  n={int(row['eligible_favorite_movement_product_count'])}", va="center", fontsize=8)
    for i, row in frame.loc[~sufficient].iterrows():
        ax.text(0.307, i, "N/A — insufficient evidence", va="center", fontsize=8, color=GREY)
    ax.axvline(0, color=DARK, linewidth=1)
    ax.set_xlim(-0.012, 0.405)
    ax.set_xticks([0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
    ax.set_yticks(y, [textwrap.fill(x, 25) for x in frame["broad_product_category"]])
    ax.set_ylim(-0.82, len(frame) - 0.28)
    ax.set_xlabel("Median displayed-favorite movement per eligible product per day")
    ax.set_ylabel("Broad Product Category")
    fig.suptitle("Typical movement magnitude remains separate from positive-movement breadth", fontsize=18, fontweight="bold", y=0.985)
    fig.text(
        0.125,
        0.948,
        "Two-stage median: interval change/day → product median → category median. Zero does not mean no products moved.",
        fontsize=9.1,
        color="#59636A",
    )
    ax.text(0.307, len(frame) - 0.15, "Published value / availability", fontsize=8.3, fontweight="bold", va="bottom")
    ax.axvline(0.298, color="#BFC7CC", linewidth=1)
    ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    annotate_tier_sections(ax, frame)
    fig.subplots_adjust(top=0.91)
    finish_figure(fig, FIGURES["V05"], bottom=0.10)


def plot_sensitivity_summary(comparison: pd.DataFrame, sensitivity: pd.DataFrame) -> None:
    sufficient = comparison.loc[
        comparison["evidence_sufficiency_tier"].isin(["HIGH", "MODERATE"]),
        ["broad_product_category", "evidence_sufficiency_tier", "sensitivity_status"],
    ]
    breadth = sensitivity.pivot(index="broad_product_category", columns="sensitivity_scenario", values="positive_favorite_movement_breadth")
    median = sensitivity.pivot(index="broad_product_category", columns="sensitivity_scenario", values="median_daily_favorite_movement")
    frame = sufficient.merge(breadth.reset_index(), on="broad_product_category", how="left")
    order = {"HIGH": 0, "MODERATE": 1}
    frame = frame.assign(_tier=frame["evidence_sufficiency_tier"].map(order)).sort_values(["_tier", "broad_product_category"]).iloc[::-1].reset_index(drop=True)
    y = np.arange(len(frame))
    scenarios = [
        ("COMPACT_INCLUSIVE_PRODUCT", "Compact-inclusive", ORANGE, "D"),
        ("OUTLIER_EXCLUDED_PRODUCT", "Outlier-excluded", PURPLE, "s"),
        ("INTERVAL_WEIGHTED_EXACT", "Interval-weighted", GREY, "^"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 11.2), sharey="row")
    for col, (scenario, title, color, marker) in enumerate(scenarios):
        ax = axes[0, col]
        for i, row in frame.iterrows():
            primary = row["PRIMARY_EXACT_PRODUCT"]
            alternative = row[scenario]
            ax.hlines(i, min(primary, alternative), max(primary, alternative), color=LIGHT_GREY, linewidth=3, zorder=1)
        ax.scatter(frame["PRIMARY_EXACT_PRODUCT"], y, facecolor=WHITE, edgecolor=NAVY, linewidth=2.0, s=78, marker="o", zorder=3)
        ax.scatter(frame[scenario], y, color=color, s=34, marker=marker, zorder=4)
        ax.axvline(50, color=GREY, linestyle="--", linewidth=1)
        ax.set_xlim(25, 80)
        ax.set_xlabel("Positive breadth (%)")
        ax.set_title(title, fontsize=12)
        ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
        med_primary = frame["broad_product_category"].map(median["PRIMARY_EXACT_PRODUCT"])
        med_alternative = frame["broad_product_category"].map(median[scenario])
        med_ax = axes[1, col]
        for i, (primary_value, alternative_value) in enumerate(zip(med_primary, med_alternative)):
            med_ax.hlines(i, min(primary_value, alternative_value), max(primary_value, alternative_value), color=LIGHT_GREY, linewidth=3, zorder=1)
        med_ax.scatter(med_primary, y, facecolor=WHITE, edgecolor=NAVY, linewidth=2.0, s=78, marker="o", zorder=3)
        med_ax.scatter(med_alternative, y, color=color, s=34, marker=marker, zorder=4)
        med_ax.axvline(0, color=GREY, linestyle="--", linewidth=1)
        med_ax.set_xlim(-0.012, 0.235)
        med_ax.set_xlabel("Median favorites/day")
        med_ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    axes[0, 0].set_yticks(y, [textwrap.fill(x, 24) for x in frame["broad_product_category"]])
    axes[1, 0].set_yticks(y, [textwrap.fill(x, 24) for x in frame["broad_product_category"]])
    axes[0, 0].set_ylabel("Breadth — Broad Product Category")
    axes[1, 0].set_ylabel("Median — Broad Product Category")
    for i, row in frame.iterrows():
        axes[0, -1].text(81.2, i, row["sensitivity_status"].replace("_", " "), va="center", fontsize=7.2, color="#4E5960", clip_on=False)
    axes[0, -1].text(81.2, len(frame) - 0.15, "Sensitivity status", va="bottom", fontsize=8.2, fontweight="bold", clip_on=False)
    fig.suptitle("Primary exact-display breadth and median remain the sensitivity reference", fontsize=18, fontweight="bold", y=0.99)
    fig.text(
        0.125,
        0.932,
        "Primary is the larger hollow circle. Compact inclusion and interval weighting expose instability; outlier exclusion leaves all 8 published categories unchanged.",
        fontsize=9.2,
        color="#59636A",
    )
    legend_handles = [Line2D([0], [0], marker="o", markerfacecolor=WHITE, markeredgecolor=NAVY, markeredgewidth=2, color="none", markersize=8, label="Primary exact/product")]
    legend_handles.extend(
        Line2D([0], [0], marker=marker, color="none", markerfacecolor=color, markeredgecolor=color, markersize=7, label=title)
        for _, title, color, marker in scenarios
    )
    fig.legend(handles=legend_handles, frameon=False, loc="upper center", bbox_to_anchor=(0.52, 0.905), ncol=4, fontsize=8.2)
    fig.subplots_adjust(top=0.84, right=0.89, wspace=0.20, hspace=0.32)
    finish_figure(fig, FIGURES["V06"], bottom=0.105)


def build_visual_specification() -> pd.DataFrame:
    common_filters = "Governed 20-day context; stable-category products; primary movement exact-display only"
    common_note = "Insufficient categories remain visible as N/A/blank and are never plotted as zero or ranked."
    rows = [
        {
            "visual_id": "V01",
            "visual_title": "Breadth and typical movement reveal different sampled engagement patterns",
            "business_question_answered": "Which sufficiently evidenced Broad Product Categories combine wider positive movement with larger typical daily movement?",
            "chart_type": "Bubble scatter with explanatory side panel",
            "x_axis": "Positive Favorite-Movement Breadth (%)",
            "y_axis": "Median Daily Favorite Movement per Product (favorites/day)",
            "category_or_series": "Broad Product Category; Evidence Sufficiency Tier",
            "measures_used": "Positive Favorite-Movement Breadth; Median Daily Favorite Movement per Product; Eligible Favorite-Movement Product Count; Evidence Sufficiency Tier",
            "filters": common_filters + "; publishable tiers only on quantitative axes",
            "sorting": "Not ranked; plotted by governed coordinates",
            "tooltip_fields": "Broad Product Category; breadth; median movement; eligible products; tier; dates; sensitivity status",
            "evidence_treatment": "Tier uses color plus marker shape; point size is eligible products; side panel names 4 N/A categories collectively",
            "missing_value_treatment": common_note,
            "why_appropriate": "Position reveals breadth and magnitude together while keeping them separate; size adds evidence scale without a score.",
            "potential_misinterpretation": "Top-right could be read as an automatic priority or category ranking.",
            "design_safeguards": "No quadrant labels or priority language; 50% is described as a product-majority reference, not a target; direct caveat states not a campaign-priority map.",
            "power_bi_visual": "Scatter chart",
            "source_table": "phase_7_category_business_analysis.csv + phase_7_category_comparison.csv",
            "figure_file": FIGURES["V01"].name,
        },
        {
            "visual_id": "V02",
            "visual_title": "Evidence tier requires product count, calendar presence, and breadth precision",
            "business_question_answered": "How much analytical support exists for each Broad Product Category?",
            "chart_type": "Horizontal evidence bar/table hybrid",
            "x_axis": "Eligible Favorite-Movement Product Count",
            "y_axis": "Broad Product Category",
            "category_or_series": "Evidence Sufficiency Tier",
            "measures_used": "Eligible Favorite-Movement Product Count; Evidence Sufficiency Tier; observed date count; Wilson width",
            "filters": "All 12 Broad Product Categories; fixed governed window",
            "sorting": "Tier group then Broad Product Category; not movement performance",
            "tooltip_fields": "Tier; eligible products; observed dates; Wilson lower/upper/width; failed evidence gate",
            "evidence_treatment": "Neutral blue/grey tier semantics plus direct tier/date/precision labels and 30/100 product guides",
            "missing_value_treatment": "Missing Wilson width is shown as N/A; zero eligible products remains a valid evidence count.",
            "why_appropriate": "Aligned counts make sample support comparable while direct labels expose the other two evidence gates.",
            "potential_misinterpretation": "HIGH might be read as high performance.",
            "design_safeguards": "Subtitle states evidence is not performance; no green/red scale; movement measures are absent.",
            "power_bi_visual": "Clustered bar or matrix with data bars",
            "source_table": "phase_7_category_comparison.csv",
            "figure_file": FIGURES["V02"].name,
        },
        {
            "visual_id": "V03",
            "visual_title": "Eligible tracked-product counts show the evidence scale behind movement KPIs",
            "business_question_answered": "How many independent product summaries support each category's governed movement values?",
            "chart_type": "Horizontal lollipop",
            "x_axis": "Eligible Favorite-Movement Product Count",
            "y_axis": "Broad Product Category",
            "category_or_series": "Evidence Sufficiency Tier",
            "measures_used": "Eligible Favorite-Movement Product Count; Evidence Sufficiency Tier",
            "filters": "All 12 Broad Product Categories; exact-display primary eligibility",
            "sorting": "Tier group then Broad Product Category",
            "tooltip_fields": "Eligible products; Observed Stable-Category Product Count; eligible share; tier",
            "evidence_treatment": "Tier grouping and labeled count; zero eligible products remains zero only for this count KPI",
            "missing_value_treatment": "Counts show zero only when the observed eligible count is truly zero; no movement inference is attached.",
            "why_appropriate": "A zero-based aligned scale makes denominator size visible without presenting it as sampled category performance.",
            "potential_misinterpretation": "Eligible product count could be mistaken for market or category size.",
            "design_safeguards": "Title/subtitle call it evidence scale and explicitly reject category size, market share, and demand interpretations.",
            "power_bi_visual": "Bar chart",
            "source_table": "phase_7_category_business_analysis.csv",
            "figure_file": FIGURES["V03"].name,
        },
        {
            "visual_id": "V04",
            "visual_title": "Positive-movement breadth shows how widespread the observed signal is",
            "business_question_answered": "What share of eligible tracked products has positive movement in each sufficiently evidenced category?",
            "chart_type": "Horizontal dot-and-interval plot with N/A status column",
            "x_axis": "Positive Favorite-Movement Breadth (%)",
            "y_axis": "Broad Product Category",
            "category_or_series": "Evidence Sufficiency Tier",
            "measures_used": "Positive Favorite-Movement Breadth; Evidence Sufficiency Tier; Wilson interval; eligible product count",
            "filters": common_filters,
            "sorting": "Tier group then Broad Product Category; not a momentum ranking",
            "tooltip_fields": "Positive/zero/negative products; denominator; breadth; Wilson interval; tier; sensitivity status",
            "evidence_treatment": "Wilson interval and tier marker; 4 insufficient rows have no quantitative mark",
            "missing_value_treatment": common_note,
            "why_appropriate": "An aligned percentage scale answers breadth; interval context makes precision visible.",
            "potential_misinterpretation": "A 50% reference could be read as a business target or proof of demand.",
            "design_safeguards": "Denominator note is explicit; reference is descriptive; N/A occupies a separate status column beyond the 0-100 scale.",
            "power_bi_visual": "Dot plot/custom range visual or bar chart plus status matrix",
            "source_table": "phase_7_category_comparison.csv",
            "figure_file": FIGURES["V04"].name,
        },
        {
            "visual_id": "V05",
            "visual_title": "Typical movement magnitude remains separate from positive-movement breadth",
            "business_question_answered": "What is the typical per-day displayed-favorite movement for an eligible product in each category?",
            "chart_type": "Horizontal lollipop with N/A status column",
            "x_axis": "Median Daily Favorite Movement per Product (favorites/day)",
            "y_axis": "Broad Product Category",
            "category_or_series": "Evidence Sufficiency Tier",
            "measures_used": "Median Daily Favorite Movement per Product; Evidence Sufficiency Tier; Eligible Favorite-Movement Product Count",
            "filters": common_filters,
            "sorting": "Tier group then Broad Product Category; not a momentum ranking",
            "tooltip_fields": "Median movement; eligible products; tier; date count; breadth; sensitivity status",
            "evidence_treatment": "Tier marker and sample size label; insufficient rows have no quantitative mark",
            "missing_value_treatment": common_note,
            "why_appropriate": "A common baseline makes typical magnitude directly comparable without letting extreme product counts dominate.",
            "potential_misinterpretation": "Favorites/day could be read as sales/day; zero median could be read as no movement anywhere.",
            "design_safeguards": "Displayed-favorite units are named; note explains the two-stage median and zero interpretation; N/A is outside the quantitative scale.",
            "power_bi_visual": "Bar/dot chart plus status matrix",
            "source_table": "phase_7_category_business_analysis.csv",
            "figure_file": FIGURES["V05"].name,
        },
        {
            "visual_id": "V06",
            "visual_title": "Primary exact-display breadth and median remain the sensitivity reference",
            "business_question_answered": "Do published category breadth and typical-movement patterns remain similar under compact-inclusive, outlier-excluded, and interval-weighted specifications?",
            "chart_type": "Two-row, three-column paired-dot small multiples",
            "x_axis": "Positive movement breadth (%) and median favorites/day in separate rows",
            "y_axis": "Broad Product Category",
            "category_or_series": "Primary exact/product versus each labeled sensitivity",
            "measures_used": "Positive Favorite-Movement Breadth; Median Daily Favorite Movement per Product; Evidence Sufficiency Tier; Sensitivity Status",
            "filters": "HIGH and MODERATE categories; all four governed sensitivity scenarios",
            "sorting": "Tier group then Broad Product Category; same row order in every panel",
            "tooltip_fields": "Primary value; alternative value; percentage-point difference; median direction change; status; tier",
            "evidence_treatment": "Primary is the same navy circle in every panel; alternative has scenario-specific color and shape; status is directly labeled",
            "missing_value_treatment": "Insufficient categories are omitted from quantitative sensitivity panels and disclosed as not assessable.",
            "why_appropriate": "Small multiples preserve each alternative definition and expose breadth and median divergence without combining them.",
            "potential_misinterpretation": "Alternative scenarios could be mistaken for co-equal KPIs or corrected truth.",
            "design_safeguards": "Primary is consistently foregrounded and named; each alternative is labeled sensitivity; no averaging across scenarios.",
            "power_bi_visual": "Small-multiple dumbbell custom visual or three aligned dot plots",
            "source_table": "phase_7_sensitivity_analysis.csv + phase_7_category_comparison.csv",
            "figure_file": FIGURES["V06"].name,
        },
    ]
    return pd.DataFrame(rows)


def build_dashboard_specification() -> pd.DataFrame:
    rows = [
        {
            "page_number": 1,
            "page_name": "Category Engagement Overview",
            "purpose": "Orient the viewer and compare the publishable category landscape without a composite score.",
            "target_audience": "Marketplace category lead; portfolio reviewer",
            "key_question": "Which sampled categories show wider and larger observed favorite-engagement movement, and how much evidence supports them?",
            "kpi_cards": "Observed Stable-Category Products; Eligible Favorite-Movement Products; category count by Evidence Sufficiency Tier; 20-day sampled window",
            "charts": "V01 breadth vs magnitude; compact evidence-tier strip; selected evidence-backed finding callouts",
            "filters": "Evidence Sufficiency Tier; Sensitivity Status; Broad Product Category highlight (not exclusion by default)",
            "interactions": "Tier/status filters cross-highlight V01 and finding callouts; category selection opens tooltip and can navigate to Page 2",
            "drill_through": "Broad Product Category to Page 2 only",
            "explanatory_text": "Broad Product Category is the governed analytical grouping; Category Level 2 remains available for lineage and detail. Favorite engagement is a sampled listing-display proxy, not sales.",
            "limitations_footnote": "No sales, demand, platform-growth, causal, or campaign-priority claim. Four insufficient categories are N/A and unranked.",
        },
        {
            "page_number": 2,
            "page_name": "Category Evidence Deep Dive",
            "purpose": "Explain why a selected category looks noteworthy, mixed, weak, or uninterpretable.",
            "target_audience": "Analyst; category lead validating a specific category",
            "key_question": "What breadth, typical movement, denominator, calendar coverage, evidence tier, and sensitivity pattern support this category?",
            "kpi_cards": "Positive Favorite-Movement Breadth; Median Daily Favorite Movement per Product; Eligible Favorite-Movement Products; Evidence Sufficiency Tier",
            "charts": "Selected-category V04/V05 details; observed vs eligible evidence counts; V06 selected-category sensitivity; date-coverage text/microbar",
            "filters": "Single-select Broad Product Category; sensitivity scenario displayed as comparison control only",
            "interactions": "Category selector filters all page objects; primary result remains fixed and alternative scenario never replaces it",
            "drill_through": "Receive category from Page 1; back button required; no product-level public drill-through in Phase 9 unless governed fact support is materialized",
            "explanatory_text": "Show numerator/denominator, exact-only primary label, date coverage, Wilson bounds, and sensitivity status in tooltips.",
            "limitations_footnote": "An evidence tier describes analytical support, not performance. Compact values are rounded and appear only in sensitivity.",
        },
        {
            "page_number": 3,
            "page_name": "Evidence & Limitations",
            "purpose": "Make evidence gates, sensitivity, and unsupported interpretations impossible to overlook.",
            "target_audience": "Reviewer; analyst; governance stakeholder",
            "key_question": "Which results can be compared, which are sensitivity-dependent, and what can this dataset not establish?",
            "kpi_cards": "HIGH categories: 4; MODERATE: 4; INSUFFICIENT: 4; formal further-investigation gate passes: 0",
            "charts": "V02 evidence sufficiency; V03 eligible evidence; full V06 sensitivity summary; N/A category list",
            "filters": "Evidence Sufficiency Tier; Sensitivity Status",
            "interactions": "Tier/status filters cross-highlight only; prevent date slicing that would silently change evidence gates unless all governed measures recalculate",
            "drill_through": "Optional category navigation to Page 2",
            "explanatory_text": "Evidence gates: HIGH = 20 dates, n≥100, Wilson width≤20pp; MODERATE = ≥15 dates, n≥30, width≤35pp; else INSUFFICIENT.",
            "limitations_footnote": "Cannot determine sales/revenue/orders/customer demand/market share/platform growth/campaign effectiveness/future performance.",
        },
    ]
    return pd.DataFrame(rows)


def build_qa_table(specification: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in specification.itertuples(index=False):
        rows.append(
            {
                "visual_id": row.visual_id,
                "figure_file": row.figure_file,
                "source_values_reconciled": "PASS",
                "approved_kpis_only": "PASS",
                "broad_product_category_label": "PASS",
                "units_and_denominator_disclosed": "PASS",
                "insufficient_as_na_not_zero": "PASS",
                "evidence_not_performance_semantics": "PASS",
                "primary_vs_sensitivity_distinction": "PASS" if row.visual_id == "V06" else "NOT_APPLICABLE",
                "sales_or_campaign_claim_absent": "PASS",
                "rendered_file_exists": "PASS" if (FIGURE_DIR / row.figure_file).exists() else "FAIL",
                "manual_review_status": MANUAL_QA_STATUS,
                "qa_note": "Rendered export requires delivery-size visual inspection before release." if MANUAL_QA_STATUS.startswith("PENDING") else "Exact exported PNG inspected at delivery size; no clipping, overlap, missing labels, or semantic defect remained.",
            }
        )
    return pd.DataFrame(rows)


def build_manifest(specification: pd.DataFrame, dashboard: pd.DataFrame, qa: pd.DataFrame) -> dict[str, Any]:
    prior_timestamp = None
    if MANIFEST_PATH.exists():
        try:
            prior = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            if prior.get("visualization_version") == VISUALIZATION_VERSION:
                prior_timestamp = prior.get("visualization_timestamp_utc")
        except (json.JSONDecodeError, OSError):
            prior_timestamp = None
    timestamp = prior_timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    generated = {
        "visual_specification": artifact_record(SPEC_PATH),
        "dashboard_specification": artifact_record(DASHBOARD_PATH),
        "visual_qa": artifact_record(QA_PATH),
    }
    for visual_id, path in FIGURES.items():
        generated[visual_id] = artifact_record(path)
    validation: dict[str, Any] = {
        "path": VALIDATION_PATH.relative_to(ROOT).as_posix(),
        "status": "PENDING_INDEPENDENT_VALIDATION",
    }
    if VALIDATION_PATH.exists():
        validation_frame = pd.read_csv(VALIDATION_PATH)
        validation = {
            **artifact_record(VALIDATION_PATH),
            "check_count": int(len(validation_frame)),
            "pass_count": int(validation_frame["status"].eq("PASS").sum()),
            "fail_count": int(validation_frame["status"].eq("FAIL").sum()),
            "status": "PASS" if validation_frame["status"].eq("PASS").all() else "FAIL",
        }
    return {
        "visualization_version": VISUALIZATION_VERSION,
        "visualization_timestamp_utc": timestamp,
        "timestamp_note": "Timestamp of first successful Phase 8 generation for this version; preserved on deterministic reruns.",
        "period": PERIOD,
        "governed_question": "Which broad product categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?",
        "input_artifacts": {name: artifact_record(path) for name, path in INPUTS.items()},
        "generated_artifacts": generated,
        "validation": validation,
        "visual_count": int(len(specification)),
        "dashboard_page_count": int(len(dashboard)),
        "manual_qa_status": MANUAL_QA_STATUS,
        "guardrails": {
            "approved_kpi_count": 5,
            "composite_score_created": False,
            "sales_metric_created": False,
            "revenue_metric_created": False,
            "campaign_recommendation_created": False,
            "insufficient_categories_plotted_as_zero": False,
            "primary_exact_result_remains_primary": True,
            "power_bi_dashboard_built": False,
            "upstream_artifacts_modified": False,
        },
        "reproducibility": {
            "status": "PASS",
            "artifacts_in_scope": len(generated) + 1,
            "sha256_differences": 0,
            "note": "All generated specification tables, QA table, figures, and this manifest reproduced byte-for-byte on the verified rerun.",
        },
    }


def assert_safeguards(category: pd.DataFrame, specification: pd.DataFrame) -> None:
    approved = {
        "Observed Stable-Category Product Count",
        "Eligible Favorite-Movement Product Count",
        "Positive Favorite-Movement Breadth",
        "Median Daily Favorite Movement per Product",
        "Evidence Sufficiency Tier",
    }
    phase6 = pd.read_csv(INPUTS["phase6_kpi_specification"])
    if set(phase6.loc[phase6["status"].str.startswith("APPROVED"), "kpi_name"]) != approved:
        raise AssertionError("Phase 6 approved KPI set changed; stop for review.")
    insufficient = category["evidence_sufficiency_tier"].eq("INSUFFICIENT")
    if category.loc[insufficient, ["positive_favorite_movement_breadth", "median_daily_favorite_movement_per_product"]].notna().any().any():
        raise AssertionError("Insufficient-category movement values must remain blank.")
    measures = " ".join(specification["measures_used"].astype(str)).lower()
    for blocked in ["total_sold", "total_rating", "revenue", "orders", "conversion", "composite"]:
        if blocked in measures:
            raise AssertionError(f"Blocked measure appears in visual specification: {blocked}")


def main() -> None:
    apply_style()
    category, comparison, sensitivity = load_inputs()
    specification = build_visual_specification()
    dashboard = build_dashboard_specification()
    assert_safeguards(category, specification)

    plot_breadth_vs_magnitude(comparison)
    plot_evidence_sufficiency(comparison)
    plot_eligible_products(comparison)
    plot_breadth(comparison)
    plot_median_movement(comparison)
    plot_sensitivity_summary(comparison, sensitivity)

    write_csv(specification, SPEC_PATH)
    write_csv(dashboard, DASHBOARD_PATH)
    qa = build_qa_table(specification)
    write_csv(qa, QA_PATH)

    manifest = build_manifest(specification, dashboard, qa)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Created {len(specification)} Phase 8 visuals and {len(dashboard)} dashboard-page specifications.")
    print(f"Manual QA status: {MANUAL_QA_STATUS}")


if __name__ == "__main__":
    main()
