"""Build deterministic Phase 4 analytical tables from the validated snapshot data.

The outputs expose intuitive analytical names, explicit grains, coverage evidence,
validity-aware price and engagement fields, and no verified sales/momentum metric.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "data" / "processed" / "shopee_sales_cleaned.csv"
EXPECTED_SOURCE_SHA256 = "407c6f5e654283461c8eba20a3a1721f5105650212e92ae99206ea6dbadd199d"
RAW_CANDIDATES = (
    ROOT / "data" / "raw" / "shopee_sales_data.csv",
    ROOT / "dataset" / "shopee_sales_data.csv",
)
EXPECTED_RAW_SHA256 = "afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69"
STUDY_DATE_COUNT = 20

OUTPUTS = {
    "product_snapshots": ROOT / "data" / "processed" / "shopee_product_snapshots.csv",
    "matched_observations": ROOT / "data" / "processed" / "shopee_matched_observations.csv",
    "product_coverage": ROOT / "data" / "processed" / "shopee_product_coverage.csv",
    "daily_coverage": ROOT / "data" / "processed" / "shopee_daily_coverage.csv",
    "category_daily_coverage": ROOT / "data" / "processed" / "shopee_category_daily_coverage.csv",
    "category_level2_summary": ROOT / "data" / "processed" / "shopee_category_level2_summary.csv",
}
RECONCILIATION_PATH = ROOT / "outputs" / "tables" / "phase_4_table_reconciliation.csv"
TRANSFORMATION_SUMMARY_PATH = ROOT / "outputs" / "tables" / "phase_4_transformation_summary.csv"
MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_4_transformation_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def boolean_text(values: pd.Series) -> pd.Series:
    return values.fillna(False).map({True: "TRUE", False: "FALSE"}).astype("string")


def numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column].replace("", pd.NA), errors="coerce")


def percent(numerator: pd.Series | float, denominator: pd.Series | float) -> pd.Series | float:
    if isinstance(denominator, pd.Series):
        result = numerator / denominator.replace(0, np.nan) * 100
        return result
    return np.nan if denominator == 0 else numerator / denominator * 100


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, encoding="utf-8", lineterminator="\n", float_format="%.10g")
    temporary.replace(path)


def build_product_snapshots(source: pd.DataFrame) -> pd.DataFrame:
    favorite_valid = source["favorite_parse_status"].isin(
        ["PARSED_EXACT_DISPLAY", "PARSED_COMPACT_ROUNDED"]
    )
    rating_valid = source["item_rating_status"].eq("VALID")
    actual_price_valid = source["price_actual_status"].eq("VALID")
    original_price_valid = source["price_ori_status"].eq("VALID")
    discount_valid = source["price_pair_status"].eq("VALID_COMPARABLE")

    snapshots = pd.DataFrame({
        "source_row_number": numeric(source, "source_row_number").astype("int64"),
        "product_id": source["id"],
        "observation_date": source["observation_date"],
        "observation_week_start": source["observation_week_start"],
        "observation_month": source["observation_month"],
        "observation_day_of_week": source["observation_day_of_week"],
        "product_title": source["title"],
        "seller_name": source["seller_name"],
        "product_url": source["link_ori"],
        "category_level_2": source["category_level_2"],
        "category_level_3": source["category_level_3"],
        "category_level_4": source["category_level_4"],
        "category_path": source["category_path_clean"],
        "category_path_status": source["category_path_parse_status"],
        "category_changed_over_time_flag": source["product_category_change_flag"],
        "level2_category_changed_over_time_flag": source["product_category_level2_change_flag"],
        "category_changed_from_previous_observation_flag": source["category_changed_from_previous_flag"],
        "level2_category_changed_from_previous_observation_flag": source["category_level2_changed_from_previous_flag"],
        "actual_price": numeric(source, "price_actual_clean"),
        "actual_price_status": source["price_actual_status"],
        "actual_price_valid_flag": boolean_text(actual_price_valid),
        "actual_price_outlier_flag": source["price_actual_statistical_outlier_flag"],
        "original_price": numeric(source, "price_ori_clean"),
        "original_price_status": source["price_ori_status"],
        "original_price_valid_flag": boolean_text(original_price_valid),
        "original_price_outlier_flag": source["price_ori_statistical_outlier_flag"],
        "price_pair_status": source["price_pair_status"],
        "discount_valid_flag": boolean_text(discount_valid),
        "discount_amount": numeric(source, "discount_amount"),
        "discount_percent": numeric(source, "discount_pct"),
        "currency_status": source["price_currency_status"],
        "favorite_count_approx": numeric(source, "favorite_parsed"),
        "favorite_status": source["favorite_parse_status"],
        "favorite_valid_flag": boolean_text(favorite_valid),
        "favorite_is_rounded_flag": source["favorite_compact_rounded_flag"],
        "favorite_precision_unit": numeric(source, "favorite_precision_unit"),
        "favorite_outlier_flag": source["favorite_statistical_outlier_flag"],
        "average_rating": numeric(source, "item_rating_numeric"),
        "average_rating_status": source["item_rating_status"],
        "average_rating_valid_flag": boolean_text(rating_valid),
        "average_rating_outlier_flag": source["item_rating_statistical_outlier_flag"],
        "product_observation_count": numeric(source, "product_observation_count").astype("int64"),
        "product_first_observation_date": source["product_first_observation_date"],
        "product_last_observation_date": source["product_last_observation_date"],
        "product_observation_span_days": numeric(source, "product_observation_span_days").astype("int64"),
        "product_observed_date_rate_percent": numeric(source, "product_observation_count") / STUDY_DATE_COUNT * 100,
        "repeated_product_flag": source["matched_product_flag"],
        "observation_sequence": numeric(source, "observation_sequence").astype("int64"),
        "previous_observation_date": source["previous_observation_date"],
        "days_since_previous_observation": numeric(source, "observation_interval_days"),
        "has_three_or_more_observations_flag": source["acceleration_structure_flag"],
        "duplicate_review_flag": source["duplicate_review_flag"],
        "duplicate_review_group_id": source["duplicate_review_group_id"],
        "negative_unverified_counter_change_flag": source["negative_change_flag"],
        "unverified_counter_change_status": source["cumulative_change_status"],
        "movement_analysis_eligibility_status": source["movement_analysis_eligibility_status"],
        "total_sold_metric_status": source["total_sold_metric_status"],
        "total_rating_metric_status": source["total_rating_metric_status"],
        "daily_sampled_snapshot_count": numeric(source, "daily_observation_count").astype("int64"),
        "daily_sampled_unique_product_count": numeric(source, "daily_unique_product_count").astype("int64"),
        "daily_sampled_category_count": numeric(source, "daily_category_level2_count").astype("int64"),
        "daily_sampled_seller_count": numeric(source, "daily_seller_count").astype("int64"),
        "category_day_sampled_snapshot_count": numeric(source, "category_date_observation_count").astype("int64"),
        "category_day_sampled_unique_product_count": numeric(source, "category_date_unique_product_count").astype("int64"),
        "coverage_reliability_tier_status": "NOT_ASSIGNED_REQUIRES_APPROVED_THRESHOLDS",
    })
    return snapshots.sort_values(["observation_date", "product_id", "source_row_number"]).reset_index(drop=True)


def build_matched_observations(snapshots: pd.DataFrame) -> pd.DataFrame:
    ordered = snapshots.sort_values(["product_id", "observation_date", "source_row_number"]).copy()
    grouped = ordered.groupby("product_id", sort=False)
    shift_fields = [
        "source_row_number", "observation_date", "category_level_2", "category_level_3",
        "category_level_4", "category_path", "actual_price", "actual_price_status",
        "discount_amount", "discount_percent", "discount_valid_flag", "favorite_count_approx",
        "favorite_status", "favorite_is_rounded_flag", "average_rating", "average_rating_status",
        "duplicate_review_flag",
    ]
    for field in shift_fields:
        ordered[f"previous__{field}"] = grouped[field].shift()
    intervals = ordered.loc[ordered["observation_sequence"].gt(1)].copy()

    actual_price_comparable = (
        intervals["actual_price_status"].eq("VALID")
        & intervals["previous__actual_price_status"].eq("VALID")
        & intervals["actual_price"].notna()
        & intervals["previous__actual_price"].notna()
    )
    discount_comparable = (
        intervals["discount_valid_flag"].eq("TRUE")
        & intervals["previous__discount_valid_flag"].eq("TRUE")
    )
    favorite_valid_statuses = ["PARSED_EXACT_DISPLAY", "PARSED_COMPACT_ROUNDED"]
    favorite_comparable = (
        intervals["favorite_status"].isin(favorite_valid_statuses)
        & intervals["previous__favorite_status"].isin(favorite_valid_statuses)
    )
    rating_comparable = (
        intervals["average_rating_status"].eq("VALID")
        & intervals["previous__average_rating_status"].eq("VALID")
    )
    same_path = intervals["category_path"].eq(intervals["previous__category_path"])
    same_level2 = intervals["category_level_2"].eq(intervals["previous__category_level_2"])
    favorite_rounded_present = (
        intervals["favorite_is_rounded_flag"].eq("TRUE")
        | intervals["previous__favorite_is_rounded_flag"].eq("TRUE")
    )

    matched = pd.DataFrame({
        "product_id": intervals["product_id"],
        "previous_observation_date": intervals["previous__observation_date"],
        "current_observation_date": intervals["observation_date"],
        "previous_source_row_number": intervals["previous__source_row_number"].astype("int64"),
        "current_source_row_number": intervals["source_row_number"].astype("int64"),
        "elapsed_days": intervals["days_since_previous_observation"].astype("int64"),
        "current_observation_sequence": intervals["observation_sequence"].astype("int64"),
        "product_title": intervals["product_title"],
        "seller_name": intervals["seller_name"],
        "product_url": intervals["product_url"],
        "previous_category_level_2": intervals["previous__category_level_2"],
        "current_category_level_2": intervals["category_level_2"],
        "previous_category_level_3": intervals["previous__category_level_3"],
        "current_category_level_3": intervals["category_level_3"],
        "previous_category_level_4": intervals["previous__category_level_4"],
        "current_category_level_4": intervals["category_level_4"],
        "previous_category_path": intervals["previous__category_path"],
        "current_category_path": intervals["category_path"],
        "category_path_stable_flag": boolean_text(same_path),
        "level2_category_stable_flag": boolean_text(same_level2),
        "category_changed_over_time_flag": intervals["category_changed_over_time_flag"],
        "level2_category_changed_over_time_flag": intervals["level2_category_changed_over_time_flag"],
        "previous_actual_price": intervals["previous__actual_price"],
        "current_actual_price": intervals["actual_price"],
        "previous_actual_price_status": intervals["previous__actual_price_status"],
        "current_actual_price_status": intervals["actual_price_status"],
        "actual_price_comparison_status": np.where(
            actual_price_comparable, "VALID_COMPARISON", "NOT_COMPARABLE_INVALID_OR_MISSING_PRICE"
        ),
        "actual_price_change": (intervals["actual_price"] - intervals["previous__actual_price"]).where(actual_price_comparable),
        "actual_price_change_percent": (
            (intervals["actual_price"] - intervals["previous__actual_price"])
            / intervals["previous__actual_price"] * 100
        ).where(actual_price_comparable),
        "previous_discount_amount": intervals["previous__discount_amount"],
        "current_discount_amount": intervals["discount_amount"],
        "previous_discount_percent": intervals["previous__discount_percent"],
        "current_discount_percent": intervals["discount_percent"],
        "discount_comparison_status": np.where(
            discount_comparable, "VALID_COMPARISON", "NOT_COMPARABLE_INVALID_OR_MISSING_PRICE_PAIR"
        ),
        "discount_amount_change": (
            intervals["discount_amount"] - intervals["previous__discount_amount"]
        ).where(discount_comparable),
        "discount_percentage_point_change": (
            intervals["discount_percent"] - intervals["previous__discount_percent"]
        ).where(discount_comparable),
        "previous_favorite_count_approx": intervals["previous__favorite_count_approx"],
        "current_favorite_count_approx": intervals["favorite_count_approx"],
        "previous_favorite_status": intervals["previous__favorite_status"],
        "current_favorite_status": intervals["favorite_status"],
        "favorite_comparison_status": np.select(
            [favorite_comparable & favorite_rounded_present, favorite_comparable],
            ["VALID_APPROXIMATE_COMPACT_PRESENT", "VALID_EXACT_DISPLAY_VALUES"],
            default="NOT_COMPARABLE_MISSING_OR_INVALID",
        ),
        "favorite_count_change_approx": (
            intervals["favorite_count_approx"] - intervals["previous__favorite_count_approx"]
        ).where(favorite_comparable),
        "previous_average_rating": intervals["previous__average_rating"],
        "current_average_rating": intervals["average_rating"],
        "previous_average_rating_status": intervals["previous__average_rating_status"],
        "current_average_rating_status": intervals["average_rating_status"],
        "average_rating_comparison_status": np.where(
            rating_comparable, "VALID_COMPARISON", "NOT_COMPARABLE_MISSING_OR_UNRATED"
        ),
        "average_rating_change": (
            intervals["average_rating"] - intervals["previous__average_rating"]
        ).where(rating_comparable),
        "product_observation_count": intervals["product_observation_count"].astype("int64"),
        "product_observation_span_days": intervals["product_observation_span_days"].astype("int64"),
        "product_observed_date_rate_percent": intervals["product_observed_date_rate_percent"],
        "current_daily_sampled_snapshot_count": intervals["daily_sampled_snapshot_count"].astype("int64"),
        "current_category_day_sampled_snapshot_count": intervals["category_day_sampled_snapshot_count"].astype("int64"),
        "previous_duplicate_review_flag": intervals["previous__duplicate_review_flag"],
        "current_duplicate_review_flag": intervals["duplicate_review_flag"],
        "negative_unverified_counter_change_flag": intervals["negative_unverified_counter_change_flag"],
        "unverified_counter_change_status": intervals["unverified_counter_change_status"],
        "movement_analysis_eligibility_status": intervals["movement_analysis_eligibility_status"],
        "sales_movement_metric_status": "NO_VERIFIED_SALES_MOVEMENT_METRIC",
        "total_sold_metric_status": intervals["total_sold_metric_status"],
        "total_rating_metric_status": intervals["total_rating_metric_status"],
        "coverage_reliability_tier_status": "NOT_ASSIGNED_REQUIRES_APPROVED_THRESHOLDS",
    })
    return matched.sort_values(["current_observation_date", "product_id"]).reset_index(drop=True)


def build_product_coverage(snapshots: pd.DataFrame) -> pd.DataFrame:
    ordered = snapshots.sort_values(["product_id", "observation_date", "source_row_number"]).copy()
    ordered["interval_days"] = ordered.groupby("product_id")["observation_date"].transform(
        lambda values: pd.to_datetime(values).diff().dt.days
    )
    first_rows = ordered.groupby("product_id", sort=True).first()
    last_rows = ordered.groupby("product_id", sort=True).last()
    grouped = ordered.groupby("product_id", sort=True)

    coverage = pd.DataFrame(index=first_rows.index)
    coverage["product_url"] = last_rows["product_url"]
    coverage["latest_product_title"] = last_rows["product_title"]
    coverage["latest_seller_name"] = last_rows["seller_name"]
    coverage["first_observation_date"] = grouped["observation_date"].min()
    coverage["last_observation_date"] = grouped["observation_date"].max()
    coverage["observation_count"] = grouped.size().astype("int64")
    coverage["observed_date_count"] = grouped["observation_date"].nunique().astype("int64")
    coverage["observation_span_days"] = grouped["product_observation_span_days"].max().astype("int64")
    coverage["observed_date_rate_percent"] = coverage["observed_date_count"] / STUDY_DATE_COUNT * 100
    coverage["matched_interval_count"] = (coverage["observation_count"] - 1).clip(lower=0).astype("int64")
    coverage["minimum_interval_days"] = grouped["interval_days"].min()
    coverage["median_interval_days"] = grouped["interval_days"].median()
    coverage["maximum_interval_days"] = grouped["interval_days"].max()
    coverage["repeated_product_flag"] = boolean_text(coverage["observation_count"].gt(1))
    coverage["has_three_or_more_observations_flag"] = boolean_text(coverage["observation_count"].ge(3))
    coverage["has_four_or_more_observations_flag"] = boolean_text(coverage["observation_count"].ge(4))
    coverage["first_category_level_2"] = first_rows["category_level_2"]
    coverage["latest_category_level_2"] = last_rows["category_level_2"]
    coverage["distinct_category_path_count"] = grouped["category_path"].nunique().astype("int64")
    coverage["distinct_level2_category_count"] = grouped["category_level_2"].nunique().astype("int64")
    coverage["category_path_stable_flag"] = boolean_text(coverage["distinct_category_path_count"].eq(1))
    coverage["level2_category_stable_flag"] = boolean_text(coverage["distinct_level2_category_count"].eq(1))
    coverage["valid_actual_price_observation_count"] = grouped["actual_price_valid_flag"].apply(lambda values: values.eq("TRUE").sum()).astype("int64")
    coverage["valid_actual_price_observation_rate_percent"] = percent(
        coverage["valid_actual_price_observation_count"], coverage["observation_count"]
    )
    coverage["valid_discount_observation_count"] = grouped["discount_valid_flag"].apply(lambda values: values.eq("TRUE").sum()).astype("int64")
    coverage["valid_discount_observation_rate_percent"] = percent(
        coverage["valid_discount_observation_count"], coverage["observation_count"]
    )
    coverage["valid_favorite_observation_count"] = grouped["favorite_valid_flag"].apply(lambda values: values.eq("TRUE").sum()).astype("int64")
    coverage["valid_favorite_observation_rate_percent"] = percent(
        coverage["valid_favorite_observation_count"], coverage["observation_count"]
    )
    coverage["valid_average_rating_observation_count"] = grouped["average_rating_valid_flag"].apply(lambda values: values.eq("TRUE").sum()).astype("int64")
    coverage["valid_average_rating_observation_rate_percent"] = percent(
        coverage["valid_average_rating_observation_count"], coverage["observation_count"]
    )
    coverage["any_duplicate_review_flag"] = boolean_text(
        grouped["duplicate_review_flag"].apply(lambda values: values.eq("TRUE").any())
    )
    coverage["total_sold_metric_status"] = "UNVERIFIED_UNUSABLE_AS_SALES_METRIC"
    coverage["total_rating_metric_status"] = "UNVERIFIED_DUPLICATES_TOTAL_SOLD"
    coverage["coverage_reliability_tier_status"] = "NOT_ASSIGNED_REQUIRES_APPROVED_THRESHOLDS"
    return coverage.reset_index().sort_values("product_id").reset_index(drop=True)


def build_daily_coverage(snapshots: pd.DataFrame, matched: pd.DataFrame) -> pd.DataFrame:
    grouped = snapshots.groupby("observation_date", sort=True)
    daily = grouped.agg(
        sampled_snapshot_count=("product_id", "size"),
        sampled_unique_product_count=("product_id", "nunique"),
        sampled_category_level2_count=("category_level_2", "nunique"),
        sampled_seller_count=("seller_name", "nunique"),
    )
    daily["repeated_product_snapshot_count"] = grouped["repeated_product_flag"].apply(lambda x: x.eq("TRUE").sum())
    daily["repeated_product_snapshot_rate_percent"] = percent(
        daily["repeated_product_snapshot_count"], daily["sampled_snapshot_count"]
    )
    daily["valid_actual_price_snapshot_count"] = grouped["actual_price_valid_flag"].apply(lambda x: x.eq("TRUE").sum())
    daily["valid_actual_price_snapshot_rate_percent"] = percent(
        daily["valid_actual_price_snapshot_count"], daily["sampled_snapshot_count"]
    )
    daily["valid_favorite_snapshot_count"] = grouped["favorite_valid_flag"].apply(lambda x: x.eq("TRUE").sum())
    daily["valid_favorite_snapshot_rate_percent"] = percent(
        daily["valid_favorite_snapshot_count"], daily["sampled_snapshot_count"]
    )
    daily["valid_average_rating_snapshot_count"] = grouped["average_rating_valid_flag"].apply(lambda x: x.eq("TRUE").sum())
    daily["valid_average_rating_snapshot_rate_percent"] = percent(
        daily["valid_average_rating_snapshot_count"], daily["sampled_snapshot_count"]
    )
    interval_counts = matched.groupby("current_observation_date").size()
    daily["matched_interval_count_ending_on_date"] = daily.index.to_series().map(interval_counts).fillna(0).astype("int64")
    daily["study_date_count"] = STUDY_DATE_COUNT
    return daily.reset_index()


def build_category_daily_coverage(snapshots: pd.DataFrame, matched: pd.DataFrame) -> pd.DataFrame:
    categories = sorted(snapshots["category_level_2"].unique())
    dates = sorted(snapshots["observation_date"].unique())
    complete_index = pd.MultiIndex.from_product(
        [categories, dates], names=["category_level_2", "observation_date"]
    )
    grouped = snapshots.groupby(["category_level_2", "observation_date"], sort=True)
    base = grouped.agg(
        sampled_snapshot_count=("product_id", "size"),
        sampled_unique_product_count=("product_id", "nunique"),
        sampled_seller_count=("seller_name", "nunique"),
    ).reindex(complete_index, fill_value=0)
    base["repeated_product_snapshot_count"] = grouped["repeated_product_flag"].apply(
        lambda x: x.eq("TRUE").sum()
    ).reindex(complete_index, fill_value=0)
    base["valid_actual_price_snapshot_count"] = grouped["actual_price_valid_flag"].apply(
        lambda x: x.eq("TRUE").sum()
    ).reindex(complete_index, fill_value=0)
    base["valid_discount_snapshot_count"] = grouped["discount_valid_flag"].apply(
        lambda x: x.eq("TRUE").sum()
    ).reindex(complete_index, fill_value=0)
    base["displayed_discount_snapshot_count"] = grouped["discount_amount"].apply(
        lambda x: x.gt(0).sum()
    ).reindex(complete_index, fill_value=0)
    base["valid_favorite_snapshot_count"] = grouped["favorite_valid_flag"].apply(
        lambda x: x.eq("TRUE").sum()
    ).reindex(complete_index, fill_value=0)
    base["valid_average_rating_snapshot_count"] = grouped["average_rating_valid_flag"].apply(
        lambda x: x.eq("TRUE").sum()
    ).reindex(complete_index, fill_value=0)
    interval_counts = matched.groupby(["current_category_level_2", "current_observation_date"]).size()
    base["matched_interval_count_ending_on_date"] = interval_counts.reindex(complete_index, fill_value=0)
    base["category_observed_on_date_flag"] = boolean_text(base["sampled_snapshot_count"].gt(0))
    base["repeated_product_snapshot_rate_percent"] = percent(
        base["repeated_product_snapshot_count"], base["sampled_snapshot_count"]
    )
    base["valid_actual_price_snapshot_rate_percent"] = percent(
        base["valid_actual_price_snapshot_count"], base["sampled_snapshot_count"]
    )
    base["valid_favorite_snapshot_rate_percent"] = percent(
        base["valid_favorite_snapshot_count"], base["sampled_snapshot_count"]
    )
    base["valid_average_rating_snapshot_rate_percent"] = percent(
        base["valid_average_rating_snapshot_count"], base["sampled_snapshot_count"]
    )
    return base.reset_index()


def build_category_summary(
    snapshots: pd.DataFrame,
    matched: pd.DataFrame,
    category_daily: pd.DataFrame,
) -> pd.DataFrame:
    grouped = snapshots.groupby("category_level_2", sort=True)
    summary = grouped.agg(
        sampled_snapshot_count=("product_id", "size"),
        sampled_unique_product_count=("product_id", "nunique"),
        sampled_seller_count=("seller_name", "nunique"),
    )
    summary["sampled_snapshot_share_percent"] = summary["sampled_snapshot_count"] / len(snapshots) * 100
    summary["repeated_product_count"] = grouped.apply(
        lambda frame: frame.loc[frame["repeated_product_flag"].eq("TRUE"), "product_id"].nunique(),
        include_groups=False,
    )
    summary["repeated_product_rate_percent"] = percent(
        summary["repeated_product_count"], summary["sampled_unique_product_count"]
    )
    interval_counts = matched.groupby("current_category_level_2").size()
    summary["matched_interval_count"] = summary.index.to_series().map(interval_counts).fillna(0).astype("int64")

    daily_grouped = category_daily.groupby("category_level_2", sort=True)
    summary["dates_observed_count"] = daily_grouped["category_observed_on_date_flag"].apply(lambda x: x.eq("TRUE").sum())
    summary["date_coverage_rate_percent"] = summary["dates_observed_count"] / STUDY_DATE_COUNT * 100
    summary["minimum_daily_sampled_snapshot_count"] = daily_grouped["sampled_snapshot_count"].min()
    summary["median_daily_sampled_snapshot_count"] = daily_grouped["sampled_snapshot_count"].median()
    summary["average_daily_sampled_snapshot_count"] = daily_grouped["sampled_snapshot_count"].mean()
    summary["maximum_daily_sampled_snapshot_count"] = daily_grouped["sampled_snapshot_count"].max()

    summary["valid_actual_price_snapshot_count"] = grouped["actual_price_valid_flag"].apply(lambda x: x.eq("TRUE").sum())
    summary["valid_actual_price_snapshot_rate_percent"] = percent(
        summary["valid_actual_price_snapshot_count"], summary["sampled_snapshot_count"]
    )
    summary["median_actual_price"] = grouped["actual_price"].median()
    summary["average_actual_price"] = grouped["actual_price"].mean()
    summary["valid_original_price_snapshot_count"] = grouped["original_price_valid_flag"].apply(lambda x: x.eq("TRUE").sum())
    summary["median_original_price"] = grouped["original_price"].median()
    summary["average_original_price"] = grouped["original_price"].mean()
    summary["valid_discount_snapshot_count"] = grouped["discount_valid_flag"].apply(lambda x: x.eq("TRUE").sum())
    summary["displayed_discount_snapshot_count"] = grouped["discount_amount"].apply(lambda x: x.gt(0).sum())
    summary["displayed_discount_prevalence_percent"] = percent(
        summary["displayed_discount_snapshot_count"], summary["valid_discount_snapshot_count"]
    )
    summary["median_discount_percent"] = grouped["discount_percent"].median()

    summary["valid_favorite_snapshot_count"] = grouped["favorite_valid_flag"].apply(lambda x: x.eq("TRUE").sum())
    summary["valid_favorite_snapshot_rate_percent"] = percent(
        summary["valid_favorite_snapshot_count"], summary["sampled_snapshot_count"]
    )
    summary["median_favorite_count_approx"] = grouped["favorite_count_approx"].median()
    summary["average_favorite_count_approx"] = grouped["favorite_count_approx"].mean()
    summary["rounded_favorite_snapshot_count"] = grouped["favorite_is_rounded_flag"].apply(lambda x: x.eq("TRUE").sum())
    summary["valid_average_rating_snapshot_count"] = grouped["average_rating_valid_flag"].apply(lambda x: x.eq("TRUE").sum())
    summary["valid_average_rating_snapshot_rate_percent"] = percent(
        summary["valid_average_rating_snapshot_count"], summary["sampled_snapshot_count"]
    )
    summary["median_average_rating"] = grouped["average_rating"].median()
    summary["average_average_rating"] = grouped["average_rating"].mean()
    summary["category_changed_product_count"] = grouped.apply(
        lambda frame: frame.loc[frame["category_changed_over_time_flag"].eq("TRUE"), "product_id"].nunique(),
        include_groups=False,
    )
    summary["level2_category_changed_product_count"] = grouped.apply(
        lambda frame: frame.loc[frame["level2_category_changed_over_time_flag"].eq("TRUE"), "product_id"].nunique(),
        include_groups=False,
    )
    summary["duplicate_review_snapshot_count"] = grouped["duplicate_review_flag"].apply(lambda x: x.eq("TRUE").sum())
    summary["coverage_reliability_tier_status"] = "NOT_ASSIGNED_REQUIRES_APPROVED_THRESHOLDS"
    summary["performance_metric_status"] = "NO_VERIFIED_SALES_OR_REVENUE_METRIC"
    return summary.reset_index()


def build_reconciliation(
    source: pd.DataFrame,
    snapshots: pd.DataFrame,
    matched: pd.DataFrame,
    products: pd.DataFrame,
    daily: pd.DataFrame,
    category_daily: pd.DataFrame,
    category_summary: pd.DataFrame,
) -> pd.DataFrame:
    source_products = source["id"].nunique()
    source_categories = source["category_level_2"].nunique()
    date_min = source["observation_date"].min()
    date_max = source["observation_date"].max()
    rows = [
        ("shopee_product_snapshots.csv", "product snapshot", "product_id + observation_date", len(snapshots), len(source),
         snapshots.duplicated(["product_id", "observation_date"]).sum(), len(snapshots), snapshots["product_id"].nunique(), snapshots["category_level_2"].nunique(), "No filtering; one row per validated source row"),
        ("shopee_matched_observations.csv", "consecutive product observation interval", "product_id + current_observation_date", len(matched),
         len(source) - source_products, matched.duplicated(["product_id", "current_observation_date"]).sum(), np.nan,
         matched["product_id"].nunique(), matched["current_category_level_2"].nunique(), "First observation per product intentionally excluded; no sold-count movement"),
        ("shopee_product_coverage.csv", "product", "product_id", len(products), source_products,
         products.duplicated(["product_id"]).sum(), int(products["observation_count"].sum()), len(products),
         pd.concat([products["first_category_level_2"], products["latest_category_level_2"]]).nunique(), "Observation counts sum to source rows"),
        ("shopee_daily_coverage.csv", "observation date", "observation_date", len(daily), source["observation_date"].nunique(),
         daily.duplicated(["observation_date"]).sum(), int(daily["sampled_snapshot_count"].sum()), np.nan,
         int(daily["sampled_category_level2_count"].max()), "Daily snapshot counts sum to source rows"),
        ("shopee_category_daily_coverage.csv", "Level-2 category by study date", "category_level_2 + observation_date", len(category_daily),
         source_categories * source["observation_date"].nunique(), category_daily.duplicated(["category_level_2", "observation_date"]).sum(),
         int(category_daily["sampled_snapshot_count"].sum()), np.nan, category_daily["category_level_2"].nunique(),
         "Complete category-date grid; zero rows represent no sampled observation"),
        ("shopee_category_level2_summary.csv", "Level-2 category", "category_level_2", len(category_summary), source_categories,
         category_summary.duplicated(["category_level_2"]).sum(), int(category_summary["sampled_snapshot_count"].sum()), np.nan,
         len(category_summary), "Category snapshot counts sum to source rows; no ranking"),
    ]
    reconciliation = pd.DataFrame(rows, columns=[
        "table_name", "grain", "primary_key", "row_count", "expected_row_count", "duplicate_key_row_count",
        "reconciled_snapshot_count", "unique_product_count", "level2_category_count", "reconciliation_note",
    ])
    reconciliation["source_date_min"] = date_min
    reconciliation["source_date_max"] = date_max
    reconciliation["status"] = np.where(
        reconciliation["row_count"].eq(reconciliation["expected_row_count"])
        & reconciliation["duplicate_key_row_count"].eq(0),
        "PASS", "FAIL",
    )
    return reconciliation


def assert_business_safety(tables: dict[str, pd.DataFrame]) -> None:
    prohibited = re.compile(
        r"(^|_)(revenue|aov|orders?|units_sold|sales_velocity|sales_growth|momentum_score|category_rank)($|_)",
        re.IGNORECASE,
    )
    for table_name, frame in tables.items():
        prohibited_columns = [column for column in frame.columns if prohibited.search(column)]
        if prohibited_columns:
            raise RuntimeError(f"Unsupported metric columns in {table_name}: {prohibited_columns}")
        counter_columns = [
            column for column in frame.columns
            if ("total_sold" in column or "total_rating" in column) and not column.endswith("metric_status")
        ]
        if counter_columns:
            raise RuntimeError(f"Unverified counters exposed in {table_name}: {counter_columns}")


def main() -> None:
    if not SOURCE_PATH.is_file():
        raise RuntimeError(f"Validated Phase 2 source is missing: {SOURCE_PATH}")
    source_hash_before = sha256(SOURCE_PATH)
    if source_hash_before != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Processed source SHA-256 mismatch: {source_hash_before}")
    raw_paths = [path for path in RAW_CANDIDATES if path.is_file()]
    if len(raw_paths) != 1 or sha256(raw_paths[0]) != EXPECTED_RAW_SHA256:
        raise RuntimeError("Immutable raw source is missing, duplicated, or changed")
    raw_hash_before = sha256(raw_paths[0])

    source = pd.read_csv(SOURCE_PATH, dtype=str, keep_default_na=False, low_memory=False)
    if source.shape != (20_312, 111):
        raise RuntimeError(f"Unexpected validated source shape: {source.shape}")
    if source.duplicated(["id", "w_date"]).any():
        raise RuntimeError("Validated source key is not unique")

    snapshots = build_product_snapshots(source)
    matched = build_matched_observations(snapshots)
    products = build_product_coverage(snapshots)
    daily = build_daily_coverage(snapshots, matched)
    category_daily = build_category_daily_coverage(snapshots, matched)
    category_summary = build_category_summary(snapshots, matched, category_daily)
    tables = {
        "product_snapshots": snapshots,
        "matched_observations": matched,
        "product_coverage": products,
        "daily_coverage": daily,
        "category_daily_coverage": category_daily,
        "category_level2_summary": category_summary,
    }
    assert_business_safety(tables)

    reconciliation = build_reconciliation(
        source, snapshots, matched, products, daily, category_daily, category_summary
    )
    if not reconciliation["status"].eq("PASS").all():
        raise RuntimeError("One or more table reconciliations failed")
    if not matched["elapsed_days"].gt(0).all():
        raise RuntimeError("Matched observations contain a non-positive interval")
    if not matched["sales_movement_metric_status"].eq("NO_VERIFIED_SALES_MOVEMENT_METRIC").all():
        raise RuntimeError("Matched table sales safeguard failed")
    if not category_summary["performance_metric_status"].eq("NO_VERIFIED_SALES_OR_REVENUE_METRIC").all():
        raise RuntimeError("Category summary performance safeguard failed")

    transformation_summary = pd.DataFrame([
        ("shopee_product_snapshots.csv", "Select and clearly rename analysis-useful validated fields", len(source), len(snapshots), "No rows filtered"),
        ("shopee_matched_observations.csv", "Pair each repeated product observation with its immediately preceding snapshot", len(snapshots), len(matched), "First observation per product excluded by grain"),
        ("shopee_product_coverage.csv", "Aggregate observation and validity coverage to product grain", len(snapshots), len(products), "All source rows represented in observation_count"),
        ("shopee_daily_coverage.csv", "Aggregate sampling and validity coverage by observation date", len(snapshots), len(daily), "All source rows represented in sampled_snapshot_count"),
        ("shopee_category_daily_coverage.csv", "Build complete Level-2 category/date coverage grid", len(snapshots), len(category_daily), "Zero-count combinations added explicitly; no source rows duplicated"),
        ("shopee_category_level2_summary.csv", "Aggregate structural, price, engagement, and reliability evidence by Level 2", len(snapshots), len(category_summary), "No sales metric, ranking, or reliability tier assigned"),
    ], columns=["output_table", "transformation", "input_row_count", "output_row_count", "filtering_or_expansion_logic"])

    for name, frame in tables.items():
        write_csv(frame, OUTPUTS[name])
    write_csv(reconciliation, RECONCILIATION_PATH)
    write_csv(transformation_summary, TRANSFORMATION_SUMMARY_PATH)

    source_hash_after = sha256(SOURCE_PATH)
    raw_hash_after = sha256(raw_paths[0])
    if source_hash_after != source_hash_before or raw_hash_after != raw_hash_before:
        raise RuntimeError("A protected source changed during transformation")

    manifest = {
        "source": {
            "path": SOURCE_PATH.relative_to(ROOT).as_posix(),
            "sha256": source_hash_after,
            "rows": len(source),
            "columns": len(source.columns),
        },
        "raw_integrity": {
            "path": raw_paths[0].relative_to(ROOT).as_posix(),
            "sha256": raw_hash_after,
        },
        "study_window": {"first_date": "2023-04-24", "last_date": "2023-05-13", "date_count": 20},
        "tables": {
            name: {
                "path": OUTPUTS[name].relative_to(ROOT).as_posix(),
                "sha256": sha256(OUTPUTS[name]),
                "rows": len(frame),
                "columns": len(frame.columns),
                "schema": list(frame.columns),
            }
            for name, frame in tables.items()
        },
        "safeguards": {
            "verified_sales_metric_created": False,
            "category_ranking_created": False,
            "momentum_score_created": False,
            "reliability_tier_assigned": False,
            "total_sold_status": "UNVERIFIED_UNUSABLE_AS_SALES_METRIC",
            "total_rating_status": "UNVERIFIED_DUPLICATES_TOTAL_SOLD",
        },
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Validated source: {len(source):,} rows x {len(source.columns)} columns")
    for name, frame in tables.items():
        print(f"{name}: {len(frame):,} rows x {len(frame.columns)} columns")
    print("All reconciliations: PASS")
    print("Verified sales/momentum metrics created: 0")


if __name__ == "__main__":
    main()
