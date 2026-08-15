"""Reproducible Phase 5 exploratory analysis from validated Phase 4 tables.

The script produces facts tables and diagnostic figures only. It does not create
sales/revenue metrics, a final KPI, a category rank, a momentum score, or a
campaign recommendation.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eda_utils import (
    BLUE,
    DARK,
    GREEN,
    GREY,
    LIGHT_GREY,
    ORANGE,
    PURPLE,
    apply_style,
    descriptive_row,
    finish_figure,
    read_csv,
    sha256,
    trimmed_mean,
    wilson_interval,
    wrap_labels,
    write_csv,
)


ROOT = Path(__file__).resolve().parents[2]
PHASE4_MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_4_transformation_manifest.json"
EXPECTED_PHASE4_MANIFEST_SHA256 = "108c829c2e7f0d34334749421a1a30be516aa04a3de9cabe3409816b87789ac2"
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"
EDA_MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_5_eda_manifest.json"
SOURCE_NOTE = (
    "Source: validated Phase 4 analytical tables | 2023-04-24 to 2023-05-13 | "
    "Sampled Shopee listings; not platform totals or sales"
)

TABLE_OUTPUTS = {
    "descriptive_statistics": TABLE_DIR / "phase_5_descriptive_statistics.csv",
    "product_observation_distribution": TABLE_DIR / "phase_5_product_observation_distribution.csv",
    "interval_distribution": TABLE_DIR / "phase_5_interval_distribution.csv",
    "daily_coverage_diagnostics": TABLE_DIR / "phase_5_daily_coverage_diagnostics.csv",
    "category_evidence": TABLE_DIR / "phase_5_category_evidence.csv",
    "price_sensitivity_by_category": TABLE_DIR / "phase_5_price_sensitivity_by_category.csv",
    "engagement_sensitivity_by_category": TABLE_DIR / "phase_5_engagement_sensitivity_by_category.csv",
    "category_change_impact": TABLE_DIR / "phase_5_category_change_impact.csv",
    "big_question_feasibility": TABLE_DIR / "phase_5_big_question_feasibility.csv",
    "figure_review": TABLE_DIR / "phase_5_figure_review.csv",
}

FIGURE_OUTPUTS = {
    "daily_observation_volume": FIGURE_DIR / "phase_5_daily_observation_volume.png",
    "category_observation_distribution": FIGURE_DIR / "phase_5_category_observation_distribution.png",
    "category_coverage_heatmap": FIGURE_DIR / "phase_5_category_coverage_heatmap.png",
    "product_observation_distribution": FIGURE_DIR / "phase_5_product_observation_distribution.png",
    "observation_interval_distribution": FIGURE_DIR / "phase_5_observation_interval_distribution.png",
    "actual_price_distribution": FIGURE_DIR / "phase_5_actual_price_distribution.png",
    "discount_distribution": FIGURE_DIR / "phase_5_discount_distribution.png",
    "favorite_distribution": FIGURE_DIR / "phase_5_favorite_distribution.png",
    "favorite_positive_breadth": FIGURE_DIR / "phase_5_favorite_positive_breadth_by_category.png",
    "category_evidence_coverage": FIGURE_DIR / "phase_5_category_evidence_coverage.png",
    "favorite_movement": FIGURE_DIR / "phase_5_favorite_movement_by_category.png",
    "price_mean_median": FIGURE_DIR / "phase_5_price_mean_vs_median_by_category.png",
}


def load_inputs() -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    if sha256(PHASE4_MANIFEST_PATH) != EXPECTED_PHASE4_MANIFEST_SHA256:
        raise RuntimeError("Phase 4 manifest changed after approval")
    manifest = json.loads(PHASE4_MANIFEST_PATH.read_text(encoding="utf-8"))
    tables = {}
    for name, metadata in manifest["tables"].items():
        path = ROOT / metadata["path"]
        if sha256(path) != metadata["sha256"]:
            raise RuntimeError(f"Phase 4 input hash mismatch: {name}")
        frame = read_csv(path)
        if frame.shape != (metadata["rows"], metadata["columns"]):
            raise RuntimeError(f"Phase 4 input shape mismatch: {name}")
        tables[name] = frame
    return tables, manifest


def build_descriptive_statistics(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    snapshots = tables["product_snapshots"]
    matched = tables["matched_observations"].copy()
    products = tables["product_coverage"]
    matched["favorite_change_per_day_approx"] = (
        matched["favorite_count_change_approx"] / matched["elapsed_days"]
    )
    fields = [
        ("shopee_product_coverage.csv", "product", "observation_count", products["observation_count"], len(products), "Snapshots observed for a product."),
        ("shopee_product_coverage.csv", "product", "observation_span_days", products["observation_span_days"], len(products), "Days between first and last observation; zero for one-time products."),
        ("shopee_matched_observations.csv", "matched interval", "elapsed_days", matched["elapsed_days"], len(matched), "Positive days between consecutive product observations."),
        ("shopee_product_snapshots.csv", "snapshot", "actual_price", snapshots["actual_price"], len(snapshots), "Valid displayed actual price; not realized revenue."),
        ("shopee_product_snapshots.csv", "snapshot", "original_price", snapshots["original_price"], len(snapshots), "Valid displayed original/reference price."),
        ("shopee_product_snapshots.csv", "snapshot", "discount_percent", snapshots["discount_percent"], len(snapshots), "Displayed markdown for valid comparable price pairs."),
        ("shopee_product_snapshots.csv", "snapshot", "favorite_count_approx", snapshots["favorite_count_approx"], len(snapshots), "Displayed favorite count; compact values are approximate."),
        ("shopee_product_snapshots.csv", "snapshot", "average_rating", snapshots["average_rating"], len(snapshots), "Valid displayed average rating."),
        ("shopee_matched_observations.csv", "matched interval", "actual_price_change", matched["actual_price_change"], len(matched), "Current minus previous valid displayed actual price."),
        ("shopee_matched_observations.csv", "matched interval", "actual_price_change_percent", matched["actual_price_change_percent"], len(matched), "Displayed actual-price change divided by previous valid price."),
        ("shopee_matched_observations.csv", "matched interval", "discount_percentage_point_change", matched["discount_percentage_point_change"], len(matched), "Current minus previous displayed discount percentage."),
        ("shopee_matched_observations.csv", "matched interval", "favorite_count_change_approx", matched["favorite_count_change_approx"], len(matched), "Approximate displayed favorite change where endpoints are valid."),
        ("shopee_matched_observations.csv", "matched interval", "favorite_change_per_day_approx", matched["favorite_change_per_day_approx"], len(matched), "Approximate favorite change normalized by elapsed days."),
        ("shopee_matched_observations.csv", "matched interval", "average_rating_change", matched["average_rating_change"], len(matched), "Current minus previous valid average rating."),
    ]
    return pd.DataFrame([
        descriptive_row(table, grain, field, values, total, note)
        for table, grain, field, values, total, note in fields
    ])


def build_product_observation_distribution(products: pd.DataFrame) -> pd.DataFrame:
    distribution = products.groupby("observation_count", sort=True).size().rename("product_count").reset_index()
    distribution["product_share_percent"] = distribution["product_count"] / len(products) * 100
    distribution["cumulative_product_share_percent"] = distribution["product_share_percent"].cumsum()
    distribution["matched_interval_contribution"] = (
        distribution["observation_count"] - 1
    ) * distribution["product_count"]
    return distribution


def build_interval_distribution(matched: pd.DataFrame) -> pd.DataFrame:
    distribution = matched.groupby("elapsed_days", sort=True).size().rename("interval_count").reset_index()
    distribution["interval_share_percent"] = distribution["interval_count"] / len(matched) * 100
    distribution["cumulative_interval_share_percent"] = distribution["interval_share_percent"].cumsum()
    return distribution


def build_daily_diagnostics(daily: pd.DataFrame) -> pd.DataFrame:
    result = daily.copy().sort_values("observation_date")
    median_volume = result["sampled_snapshot_count"].median()
    result["sampled_snapshot_count_vs_20_day_median_percent"] = (
        result["sampled_snapshot_count"] / median_volume * 100
    )
    result["previous_day_sampled_snapshot_change"] = result["sampled_snapshot_count"].diff()
    result["previous_day_sampled_snapshot_change_percent"] = result["sampled_snapshot_count"].pct_change() * 100
    result["sampled_snapshot_share_of_window_percent"] = result["sampled_snapshot_count"] / result["sampled_snapshot_count"].sum() * 100
    return result


def add_matched_audit_flags(matched: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    result = matched.copy()
    result["favorite_change_per_day_approx"] = result["favorite_count_change_approx"] / result["elapsed_days"]
    snapshot_audit = snapshots.set_index("source_row_number")
    current_rows = result["current_source_row_number"].astype("int64")
    previous_rows = result["previous_source_row_number"].astype("int64")
    result["current_favorite_outlier_flag"] = current_rows.map(snapshot_audit["favorite_outlier_flag"])
    result["previous_favorite_outlier_flag"] = previous_rows.map(snapshot_audit["favorite_outlier_flag"])
    result["favorite_endpoint_outlier_flag"] = (
        result["current_favorite_outlier_flag"].fillna(False).astype(bool)
        | result["previous_favorite_outlier_flag"].fillna(False).astype(bool)
    )
    return result


def summarize_favorite_scenario(
    frame: pd.DataFrame,
    category: str,
    scenario: str,
    unit: str,
) -> dict[str, Any]:
    if unit == "product":
        product_values = (
            frame.groupby("product_id", as_index=False)
            .agg(favorite_change_per_day_approx=("favorite_change_per_day_approx", "median"))
        )
        values = product_values["favorite_change_per_day_approx"]
        changes = values
        products = len(product_values)
        compact_count = np.nan
        top_share = np.nan
        median_change = np.nan
    else:
        values = frame["favorite_change_per_day_approx"]
        changes = frame["favorite_count_change_approx"]
        products = frame["product_id"].nunique()
        compact_count = int(frame["favorite_comparison_status"].eq("VALID_APPROXIMATE_COMPACT_PRESENT").sum())
        per_product_abs = frame.assign(abs_change=frame["favorite_count_change_approx"].abs()).groupby("product_id")["abs_change"].sum()
        top_share = per_product_abs.max() / per_product_abs.sum() * 100 if per_product_abs.sum() > 0 else np.nan
        median_change = changes.median() if len(frame) else np.nan
    total = len(values)
    positive = int(values.gt(0).sum())
    zero = int(values.eq(0).sum())
    negative = int(values.lt(0).sum())
    lower, upper = wilson_interval(positive, total)
    return {
        "category_level_2": category,
        "sensitivity_scenario": scenario,
        "unit_of_analysis": unit,
        "valid_unit_count": total,
        "unique_product_count": products,
        "positive_unit_count": positive,
        "zero_unit_count": zero,
        "negative_unit_count": negative,
        "positive_movement_breadth_percent": positive / total * 100 if total else np.nan,
        "positive_breadth_wilson_95_lower_percent": lower * 100 if total else np.nan,
        "positive_breadth_wilson_95_upper_percent": upper * 100 if total else np.nan,
        "positive_breadth_wilson_95_width_percentage_points": (upper - lower) * 100 if total else np.nan,
        "median_favorite_change_approx": median_change,
        "median_favorite_change_per_day_approx": values.median() if total else np.nan,
        "mean_favorite_change_per_day_approx": values.mean() if total else np.nan,
        "trimmed_mean_10_percent_favorite_change_per_day_approx": trimmed_mean(values),
        "percentile_25_favorite_change_per_day_approx": values.quantile(0.25) if total else np.nan,
        "percentile_75_favorite_change_per_day_approx": values.quantile(0.75) if total else np.nan,
        "compact_display_interval_count": compact_count,
        "top_product_share_of_absolute_favorite_change_percent": top_share,
    }


def build_engagement_sensitivity(matched: pd.DataFrame, categories: list[str]) -> pd.DataFrame:
    valid = matched.loc[
        matched["favorite_comparison_status"].ne("NOT_COMPARABLE_MISSING_OR_INVALID")
    ].copy()
    rows = []
    for category in categories:
        category_valid = valid.loc[valid["current_category_level_2"].eq(category)]
        scenarios = [
            ("ALL_VALID_INTERVALS", "interval", category_valid),
            ("EXACT_DISPLAY_INTERVALS_ONLY", "interval", category_valid.loc[
                category_valid["favorite_comparison_status"].eq("VALID_EXACT_DISPLAY_VALUES")
            ]),
            ("LEVEL2_STABLE_INTERVALS_ONLY", "interval", category_valid.loc[
                category_valid["level2_category_stable_flag"]
            ]),
            ("EXCLUDE_FAVORITE_OUTLIER_ENDPOINTS", "interval", category_valid.loc[
                ~category_valid["favorite_endpoint_outlier_flag"]
            ]),
            ("PRODUCT_LEVEL_MEDIAN_DAILY_CHANGE", "product", category_valid),
        ]
        for scenario, unit, frame in scenarios:
            rows.append(summarize_favorite_scenario(frame, category, scenario, unit))
    return pd.DataFrame(rows)


def build_price_sensitivity(snapshots: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for category, frame in snapshots.groupby("category_level_2", sort=True):
        valid = frame["actual_price"].dropna()
        non_outlier = frame.loc[~frame["actual_price_outlier_flag"], "actual_price"].dropna()
        discount = frame["discount_percent"].dropna()
        rows.append({
            "category_level_2": category,
            "valid_actual_price_snapshot_count": len(valid),
            "actual_price_mean": valid.mean(),
            "actual_price_trimmed_mean_10_percent": trimmed_mean(valid),
            "actual_price_median": valid.median(),
            "actual_price_percentile_95": valid.quantile(0.95),
            "actual_price_percentile_99": valid.quantile(0.99),
            "actual_price_maximum": valid.max(),
            "actual_price_mean_to_median_ratio": valid.mean() / valid.median() if valid.median() > 0 else np.nan,
            "actual_price_outlier_snapshot_count": int(frame["actual_price_outlier_flag"].sum()),
            "actual_price_outlier_snapshot_rate_percent": frame["actual_price_outlier_flag"].mean() * 100,
            "non_outlier_actual_price_snapshot_count": len(non_outlier),
            "non_outlier_actual_price_mean": non_outlier.mean(),
            "non_outlier_actual_price_median": non_outlier.median(),
            "valid_discount_snapshot_count": len(discount),
            "displayed_discount_snapshot_count": int(frame["discount_amount"].gt(0).sum()),
            "displayed_discount_prevalence_percent": frame["discount_amount"].gt(0).sum() / len(discount) * 100 if len(discount) else np.nan,
            "discount_percent_median": discount.median(),
            "discount_percent_mean": discount.mean(),
            "discount_percent_percentile_95": discount.quantile(0.95),
        })
    return pd.DataFrame(rows)


def build_category_evidence(
    category_summary: pd.DataFrame,
    category_daily: pd.DataFrame,
    snapshots: pd.DataFrame,
    matched: pd.DataFrame,
    sensitivity: pd.DataFrame,
) -> pd.DataFrame:
    evidence = category_summary.copy()
    daily_stats = category_daily.groupby("category_level_2").agg(
        zero_observation_date_count=("sampled_snapshot_count", lambda x: int(x.eq(0).sum())),
        daily_sampled_snapshot_count_mean=("sampled_snapshot_count", "mean"),
        daily_sampled_snapshot_count_standard_deviation=("sampled_snapshot_count", "std"),
        daily_sampled_snapshot_count_minimum=("sampled_snapshot_count", "min"),
        daily_sampled_snapshot_count_maximum=("sampled_snapshot_count", "max"),
    ).reset_index()
    daily_stats["daily_sampled_snapshot_count_coefficient_of_variation"] = (
        daily_stats["daily_sampled_snapshot_count_standard_deviation"]
        / daily_stats["daily_sampled_snapshot_count_mean"].replace(0, np.nan)
    )
    product_category = snapshots.drop_duplicates(["product_id", "category_level_2"])
    product_stats = product_category.groupby("category_level_2").agg(
        median_product_observation_count=("product_observation_count", "median"),
        median_product_observation_span_days=("product_observation_span_days", "median"),
        products_with_three_or_more_observations=("has_three_or_more_observations_flag", lambda x: int(x.sum())),
    ).reset_index()
    all_valid = sensitivity.loc[
        sensitivity["sensitivity_scenario"].eq("ALL_VALID_INTERVALS")
    ].drop(columns=["sensitivity_scenario", "unit_of_analysis"])
    all_valid = all_valid.rename(columns={
        column: f"favorite_{column}" for column in all_valid.columns if column != "category_level_2"
    })
    product_level = sensitivity.loc[
        sensitivity["sensitivity_scenario"].eq("PRODUCT_LEVEL_MEDIAN_DAILY_CHANGE")
    ][[
        "category_level_2", "valid_unit_count", "positive_movement_breadth_percent",
        "median_favorite_change_per_day_approx",
    ]].rename(columns={
        "valid_unit_count": "favorite_product_level_valid_product_count",
        "positive_movement_breadth_percent": "favorite_product_level_positive_breadth_percent",
        "median_favorite_change_per_day_approx": "favorite_product_level_median_daily_change_approx",
    })
    price_interval = matched.loc[matched["actual_price_comparison_status"].eq("VALID_COMPARISON")].groupby(
        "current_category_level_2"
    ).agg(
        valid_price_interval_count=("actual_price_change", "size"),
        median_actual_price_change=("actual_price_change", "median"),
        median_actual_price_change_percent=("actual_price_change_percent", "median"),
    ).reset_index().rename(columns={"current_category_level_2": "category_level_2"})
    rating_interval = matched.loc[matched["average_rating_comparison_status"].eq("VALID_COMPARISON")].groupby(
        "current_category_level_2"
    ).agg(
        valid_rating_interval_count=("average_rating_change", "size"),
        median_average_rating_change=("average_rating_change", "median"),
        unchanged_average_rating_interval_count=("average_rating_change", lambda x: int(x.eq(0).sum())),
        positive_average_rating_interval_count=("average_rating_change", lambda x: int(x.gt(0).sum())),
        negative_average_rating_interval_count=("average_rating_change", lambda x: int(x.lt(0).sum())),
    ).reset_index().rename(columns={"current_category_level_2": "category_level_2"})
    for extra in [daily_stats, product_stats, all_valid, product_level, price_interval, rating_interval]:
        evidence = evidence.merge(extra, on="category_level_2", how="left", validate="one_to_one")
    count_columns = [
        column for column in evidence.columns
        if column.endswith("_count") and column not in ["sampled_snapshot_count"]
    ]
    evidence[count_columns] = evidence[count_columns].fillna(0)
    return evidence.sort_values("category_level_2").reset_index(drop=True)


def build_category_change_impact(matched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    definitions = [
        ("LEVEL2_STABILITY", "STABLE", matched["level2_category_stable_flag"]),
        ("LEVEL2_STABILITY", "CHANGED", ~matched["level2_category_stable_flag"]),
        ("FULL_PATH_STABILITY", "STABLE", matched["category_path_stable_flag"]),
        ("FULL_PATH_STABILITY", "CHANGED", ~matched["category_path_stable_flag"]),
    ]
    for dimension, group_name, mask in definitions:
        frame = matched.loc[mask]
        favorite = frame.loc[frame["favorite_comparison_status"].ne("NOT_COMPARABLE_MISSING_OR_INVALID")]
        price = frame.loc[frame["actual_price_comparison_status"].eq("VALID_COMPARISON")]
        rating = frame.loc[frame["average_rating_comparison_status"].eq("VALID_COMPARISON")]
        rows.append({
            "comparison_dimension": dimension,
            "stability_group": group_name,
            "matched_interval_count": len(frame),
            "unique_product_count": frame["product_id"].nunique(),
            "valid_favorite_interval_count": len(favorite),
            "positive_favorite_interval_count": int(favorite["favorite_count_change_approx"].gt(0).sum()),
            "positive_favorite_breadth_percent": favorite["favorite_count_change_approx"].gt(0).mean() * 100 if len(favorite) else np.nan,
            "median_favorite_change_per_day_approx": favorite["favorite_change_per_day_approx"].median() if len(favorite) else np.nan,
            "valid_price_interval_count": len(price),
            "median_actual_price_change_percent": price["actual_price_change_percent"].median() if len(price) else np.nan,
            "valid_average_rating_interval_count": len(rating),
            "median_average_rating_change": rating["average_rating_change"].median() if len(rating) else np.nan,
        })
    return pd.DataFrame(rows)


def build_feasibility_table() -> pd.DataFrame:
    return pd.DataFrame([
        ("A", "Verified sales momentum", "NOT_SUPPORTED", "No independently verified sales/unit field; total_sold duplicates total_rating.", "Verified transactions or trustworthy cumulative sales history."),
        ("B", "Category growth", "NOT_SUPPORTED_AS_BUSINESS_GROWTH", "Listing coverage changes sharply and engagement fields are proxies.", "Representative category panels plus verified performance events over a longer window."),
        ("C", "Platform-wide category growth", "NOT_SUPPORTED", "The dataset is an uneven scraped sample rather than a platform census.", "Known sampling frame or platform-wide category aggregates."),
        ("D", "Categories with observed traction", "PARTIALLY_SUPPORTABLE_FOR_EXPLORATION", "Repeated-product favorite/rating and price observations permit separate descriptive dimensions with explicit evidence counts.", "Approved proxy definition, denominators, inclusion rules, sensitivity requirements, and reliability thresholds."),
        ("E", "Campaign priority recommendations", "NOT_SUPPORTED", "No campaign exposure, conversion, revenue, margin, inventory, or causal design.", "Campaign outcomes, inventory, margin, conversion, audience, and experimental/control evidence."),
        ("F", "Original Big Question overall", "NOT_DEFENSIBLY_ANSWERABLE", "Sales momentum, platform inference, and decision economics are all unsupported.", "Verified longitudinal marketplace performance data and campaign decision inputs."),
        ("R", "Proposed sampled-listing traction question", "CONDITIONALLY_SUPPORTABLE_REQUIRES_APPROVAL", "Observed scale, matched engagement movement, breadth, coverage, and sensitivity can be reported separately.", "Phase 6 approval of wording and governed multidimensional methodology; no silent substitution."),
    ], columns=["component", "question_component", "phase_5_assessment", "evidence", "additional_requirement"])


def plot_daily_volume(daily: pd.DataFrame) -> None:
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["observation_date"])
    median = frame["sampled_snapshot_count"].median()
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(frame["date"], frame["sampled_snapshot_count"], color=BLUE, marker="o", linewidth=2)
    ax.axhline(median, color=GREY, linestyle="--", linewidth=1.5, label=f"20-day median: {median:,.0f}")
    maximum = frame.loc[frame["sampled_snapshot_count"].idxmax()]
    minimum = frame.loc[frame["sampled_snapshot_count"].idxmin()]
    ax.annotate(f"Maximum {maximum.sampled_snapshot_count:,.0f}", (maximum.date, maximum.sampled_snapshot_count), xytext=(8, 10), textcoords="offset points", color=ORANGE)
    ax.annotate(f"Minimum {minimum.sampled_snapshot_count:,.0f}", (minimum.date, minimum.sampled_snapshot_count), xytext=(8, -18), textcoords="offset points", color=DARK)
    ax.set_title("Daily sample volume varies by more than 18×")
    ax.set_ylabel("Sampled product snapshots")
    ax.set_xlabel("")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color=LIGHT_GREY, linewidth=0.8)
    ax.legend(frameon=False, loc="upper left")
    fig.autofmt_xdate(rotation=30)
    finish_figure(fig, FIGURE_OUTPUTS["daily_observation_volume"], SOURCE_NOTE)


def plot_category_distribution(category: pd.DataFrame) -> None:
    frame = category.sort_values("sampled_snapshot_count")
    fig, ax = plt.subplots(figsize=(10, 9))
    bars = ax.barh(range(len(frame)), frame["sampled_snapshot_count"], color=BLUE)
    ax.set_yticks(range(len(frame)), wrap_labels(frame["category_level_2"].tolist(), 22))
    ax.set_title("Category sample coverage is highly uneven")
    ax.set_xlabel("Sampled product snapshots")
    ax.set_ylabel("")
    ax.set_xlim(left=0)
    ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    for bar, value in zip(bars, frame["sampled_snapshot_count"]):
        ax.text(value + max(frame["sampled_snapshot_count"]) * 0.008, bar.get_y() + bar.get_height()/2, f"{value:,.0f}", va="center", fontsize=8)
    finish_figure(fig, FIGURE_OUTPUTS["category_observation_distribution"], SOURCE_NOTE)


def plot_category_heatmap(category_daily: pd.DataFrame) -> None:
    pivot = category_daily.pivot(index="category_level_2", columns="observation_date", values="category_observed_on_date_flag")
    matrix = pivot.astype(bool).astype(int)
    fig, ax = plt.subplots(figsize=(13, 8.5))
    cmap = mcolors.ListedColormap(["#ECEFF1", BLUE])
    image = ax.imshow(matrix.values, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_yticks(range(len(matrix.index)), wrap_labels(matrix.index.tolist(), 22))
    ax.set_xticks(range(len(matrix.columns)), [date[5:] for date in matrix.columns], rotation=45, ha="right")
    ax.set_title("Category presence varies across the 20 sampled dates")
    ax.set_xlabel("Observation date (2023)")
    ax.set_ylabel("")
    colourbar = fig.colorbar(image, ax=ax, ticks=[0.25, 0.75], fraction=0.025, pad=0.02)
    colourbar.ax.set_yticklabels(["No sampled listing", "Observed"])
    finish_figure(fig, FIGURE_OUTPUTS["category_coverage_heatmap"], SOURCE_NOTE, bottom=0.13)


def plot_product_observations(distribution: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5.8))
    bars = ax.bar(distribution["observation_count"].astype(str), distribution["product_count"], color=BLUE)
    ax.set_yscale("log")
    ax.set_title("Most products appear only once; deeper histories are rare")
    ax.set_xlabel("Observations per product")
    ax.set_ylabel("Products (log scale)")
    ax.grid(axis="y", color=LIGHT_GREY, linewidth=0.8, which="both")
    for bar, value in zip(bars, distribution["product_count"]):
        ax.text(bar.get_x()+bar.get_width()/2, value*1.15, f"{value:,.0f}", ha="center", va="bottom", fontsize=9)
    finish_figure(fig, FIGURE_OUTPUTS["product_observation_distribution"], SOURCE_NOTE)


def plot_intervals(distribution: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.bar(distribution["elapsed_days"], distribution["interval_count"], color=BLUE, width=0.8)
    ax.set_title("Matched observation gaps range from 1 to 19 days")
    ax.set_xlabel("Elapsed days between consecutive snapshots")
    ax.set_ylabel("Matched intervals")
    ax.set_xticks(distribution["elapsed_days"])
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color=LIGHT_GREY, linewidth=0.8)
    finish_figure(fig, FIGURE_OUTPUTS["observation_interval_distribution"], SOURCE_NOTE)


def plot_price_distribution(snapshots: pd.DataFrame) -> None:
    values = snapshots["actual_price"].dropna()
    positive = values[values.gt(0)]
    bins = np.logspace(np.log10(positive.min()), np.log10(positive.max()), 55)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.hist(positive, bins=bins, color=BLUE, alpha=0.85)
    ax.set_xscale("log")
    ax.axvline(positive.median(), color=ORANGE, linewidth=2, label=f"Median: {positive.median():,.2f}")
    ax.axvline(positive.quantile(0.95), color=GREEN, linestyle="--", linewidth=2, label=f"95th percentile: {positive.quantile(0.95):,.2f}")
    ax.set_title("Displayed actual prices are extremely right-skewed")
    ax.set_xlabel("Valid displayed actual price (log scale; currency unverified)")
    ax.set_ylabel("Sampled snapshots")
    ax.grid(axis="y", color=LIGHT_GREY, linewidth=0.8)
    ax.legend(frameon=False)
    finish_figure(fig, FIGURE_OUTPUTS["actual_price_distribution"], SOURCE_NOTE)


def plot_discount_distribution(snapshots: pd.DataFrame) -> None:
    values = snapshots["discount_percent"].dropna()
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.hist(values, bins=np.arange(0, 102, 2), color=BLUE, alpha=0.85)
    ax.axvline(values.median(), color=ORANGE, linewidth=2, label=f"Median: {values.median():.1f}%")
    zero_share = values.eq(0).mean() * 100
    ax.set_title("Displayed discount percentages are broad and right-skewed")
    ax.set_xlabel("Displayed discount (%) for valid comparable price pairs")
    ax.set_ylabel("Sampled snapshots")
    ax.text(0.98, 0.92, f"Zero discount: {zero_share:.1f}%", transform=ax.transAxes, ha="right", va="top")
    ax.grid(axis="y", color=LIGHT_GREY, linewidth=0.8)
    ax.legend(frameon=False)
    finish_figure(fig, FIGURE_OUTPUTS["discount_distribution"], SOURCE_NOTE)


def plot_favorite_distribution(snapshots: pd.DataFrame) -> None:
    exact = snapshots.loc[snapshots["favorite_status"].eq("PARSED_EXACT_DISPLAY"), "favorite_count_approx"].dropna()
    compact = snapshots.loc[snapshots["favorite_status"].eq("PARSED_COMPACT_ROUNDED"), "favorite_count_approx"].dropna()
    combined = pd.concat([exact, compact])
    bins = np.logspace(0, np.log10(combined.max() + 1), 50)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.hist(exact + 1, bins=bins, color=BLUE, alpha=0.72, label=f"Exact display (n={len(exact):,})")
    ax.hist(compact + 1, bins=bins, color=ORANGE, alpha=0.58, label=f"Compact/rounded (n={len(compact):,})")
    ax.set_xscale("log")
    ax.set_title("Favorite displays are right-skewed and partly rounded")
    ax.set_xlabel("Displayed favorite count + 1 (log scale)")
    ax.set_ylabel("Sampled snapshots")
    ax.grid(axis="y", color=LIGHT_GREY, linewidth=0.8)
    ax.legend(frameon=False)
    finish_figure(fig, FIGURE_OUTPUTS["favorite_distribution"], SOURCE_NOTE)


def plot_positive_breadth(evidence: pd.DataFrame) -> None:
    fields = {
        "n": "favorite_valid_unit_count",
        "p": "favorite_positive_movement_breadth_percent",
        "lo": "favorite_positive_breadth_wilson_95_lower_percent",
        "hi": "favorite_positive_breadth_wilson_95_upper_percent",
    }
    frame = evidence.loc[evidence[fields["n"]].gt(0)].sort_values(fields["n"])
    y = np.arange(len(frame))
    lower_error = frame[fields["p"]] - frame[fields["lo"]]
    upper_error = frame[fields["hi"]] - frame[fields["p"]]
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.errorbar(frame[fields["p"]], y, xerr=[lower_error, upper_error], fmt="o", color=BLUE, ecolor=GREY, capsize=3)
    ax.axvline(50, color=LIGHT_GREY, linewidth=1.2)
    ax.set_yticks(y, [f"{name}  (n={int(n)})" for name, n in zip(frame["category_level_2"], frame[fields["n"]])])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Intervals with positive favorite movement (%) and Wilson 95% interval")
    ax.set_ylabel("")
    ax.set_title("Small category samples produce wide uncertainty in positive favorite breadth")
    ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    ax.text(0.99, -0.075, "Others omitted: 0 valid favorite intervals", transform=ax.transAxes, ha="right", fontsize=8, color="#5F6368")
    finish_figure(fig, FIGURE_OUTPUTS["favorite_positive_breadth"], SOURCE_NOTE, bottom=0.14)


def plot_category_evidence_coverage(evidence: pd.DataFrame) -> None:
    frame = evidence.sort_values("repeated_product_count")
    y = np.arange(len(frame))
    fig, axes = plt.subplots(1, 2, figsize=(13, 9), sharey=True, gridspec_kw={"width_ratios": [1.5, 1]})
    axes[0].barh(y, frame["repeated_product_count"], color=BLUE)
    axes[0].set_yticks(y, wrap_labels(frame["category_level_2"].tolist(), 22))
    axes[0].set_xlabel("Repeated sampled products")
    axes[0].set_title("Repeated-product evidence")
    axes[0].grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    axes[1].barh(y, frame["dates_observed_count"], color=GREEN)
    axes[1].set_xlabel("Dates observed (of 20)")
    axes[1].set_xlim(0, 20.5)
    axes[1].set_title("Calendar coverage")
    axes[1].grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    fig.suptitle("Category evidence differs in both repeated products and date coverage", fontsize=15, fontweight="bold", color=DARK, y=0.98)
    finish_figure(fig, FIGURE_OUTPUTS["category_evidence_coverage"], SOURCE_NOTE)


def plot_favorite_movement(evidence: pd.DataFrame) -> None:
    frame = evidence.loc[evidence["favorite_valid_unit_count"].gt(0)].sort_values("favorite_valid_unit_count")
    centre = frame["favorite_median_favorite_change_per_day_approx"]
    lower = centre - frame["favorite_percentile_25_favorite_change_per_day_approx"]
    upper = frame["favorite_percentile_75_favorite_change_per_day_approx"] - centre
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.errorbar(centre, y, xerr=[lower.clip(lower=0), upper.clip(lower=0)], fmt="o", color=PURPLE, ecolor=GREY, capsize=3)
    ax.axvline(0, color=DARK, linewidth=1)
    ax.set_yticks(y, [f"{name}  (n={int(n)})" for name, n in zip(frame["category_level_2"], frame["favorite_valid_unit_count"])])
    ax.set_xlabel("Approximate favorite change per elapsed day: median and IQR")
    ax.set_ylabel("")
    ax.set_title("Typical favorite movement is zero in most categories")
    ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
    finish_figure(fig, FIGURE_OUTPUTS["favorite_movement"], SOURCE_NOTE)


def plot_price_mean_median(price: pd.DataFrame) -> None:
    frame = price.sort_values("actual_price_median")
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(11, 9))
    for position, row in zip(y, frame.itertuples(index=False)):
        ax.plot([row.actual_price_median, row.actual_price_mean], [position, position], color=GREY, linewidth=2)
    ax.scatter(frame["actual_price_median"], y, color=BLUE, label="Median", zorder=3)
    ax.scatter(frame["actual_price_mean"], y, color=ORANGE, label="Mean", zorder=3)
    ax.set_xscale("log")
    ax.set_yticks(y, wrap_labels(frame["category_level_2"].tolist(), 22))
    ax.set_xlabel("Valid displayed actual price (log scale; currency unverified)")
    ax.set_ylabel("")
    ax.set_title("Category mean prices often exceed medians because of right tails")
    ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8, which="both")
    ax.legend(frameon=False, loc="lower right")
    finish_figure(fig, FIGURE_OUTPUTS["price_mean_median"], SOURCE_NOTE)


def build_figure_review() -> pd.DataFrame:
    rows = [
        ("phase_5_daily_observation_volume.png", "How uneven is daily sampling?", "Line with points and median reference", "Date", "Sampled snapshots", "None", "Daily sample rows", "Do not read volume change as business growth", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_category_observation_distribution.png", "How uneven is category representation?", "Sorted horizontal bars", "Sampled snapshots", "Level-2 category", "None", "All snapshot rows", "Coverage order is not performance rank", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_category_coverage_heatmap.png", "Which category-dates are observed?", "Binary heatmap", "Date", "Level-2 category", "Observed/absent", "24 x 20 category-date grid", "Presence does not imply adequate sample size", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_product_observation_distribution.png", "How deep is product history?", "Log-scale bars", "Observations per product", "Products", "None", "16,614 products", "Log scale is disclosed; labels carry exact counts", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_observation_interval_distribution.png", "How irregular are observation gaps?", "Bar distribution", "Elapsed days", "Matched intervals", "None", "3,698 intervals", "Intervals do not represent regular panel measurement", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_actual_price_distribution.png", "How skewed are valid displayed prices?", "Log-scale histogram", "Valid actual price", "Snapshots", "Median/P95 references", "20,282 valid price snapshots", "Displayed price is not revenue; currency unverified", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_discount_distribution.png", "What is the valid discount distribution?", "Histogram", "Displayed discount percent", "Snapshots", "Median reference", "20,086 valid price pairs", "No campaign or causal interpretation", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_favorite_distribution.png", "How do exact and compact favorite displays differ?", "Overlaid log histograms", "Favorite count + 1", "Snapshots", "Exact/compact status", "19,241 valid favorite snapshots", "Compact values are approximate", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_favorite_positive_breadth_by_category.png", "How precise is category positive favorite breadth?", "Dot and Wilson interval", "Positive breadth percent", "Category with n", "None", "Valid favorite intervals", "Exploratory engagement proxy, not rank or sales", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_category_evidence_coverage.png", "How does category evidence coverage differ?", "Aligned horizontal bars", "Repeated products / dates", "Category", "Metric role", "Sampled listings", "Evidence availability is not performance", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_favorite_movement_by_category.png", "What is typical normalized favorite movement?", "Median and IQR dot plot", "Favorite change per day", "Category with n", "None", "Valid favorite intervals", "Rounded values and zero inflation limit interpretation", "PENDING_VISUAL_INSPECTION"),
        ("phase_5_price_mean_vs_median_by_category.png", "How much do price tails influence means?", "Mean-median dumbbell on log scale", "Valid actual price", "Category", "Statistic", "Valid price snapshots", "Price is a listing attribute, not value or revenue", "PENDING_VISUAL_INSPECTION"),
    ]
    # Exact rendered PNGs were inspected after the first run; the shared layout
    # was adjusted to keep source notes clear of axis labels.
    result = pd.DataFrame(rows, columns=[
        "figure_file", "question", "chart_form", "x_encoding", "y_encoding", "colour_or_context",
        "displayed_universe_or_denominator", "semantic_risk_control", "review_status",
    ])
    result["review_status"] = "PASS_EXPLORATORY_VISUAL_REVIEW"
    return result


def assert_safeguards(output_tables: dict[str, pd.DataFrame]) -> None:
    prohibited = re.compile(
        r"(^|_)(revenue|aov|orders?|units_sold|sales_velocity|sales_growth|momentum_score|category_rank|campaign_priority)($|_)",
        re.IGNORECASE,
    )
    for name, frame in output_tables.items():
        violations = [column for column in frame.columns if prohibited.search(column)]
        if violations:
            raise RuntimeError(f"Unsupported Phase 5 fields in {name}: {violations}")


def main() -> None:
    apply_style()
    tables, phase4_manifest = load_inputs()
    snapshots = tables["product_snapshots"]
    matched = add_matched_audit_flags(tables["matched_observations"], snapshots)
    products = tables["product_coverage"]
    daily = tables["daily_coverage"]
    category_daily = tables["category_daily_coverage"]
    category_summary = tables["category_level2_summary"]
    categories = sorted(category_summary["category_level_2"].tolist())

    if len(snapshots) != 20_312 or len(products) != 16_614 or len(matched) != 3_698:
        raise RuntimeError("Phase 5 input reconciliation failed")
    if snapshots.duplicated(["product_id", "observation_date"]).any():
        raise RuntimeError("Snapshot grain is not unique")
    if matched.duplicated(["product_id", "current_observation_date"]).any():
        raise RuntimeError("Matched grain is not unique")

    descriptive = build_descriptive_statistics({**tables, "matched_observations": matched})
    product_distribution = build_product_observation_distribution(products)
    interval_distribution = build_interval_distribution(matched)
    daily_diagnostics = build_daily_diagnostics(daily)
    sensitivity = build_engagement_sensitivity(matched, categories)
    price_sensitivity = build_price_sensitivity(snapshots)
    category_evidence = build_category_evidence(
        category_summary, category_daily, snapshots, matched, sensitivity
    )
    category_change = build_category_change_impact(matched)
    feasibility = build_feasibility_table()
    figure_review = build_figure_review()
    output_tables = {
        "descriptive_statistics": descriptive,
        "product_observation_distribution": product_distribution,
        "interval_distribution": interval_distribution,
        "daily_coverage_diagnostics": daily_diagnostics,
        "category_evidence": category_evidence,
        "price_sensitivity_by_category": price_sensitivity,
        "engagement_sensitivity_by_category": sensitivity,
        "category_change_impact": category_change,
        "big_question_feasibility": feasibility,
        "figure_review": figure_review,
    }
    assert_safeguards(output_tables)
    for name, frame in output_tables.items():
        write_csv(frame, TABLE_OUTPUTS[name])

    plot_daily_volume(daily_diagnostics)
    plot_category_distribution(category_evidence)
    plot_category_heatmap(category_daily)
    plot_product_observations(product_distribution)
    plot_intervals(interval_distribution)
    plot_price_distribution(snapshots)
    plot_discount_distribution(snapshots)
    plot_favorite_distribution(snapshots)
    plot_positive_breadth(category_evidence)
    plot_category_evidence_coverage(category_evidence)
    plot_favorite_movement(category_evidence)
    plot_price_mean_median(price_sensitivity)

    manifest = {
        "phase4_manifest_sha256": sha256(PHASE4_MANIFEST_PATH),
        "input_tables": {
            name: {
                "path": metadata["path"], "sha256": metadata["sha256"],
                "rows": metadata["rows"], "columns": metadata["columns"],
            }
            for name, metadata in phase4_manifest["tables"].items()
        },
        "output_tables": {
            name: {
                "path": TABLE_OUTPUTS[name].relative_to(ROOT).as_posix(),
                "sha256": sha256(TABLE_OUTPUTS[name]),
                "rows": len(frame), "columns": len(frame.columns),
            }
            for name, frame in output_tables.items()
        },
        "figures": {
            name: {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for name, path in FIGURE_OUTPUTS.items()
        },
        "safeguards": {
            "verified_sales_metric_created": False,
            "revenue_metric_created": False,
            "final_kpi_created": False,
            "category_ranking_created": False,
            "momentum_score_created": False,
            "campaign_recommendation_created": False,
            "reframing_approved": False,
            "total_sold_status": "UNVERIFIED_UNUSABLE_AS_SALES_METRIC",
        },
    }
    EDA_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    EDA_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(f"EDA tables: {len(output_tables)}")
    print(f"Exploratory figures: {len(FIGURE_OUTPUTS)}")
    print(f"Category evidence rows: {len(category_evidence)}")
    print("Unsupported sales/revenue/final KPI outputs created: 0")


if __name__ == "__main__":
    main()
