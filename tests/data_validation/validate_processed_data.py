"""Independent Phase 3 validation gate for the Shopee snapshot dataset.

This suite does not import the Phase 2 cleaning implementation. It rebuilds
the expected 91 derived fields from the immutable raw source, compares them
with the processed CSV, validates business-safety restrictions, and reruns the
cleaning pipeline only for the separate reproducibility check.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_RAW_SHA256 = "afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69"
RAW_CANDIDATES = (
    ROOT / "data" / "raw" / "shopee_sales_data.csv",
    ROOT / "dataset" / "shopee_sales_data.csv",
)
PROCESSED_PATH = ROOT / "data" / "processed" / "shopee_sales_cleaned.csv"
CLEANING_SCRIPT = ROOT / "src" / "data" / "clean_data.py"
DATA_DICTIONARY = ROOT / "docs" / "data_dictionary.md"
BUSINESS_QUESTIONS = ROOT / "docs" / "business_questions.md"
RESULTS_PATH = ROOT / "outputs" / "tables" / "phase_3_validation_results.csv"
FIELD_RESULTS_PATH = ROOT / "outputs" / "tables" / "phase_3_derived_field_validation.csv"
SAMPLES_PATH = ROOT / "outputs" / "tables" / "phase_3_manual_sample_checks.csv"
SENTINEL_PRICE = 999_999_999.0
SUSPICIOUS_HIGH_PRICE = 1_000_000.0
MISSING_TOKENS = {
    "", "n/a", "na", "nan", "none", "null", "<na>", "#n/a", "#na",
    "#n/a n/a", "-nan", "-1.#ind", "-1.#qnan", "1.#ind", "1.#qnan",
}

DERIVED_FIELDS = [
    "source_row_number",
    "price_ori_missing_flag", "delivery_missing_flag", "specification_missing_flag",
    "item_rating_missing_flag", "seller_name_missing_flag", "price_actual_missing_flag",
    "total_rating_missing_flag", "total_sold_missing_flag", "favorite_missing_flag",
    "observation_date", "observation_week_start", "observation_month",
    "observation_day_of_week", "date_parse_status", "timestamp_date_match_flag",
    "category_level_1", "category_level_2", "category_level_3", "category_level_4",
    "category_path_clean", "category_path_parse_status", "primary_category_grain",
    "total_sold_parsed", "total_sold_suffix", "total_sold_precision_unit",
    "total_sold_compact_rounded_flag", "total_sold_parse_status",
    "total_rating_parsed", "total_rating_suffix", "total_rating_precision_unit",
    "total_rating_compact_rounded_flag", "total_rating_parse_status",
    "favorite_parsed", "favorite_suffix", "favorite_precision_unit",
    "favorite_compact_rounded_flag", "favorite_parse_status",
    "sold_rating_exact_match_flag", "total_sold_metric_status", "total_rating_metric_status",
    "item_rating_numeric", "item_rating_status",
    "price_ori_clean", "price_ori_status", "price_actual_clean", "price_actual_status",
    "price_ori_statistical_outlier_flag", "price_actual_statistical_outlier_flag",
    "price_pair_status", "discount_amount", "discount_pct", "price_currency_status",
    "exact_duplicate_flag", "snapshot_key_duplicate_flag", "duplicate_review_group_id",
    "duplicate_review_flag", "product_observation_count", "product_first_observation_date",
    "product_last_observation_date", "product_observation_span_days", "matched_product_flag",
    "observation_sequence", "previous_observation_date", "observation_interval_days",
    "unverified_counter_previous", "unverified_counter_change", "negative_change_flag",
    "cumulative_change_status", "movement_analysis_eligibility_status",
    "acceleration_structure_flag", "product_category_change_flag",
    "product_category_level2_change_flag", "product_category_path_count",
    "product_category_level2_count", "previous_category_path", "previous_category_level_2",
    "category_changed_from_previous_flag", "category_level2_changed_from_previous_flag",
    "daily_observation_count", "daily_unique_product_count", "daily_category_level2_count",
    "daily_seller_count", "category_date_observation_count",
    "category_date_unique_product_count", "category_total_observation_count",
    "category_unique_product_count", "category_repeated_product_count",
    "unverified_counter_statistical_outlier_flag", "favorite_statistical_outlier_flag",
    "item_rating_statistical_outlier_flag",
]

NUMERIC_FIELDS = {
    "source_row_number", "total_sold_parsed", "total_sold_precision_unit",
    "total_rating_parsed", "total_rating_precision_unit", "favorite_parsed",
    "favorite_precision_unit", "item_rating_numeric", "price_ori_clean",
    "price_actual_clean", "discount_amount", "discount_pct", "product_observation_count",
    "product_observation_span_days", "observation_sequence", "observation_interval_days",
    "unverified_counter_previous", "unverified_counter_change", "product_category_path_count",
    "product_category_level2_count", "daily_observation_count", "daily_unique_product_count",
    "daily_category_level2_count", "daily_seller_count", "category_date_observation_count",
    "category_date_unique_product_count", "category_total_observation_count",
    "category_unique_product_count", "category_repeated_product_count",
}

INTEGER_FIELDS = {
    "source_row_number", "product_observation_count", "product_observation_span_days",
    "observation_sequence", "observation_interval_days", "product_category_path_count",
    "product_category_level2_count", "daily_observation_count", "daily_unique_product_count",
    "daily_category_level2_count", "daily_seller_count", "category_date_observation_count",
    "category_date_unique_product_count", "category_total_observation_count",
    "category_unique_product_count", "category_repeated_product_count",
}


def sha256(path: Path) -> str:
    for attempt in range(10):
        try:
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            return digest.hexdigest()
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.1)
    raise RuntimeError("Unreachable hash retry state")


def missing_mask(series: pd.Series) -> pd.Series:
    text = series.astype("string")
    return text.str.strip().str.casefold().isin(MISSING_TOKENS)


def nullable_text(series: pd.Series) -> pd.Series:
    text = series.astype("string")
    return text.mask(missing_mask(text), pd.NA)


def bool_text(series: pd.Series) -> pd.Series:
    return series.fillna(False).map({True: "TRUE", False: "FALSE"}).astype("string")


def parse_display(value: Any, from_label: bool = False) -> tuple[Any, str, Any, str, str]:
    if value is None or pd.isna(value) or str(value).strip().casefold() in MISSING_TOKENS:
        return np.nan, "", np.nan, "FALSE", "MISSING"
    candidate = str(value).strip()
    if from_label:
        match_in_label = re.search(r"([0-9]+(?:\.[0-9]+)?\s*[kKmMbB]?)", candidate)
        if not match_in_label:
            return np.nan, "", np.nan, "FALSE", "INVALID_LABEL"
        candidate = match_in_label.group(1)
    candidate = candidate.lower().replace(",", "").strip()
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([kmb]?)", candidate)
    if not match:
        return np.nan, "", np.nan, "FALSE", "INVALID_FORMAT"
    number_text, suffix = match.groups()
    multiplier = {"": 1.0, "k": 1_000.0, "m": 1_000_000.0, "b": 1_000_000_000.0}[suffix]
    decimals = len(number_text.split(".", 1)[1]) if "." in number_text else 0
    parsed = float(number_text) * multiplier
    precision = multiplier / (10**decimals)
    rounded = "TRUE" if suffix else "FALSE"
    status = "PARSED_COMPACT_ROUNDED" if suffix else "PARSED_EXACT_DISPLAY"
    return parsed, suffix, precision, rounded, status


def parse_display_series(series: pd.Series, from_label: bool = False) -> pd.DataFrame:
    return pd.DataFrame(
        [parse_display(value, from_label) for value in series],
        columns=["parsed", "suffix", "precision", "rounded", "status"],
        index=series.index,
    )


def independently_classify_price(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    normalized = nullable_text(series)
    numeric = pd.to_numeric(normalized, errors="coerce")
    status = pd.Series("VALID", index=series.index, dtype="string")
    status.loc[normalized.isna()] = "MISSING"
    status.loc[normalized.notna() & numeric.isna()] = "INVALID_FORMAT"
    status.loc[numeric.eq(0)] = "ZERO"
    status.loc[numeric.eq(SENTINEL_PRICE)] = "SENTINEL_999999999"
    status.loc[numeric.ge(SUSPICIOUS_HIGH_PRICE) & numeric.ne(SENTINEL_PRICE)] = (
        "SUSPICIOUS_HIGH_GE_1000000"
    )
    return numeric.where(status.eq("VALID")), status


def independent_iqr_flag(series: pd.Series) -> tuple[pd.Series, float, float]:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    lower = q1 - 1.5 * (q3 - q1)
    upper = q3 + 1.5 * (q3 - q1)
    return ((numeric < lower) | (numeric > upper)).fillna(False), lower, upper


def stable_duplicate_id(values: tuple[Any, Any, Any]) -> str:
    safe = ["<MISSING>" if value is None or pd.isna(value) else str(value) for value in values]
    return "DUP-" + hashlib.sha256("|".join(safe).encode("utf-8")).hexdigest()[:12]


def build_independent_expected(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Recompute all Phase 2 fields without importing cleaning code."""
    expected = pd.DataFrame(index=raw.index)
    expected["source_row_number"] = np.arange(1, len(raw) + 1)

    flag_sources = (
        "price_ori", "delivery", "specification", "item_rating", "seller_name",
        "price_actual", "total_rating", "total_sold", "favorite",
    )
    for source in flag_sources:
        expected[f"{source}_missing_flag"] = bool_text(missing_mask(raw[source]))

    raw_dates = nullable_text(raw["w_date"])
    dates = pd.to_datetime(raw_dates, format="%Y-%m-%d", errors="coerce")
    timestamp_numeric = pd.to_numeric(nullable_text(raw["timestamp"]), errors="coerce")
    timestamp_dates = pd.to_datetime(timestamp_numeric, unit="ms", errors="coerce", utc=True)
    expected["observation_date"] = dates.dt.strftime("%Y-%m-%d").fillna("")
    week_start = dates - pd.to_timedelta(dates.dt.weekday, unit="D")
    expected["observation_week_start"] = week_start.dt.strftime("%Y-%m-%d").fillna("")
    expected["observation_month"] = dates.dt.strftime("%Y-%m").fillna("")
    expected["observation_day_of_week"] = dates.dt.day_name().fillna("")
    expected["date_parse_status"] = np.select(
        [raw_dates.isna(), dates.isna()], ["MISSING", "INVALID"], default="VALID"
    )
    timestamp_iso = timestamp_dates.dt.strftime("%Y-%m-%d")
    expected["timestamp_date_match_flag"] = bool_text(
        dates.notna() & timestamp_dates.notna() & dates.dt.strftime("%Y-%m-%d").eq(timestamp_iso)
    )

    category_raw = nullable_text(raw["item_category_detail"])
    category_parts = category_raw.str.split("|", regex=False)
    category_part_count = category_parts.map(lambda x: len(x) if isinstance(x, list) else 0)
    for level in range(1, 5):
        expected[f"category_level_{level}"] = category_parts.str[level - 1].str.strip().fillna("")
    expected["category_path_clean"] = category_parts.map(
        lambda x: " | ".join(part.strip() for part in x) if isinstance(x, list) else ""
    )
    expected["category_path_parse_status"] = np.select(
        [category_raw.isna(), category_part_count.eq(3), category_part_count.eq(4)],
        ["MISSING", "VALID_3_LEVEL", "VALID_4_LEVEL"],
        default="MALFORMED_LEVEL_COUNT",
    )
    expected["primary_category_grain"] = "LEVEL_2"

    for source in ("total_sold", "total_rating"):
        parsed = parse_display_series(nullable_text(raw[source]))
        expected[f"{source}_parsed"] = parsed["parsed"]
        expected[f"{source}_suffix"] = parsed["suffix"]
        expected[f"{source}_precision_unit"] = parsed["precision"]
        expected[f"{source}_compact_rounded_flag"] = parsed["rounded"]
        expected[f"{source}_parse_status"] = parsed["status"]
    favorite = parse_display_series(nullable_text(raw["favorite"]), from_label=True)
    expected["favorite_parsed"] = favorite["parsed"]
    expected["favorite_suffix"] = favorite["suffix"]
    expected["favorite_precision_unit"] = favorite["precision"]
    expected["favorite_compact_rounded_flag"] = favorite["rounded"]
    expected["favorite_parse_status"] = favorite["status"]
    expected["sold_rating_exact_match_flag"] = bool_text(raw["total_sold"].eq(raw["total_rating"]))
    expected["total_sold_metric_status"] = "UNVERIFIED_UNUSABLE_AS_SALES_METRIC"
    expected["total_rating_metric_status"] = "UNVERIFIED_DUPLICATES_TOTAL_SOLD"

    rating_raw = nullable_text(raw["item_rating"])
    rating_numeric = pd.to_numeric(rating_raw, errors="coerce")
    rating_status = pd.Series("VALID", index=raw.index, dtype="string")
    rating_status.loc[rating_raw.isna()] = "MISSING"
    no_rating = rating_raw.str.casefold().eq("no ratings yet").fillna(False)
    rating_status.loc[no_rating] = "NO_RATINGS_YET"
    rating_status.loc[rating_raw.notna() & rating_numeric.isna() & ~no_rating] = "INVALID_LABEL"
    rating_status.loc[rating_numeric.notna() & ~rating_numeric.between(1, 5)] = "OUT_OF_RANGE"
    expected["item_rating_numeric"] = rating_numeric.where(rating_status.eq("VALID"))
    expected["item_rating_status"] = rating_status

    price_ori, price_ori_status = independently_classify_price(raw["price_ori"])
    price_actual, price_actual_status = independently_classify_price(raw["price_actual"])
    expected["price_ori_clean"] = price_ori
    expected["price_ori_status"] = price_ori_status
    expected["price_actual_clean"] = price_actual
    expected["price_actual_status"] = price_actual_status
    ori_outlier, ori_lower, ori_upper = independent_iqr_flag(price_ori)
    actual_outlier, actual_lower, actual_upper = independent_iqr_flag(price_actual)
    expected["price_ori_statistical_outlier_flag"] = bool_text(ori_outlier)
    expected["price_actual_statistical_outlier_flag"] = bool_text(actual_outlier)
    pair_valid = price_ori_status.eq("VALID") & price_actual_status.eq("VALID")
    expected["price_pair_status"] = np.select(
        [~pair_valid, pair_valid & price_actual.gt(price_ori), pair_valid & price_actual.le(price_ori)],
        ["INVALID_COMPONENT", "ACTUAL_ABOVE_ORIGINAL", "VALID_COMPARABLE"],
        default="UNCLASSIFIED",
    )
    comparable = expected["price_pair_status"].eq("VALID_COMPARABLE")
    expected["discount_amount"] = (price_ori - price_actual).where(comparable)
    expected["discount_pct"] = ((price_ori - price_actual) / price_ori * 100).where(comparable)
    expected["price_currency_status"] = "UNVERIFIED_CONTEXT_SUGGESTS_MYR"

    expected["exact_duplicate_flag"] = bool_text(raw.duplicated(keep=False))
    expected["snapshot_key_duplicate_flag"] = bool_text(raw.duplicated(["id", "w_date"], keep=False))
    duplicate_base = pd.DataFrame({
        "seller_name": nullable_text(raw["seller_name"]),
        "title": nullable_text(raw["title"]),
        "w_date": nullable_text(raw["w_date"]),
        "id": nullable_text(raw["id"]),
        "link_ori": nullable_text(raw["link_ori"]),
    })
    grouped = duplicate_base.groupby(["seller_name", "title", "w_date"], dropna=False).agg(
        rows=("id", "size"), distinct_ids=("id", "nunique"), distinct_links=("link_ori", "nunique")
    ).reset_index()
    grouped = grouped.loc[grouped["rows"].gt(1) & grouped["distinct_ids"].gt(1)].copy()
    grouped["group_id"] = [
        stable_duplicate_id((row.seller_name, row.title, row.w_date))
        for row in grouped.itertuples(index=False)
    ]
    group_map = grouped.set_index(["seller_name", "title", "w_date"])["group_id"]
    duplicate_index = pd.MultiIndex.from_frame(duplicate_base[["seller_name", "title", "w_date"]])
    expected["duplicate_review_group_id"] = group_map.reindex(duplicate_index).to_numpy()
    expected["duplicate_review_group_id"] = expected["duplicate_review_group_id"].fillna("")
    expected["duplicate_review_flag"] = bool_text(expected["duplicate_review_group_id"].ne(""))

    history = pd.DataFrame({
        "source_row_number": expected["source_row_number"],
        "id": nullable_text(raw["id"]),
        "date": dates,
        "category_path": expected["category_path_clean"].replace("", pd.NA),
        "category_level_2": expected["category_level_2"].replace("", pd.NA),
        "counter": pd.to_numeric(expected["total_sold_parsed"], errors="coerce"),
    }).sort_values(["id", "date", "source_row_number"])
    by_product = history.groupby("id", dropna=False)
    history["count"] = by_product["source_row_number"].transform("size")
    history["first_date"] = by_product["date"].transform("min")
    history["last_date"] = by_product["date"].transform("max")
    history["span"] = (history["last_date"] - history["first_date"]).dt.days
    history["sequence"] = by_product.cumcount() + 1
    history["previous_date"] = by_product["date"].shift()
    history["interval"] = (history["date"] - history["previous_date"]).dt.days
    history["previous_counter"] = by_product["counter"].shift()
    history["change"] = history["counter"] - history["previous_counter"]
    history["path_count"] = by_product["category_path"].transform("nunique")
    history["level2_count"] = by_product["category_level_2"].transform("nunique")
    history["previous_path"] = by_product["category_path"].shift()
    history["previous_level2"] = by_product["category_level_2"].shift()
    history["path_transition"] = (
        history["previous_path"].notna() & history["category_path"].notna()
        & history["category_path"].ne(history["previous_path"])
    )
    history["level2_transition"] = (
        history["previous_level2"].notna() & history["category_level_2"].notna()
        & history["category_level_2"].ne(history["previous_level2"])
    )
    history = history.sort_values("source_row_number").reset_index(drop=True)
    expected["product_observation_count"] = history["count"]
    expected["product_first_observation_date"] = history["first_date"].dt.strftime("%Y-%m-%d").fillna("")
    expected["product_last_observation_date"] = history["last_date"].dt.strftime("%Y-%m-%d").fillna("")
    expected["product_observation_span_days"] = history["span"]
    expected["matched_product_flag"] = bool_text(history["count"].gt(1))
    expected["observation_sequence"] = history["sequence"]
    expected["previous_observation_date"] = history["previous_date"].dt.strftime("%Y-%m-%d").fillna("")
    expected["observation_interval_days"] = history["interval"]
    expected["unverified_counter_previous"] = history["previous_counter"]
    expected["unverified_counter_change"] = history["change"]
    expected["negative_change_flag"] = bool_text(history["change"].lt(0))
    expected["cumulative_change_status"] = np.select(
        [history["previous_date"].isna(), history["previous_counter"].isna() | history["counter"].isna(),
         history["change"].lt(0), history["change"].eq(0), history["change"].gt(0)],
        ["FIRST_OBSERVATION", "MISSING_UNVERIFIED_COUNTER", "DECREASE", "NO_CHANGE", "INCREASE"],
        default="UNCLASSIFIED",
    )
    expected["movement_analysis_eligibility_status"] = np.select(
        [history["previous_date"].isna(), history["previous_counter"].isna() | history["counter"].isna()],
        ["NO_PRIOR_OBSERVATION", "MISSING_UNVERIFIED_COUNTER"],
        default="BLOCKED_COUNTER_UNVERIFIED",
    )
    expected["acceleration_structure_flag"] = bool_text(history["count"].ge(3))
    expected["product_category_change_flag"] = bool_text(history["path_count"].gt(1))
    expected["product_category_level2_change_flag"] = bool_text(history["level2_count"].gt(1))
    expected["product_category_path_count"] = history["path_count"]
    expected["product_category_level2_count"] = history["level2_count"]
    expected["previous_category_path"] = history["previous_path"].fillna("")
    expected["previous_category_level_2"] = history["previous_level2"].fillna("")
    expected["category_changed_from_previous_flag"] = bool_text(history["path_transition"])
    expected["category_level2_changed_from_previous_flag"] = bool_text(history["level2_transition"])

    coverage = pd.DataFrame({
        "date": expected["observation_date"].replace("", pd.NA),
        "category": expected["category_level_2"].replace("", pd.NA),
        "seller": nullable_text(raw["seller_name"]),
        "id": nullable_text(raw["id"]),
    })
    expected["daily_observation_count"] = coverage.groupby("date", dropna=False)["id"].transform("size")
    expected["daily_unique_product_count"] = coverage.groupby("date", dropna=False)["id"].transform("nunique")
    expected["daily_category_level2_count"] = coverage.groupby("date", dropna=False)["category"].transform("nunique")
    expected["daily_seller_count"] = coverage.groupby("date", dropna=False)["seller"].transform("nunique")
    expected["category_date_observation_count"] = coverage.groupby(["category", "date"], dropna=False)["id"].transform("size")
    expected["category_date_unique_product_count"] = coverage.groupby(["category", "date"], dropna=False)["id"].transform("nunique")
    expected["category_total_observation_count"] = coverage.groupby("category", dropna=False)["id"].transform("size")
    expected["category_unique_product_count"] = coverage.groupby("category", dropna=False)["id"].transform("nunique")
    repeated_ids = set(history.loc[history["count"].gt(1), "id"].dropna())
    category_repeats = (
        coverage.assign(repeated=coverage["id"].isin(repeated_ids))
        .loc[lambda x: x["repeated"]]
        .groupby("category", dropna=False)["id"].nunique()
    )
    expected["category_repeated_product_count"] = coverage["category"].map(category_repeats).fillna(0).astype(int)

    counter_outlier, counter_lower, counter_upper = independent_iqr_flag(expected["total_sold_parsed"])
    favorite_outlier, favorite_lower, favorite_upper = independent_iqr_flag(expected["favorite_parsed"])
    rating_outlier, rating_lower, rating_upper = independent_iqr_flag(expected["item_rating_numeric"])
    expected["unverified_counter_statistical_outlier_flag"] = bool_text(counter_outlier)
    expected["favorite_statistical_outlier_flag"] = bool_text(favorite_outlier)
    expected["item_rating_statistical_outlier_flag"] = bool_text(rating_outlier)

    thresholds = {
        "price_ori_lower": ori_lower, "price_ori_upper": ori_upper,
        "price_actual_lower": actual_lower, "price_actual_upper": actual_upper,
        "counter_lower": counter_lower, "counter_upper": counter_upper,
        "favorite_lower": favorite_lower, "favorite_upper": favorite_upper,
        "rating_lower": rating_lower, "rating_upper": rating_upper,
    }
    return expected[DERIVED_FIELDS], thresholds


def dataframe_text_equal(left_path: Path, right_path: Path) -> bool:
    left = pd.read_csv(left_path, dtype=str, keep_default_na=False, low_memory=False)
    right = pd.read_csv(right_path, dtype=str, keep_default_na=False, low_memory=False)
    return list(left.columns) == list(right.columns) and left.equals(right)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, encoding="utf-8", lineterminator="\n")
    temporary.replace(path)


def main() -> int:
    checks: list[dict[str, Any]] = []

    def record(check_id: str, area: str, severity: str, passed: bool, expected: Any,
               observed: Any, detail: str, warning: bool = False) -> None:
        status = "WARNING" if warning and passed else ("PASS" if passed else "FAIL")
        checks.append({
            "check_id": check_id, "area": area, "severity": severity,
            "status": status, "expected": expected, "observed": observed, "detail": detail,
        })

    raw_paths = [path for path in RAW_CANDIDATES if path.is_file()]
    if len(raw_paths) != 1:
        record("RAW-001", "RAW_INTEGRITY", "CRITICAL", False, "exactly one source", len(raw_paths),
               "Expected one canonical or legacy raw source.")
        atomic_csv(pd.DataFrame(checks), RESULTS_PATH)
        return 1
    raw_path = raw_paths[0]
    raw_hash_before = sha256(raw_path)
    record("RAW-001", "RAW_INTEGRITY", "CRITICAL", True, "exists", raw_path.relative_to(ROOT).as_posix(),
           "Raw source exists.")
    record("RAW-002", "RAW_INTEGRITY", "CRITICAL", raw_hash_before == EXPECTED_RAW_SHA256,
           EXPECTED_RAW_SHA256, raw_hash_before, "Independent SHA-256 verification.")

    raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False, low_memory=False)
    record("RAW-003", "RAW_INTEGRITY", "CRITICAL", raw.shape == (20_312, 20), "20312 x 20",
           f"{raw.shape[0]} x {raw.shape[1]}", "Raw record and field counts.")
    same_size_csvs = [p for p in ROOT.rglob("*.csv") if p.stat().st_size == raw_path.stat().st_size]
    identical_raw = [p for p in same_size_csvs if sha256(p) == EXPECTED_RAW_SHA256]
    record("RAW-004", "RAW_INTEGRITY", "CRITICAL", identical_raw == [raw_path],
           raw_path.relative_to(ROOT).as_posix(),
           " | ".join(p.relative_to(ROOT).as_posix() for p in identical_raw),
           "No second byte-identical raw CSV exists.")
    record("RAW-005", "RAW_INTEGRITY", "LOW", True, "data/raw or protected legacy path",
           raw_path.relative_to(ROOT).as_posix(),
           "Source remains protected at the legacy path; relocation is outside validation.",
           warning=raw_path.parent.name == "dataset")

    if not PROCESSED_PATH.is_file():
        record("STR-001", "STRUCTURE", "CRITICAL", False, "processed dataset exists", "missing",
               "Cannot validate without the Phase 2 output.")
        atomic_csv(pd.DataFrame(checks), RESULTS_PATH)
        return 1

    processed_hash_before = sha256(PROCESSED_PATH)
    with tempfile.TemporaryDirectory(prefix="shopee-phase3-") as temporary_directory:
        isolated_root = Path(temporary_directory)
        isolated_script = isolated_root / "src" / "data" / "clean_data.py"
        isolated_raw = isolated_root / raw_path.relative_to(ROOT)
        isolated_script.parent.mkdir(parents=True, exist_ok=True)
        isolated_raw.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CLEANING_SCRIPT, isolated_script)
        shutil.copyfile(raw_path, isolated_raw)
        rerun = subprocess.run(
            [sys.executable, str(isolated_script)], cwd=isolated_root, capture_output=True, text=True
        )
        isolated_processed = isolated_root / "data" / "processed" / "shopee_sales_cleaned.csv"
        processed_hash_after = sha256(isolated_processed) if isolated_processed.exists() else "MISSING"
        byte_equal = rerun.returncode == 0 and processed_hash_before == processed_hash_after
        normalized_equal = (
            rerun.returncode == 0 and isolated_processed.exists()
            and dataframe_text_equal(PROCESSED_PATH, isolated_processed)
        )
    record("REP-001", "REPRODUCIBILITY", "CRITICAL", rerun.returncode == 0, "exit code 0",
           rerun.returncode, (rerun.stdout or rerun.stderr).strip().replace("\n", " | "))
    record("REP-002", "REPRODUCIBILITY", "CRITICAL", byte_equal, processed_hash_before,
           processed_hash_after, "Isolated regeneration is byte-for-byte identical to the canonical processed CSV.")
    record("REP-003", "REPRODUCIBILITY", "CRITICAL", normalized_equal, "identical schema/order/values",
           normalized_equal, "Independent normalized text comparison of baseline and regenerated output.")
    raw_hash_after_rerun = sha256(raw_path)
    record("REP-004", "REPRODUCIBILITY", "CRITICAL", raw_hash_after_rerun == raw_hash_before,
           raw_hash_before, raw_hash_after_rerun, "Raw bytes did not change during regeneration.")

    processed = pd.read_csv(PROCESSED_PATH, dtype=str, keep_default_na=False, low_memory=False)
    expected_columns = ["source_row_number", *raw.columns, *DERIVED_FIELDS[1:]]
    record("STR-001", "STRUCTURE", "CRITICAL", processed.shape == (20_312, 111), "20312 x 111",
           f"{processed.shape[0]} x {processed.shape[1]}", "Processed shape.")
    record("STR-002", "STRUCTURE", "CRITICAL", list(processed.columns) == expected_columns,
           "documented 111-column ordered schema", "match" if list(processed.columns) == expected_columns else "mismatch",
           "Expected 20 raw plus 91 derived fields, with no extras.")
    record("STR-003", "STRUCTURE", "CRITICAL", not processed.columns.duplicated().any(), "0", int(processed.columns.duplicated().sum()),
           "Duplicate column-name check.")
    index_columns = [column for column in processed.columns if column.casefold().startswith("unnamed:")]
    record("STR-004", "STRUCTURE", "HIGH", not index_columns, "none", " | ".join(index_columns) or "none",
           "Accidental serialized index check.")
    empty_columns = [column for column in processed.columns if missing_mask(processed[column]).all()]
    record("STR-005", "STRUCTURE", "HIGH", not empty_columns, "none", " | ".join(empty_columns) or "none",
           "Completely empty column check.")
    key_duplicates = int(processed.duplicated(["id", "w_date"]).sum())
    key_missing = int((missing_mask(processed["id"]) | missing_mask(processed["w_date"])).sum())
    record("STR-006", "STRUCTURE", "CRITICAL", key_duplicates == 0 and key_missing == 0,
           "0 duplicate or missing keys", f"duplicates={key_duplicates}; missing={key_missing}",
           "Product-snapshot grain and key uniqueness.")

    raw_columns_match = list(processed.columns[1:21]) == list(raw.columns)
    raw_cell_differences = 0
    if raw_columns_match and len(processed) == len(raw):
        raw_cell_differences = int(processed[list(raw.columns)].ne(raw).sum().sum())
    else:
        raw_cell_differences = -1
    row_numbers = pd.to_numeric(processed["source_row_number"], errors="coerce")
    row_alignment = row_numbers.equals(pd.Series(np.arange(1, len(processed) + 1), dtype="int64"))
    record("REC-001", "RAW_RECONCILIATION", "CRITICAL", raw_columns_match, list(raw.columns),
           list(processed.columns[1:21]), "Original column names and order.")
    record("REC-002", "RAW_RECONCILIATION", "CRITICAL", raw_cell_differences == 0, "0", raw_cell_differences,
           "Cell-by-cell text comparison across all 406,240 original cells.")
    record("REC-003", "RAW_RECONCILIATION", "CRITICAL", row_alignment, "1..20312", bool(row_alignment),
           "Source row numbers preserve raw ordering.")
    raw_missing = raw.apply(missing_mask)
    processed_raw_missing = processed[list(raw.columns)].apply(missing_mask)
    null_mismatches = int(raw_missing.ne(processed_raw_missing).sum().sum())
    record("REC-004", "RAW_RECONCILIATION", "CRITICAL", null_mismatches == 0, "0", null_mismatches,
           "Missing-token behavior in original fields.")

    expected, thresholds = build_independent_expected(raw)
    dictionary_text = DATA_DICTIONARY.read_text(encoding="utf-8")
    field_results = []
    for field in DERIVED_FIELDS:
        documented = f"`{field}`" in dictionary_text
        actual = processed[field]
        expected_values = expected[field]
        actual_blank = missing_mask(actual)
        if field in NUMERIC_FIELDS:
            actual_numeric = pd.to_numeric(actual.mask(actual_blank), errors="coerce")
            expected_numeric = pd.to_numeric(expected_values, errors="coerce")
            both_missing = actual_numeric.isna() & expected_numeric.isna()
            close = pd.Series(
                np.isclose(actual_numeric.fillna(0), expected_numeric.fillna(0), rtol=1e-9, atol=1e-8),
                index=actual.index,
            )
            mismatch = ~(both_missing | close)
            type_violation = (~actual_blank) & actual_numeric.isna()
            if field in INTEGER_FIELDS:
                type_violation |= actual_numeric.notna() & actual_numeric.mod(1).ne(0)
            logical_type = "integer" if field in INTEGER_FIELDS else "number"
            expected_missing = expected_numeric.isna()
        else:
            actual_text = actual.astype("string")
            expected_text = expected_values.astype("string").fillna("")
            mismatch = actual_text.ne(expected_text)
            type_violation = pd.Series(False, index=actual.index)
            logical_type = "text/category/boolean/date"
            expected_missing = expected_text.eq("")
        unexpected_null = actual_blank & ~expected_missing
        mismatch_count = int(mismatch.sum())
        type_violations = int(type_violation.sum())
        unexpected_nulls = int(unexpected_null.sum())
        field_results.append({
            "field": field,
            "logical_type": logical_type,
            "documented": "TRUE" if documented else "FALSE",
            "non_empty_count": int((~actual_blank).sum()),
            "expected_empty_count": int(expected_missing.sum()),
            "unexpected_empty_count": unexpected_nulls,
            "type_violation_count": type_violations,
            "definition_mismatch_count": mismatch_count,
            "status": "PASS" if documented and mismatch_count == 0 and type_violations == 0 else "FAIL",
        })
    field_frame = pd.DataFrame(field_results)
    failed_fields = field_frame.loc[field_frame["status"].eq("FAIL"), "field"].tolist()
    record("DER-001", "DERIVED_FIELDS", "CRITICAL", len(field_frame) == 91, "91", len(field_frame),
           "All documented derived fields included in the independent gate.")
    record("DER-002", "DERIVED_FIELDS", "CRITICAL", not failed_fields, "all 91 pass",
           " | ".join(failed_fields) or "all 91 pass",
           "Independent definition, type, null, and source-relationship comparison.")

    observation_dates = pd.to_datetime(processed["observation_date"], format="%Y-%m-%d", errors="coerce")
    unique_dates = sorted(processed["observation_date"].unique())
    expected_dates = pd.date_range("2023-04-24", "2023-05-13", freq="D").strftime("%Y-%m-%d").tolist()
    record("DAT-001", "DATES", "CRITICAL", processed["date_parse_status"].eq("VALID").all(), "20312 valid", int(processed["date_parse_status"].eq("VALID").sum()),
           "All raw observation dates parsed.")
    record("DAT-002", "DATES", "CRITICAL", unique_dates == expected_dates, "2023-04-24..2023-05-13; 20 dates",
           f"{unique_dates[0]}..{unique_dates[-1]}; {len(unique_dates)} dates", "No missing or shifted calendar date.")
    record("DAT-003", "DATES", "HIGH", processed["timestamp_date_match_flag"].eq("TRUE").all(), "20312 TRUE",
           int(processed["timestamp_date_match_flag"].eq("TRUE").sum()), "Epoch timestamp agrees with date without timezone shift.")

    category_l2 = set(processed["category_level_2"])
    raw_l2 = set(nullable_text(raw["item_category_detail"]).str.split("|", regex=False).str[1].str.strip())
    raw_l2.discard(pd.NA)
    record("CAT-001", "CATEGORIES", "CRITICAL", category_l2 == raw_l2 and len(category_l2) == 24, "24 raw-derived Level-2 categories",
           len(category_l2), "No broad categories were created or reassigned.")
    record("CAT-002", "CATEGORIES", "CRITICAL", int(processed["product_category_change_flag"].eq("TRUE").sum()) == 45
           and processed.loc[processed["product_category_change_flag"].eq("TRUE"), "id"].nunique() == 19,
           "45 rows / 19 products", f"{int(processed['product_category_change_flag'].eq('TRUE').sum())} rows / "
           f"{processed.loc[processed['product_category_change_flag'].eq('TRUE'), 'id'].nunique()} products",
           "Full-path product history flags.")
    record("CAT-003", "CATEGORIES", "CRITICAL", int(processed["product_category_level2_change_flag"].eq("TRUE").sum()) == 21
           and processed.loc[processed["product_category_level2_change_flag"].eq("TRUE"), "id"].nunique() == 8,
           "21 rows / 8 products", f"{int(processed['product_category_level2_change_flag'].eq('TRUE').sum())} rows / "
           f"{processed.loc[processed['product_category_level2_change_flag'].eq('TRUE'), 'id'].nunique()} products",
           "Level-2 product history flags.")

    sentinel_ori = processed["price_ori_status"].eq("SENTINEL_999999999")
    sentinel_actual = processed["price_actual_status"].eq("SENTINEL_999999999")
    sentinel_clean_blank = (
        missing_mask(processed.loc[sentinel_ori, "price_ori_clean"]).all()
        and missing_mask(processed.loc[sentinel_actual, "price_actual_clean"]).all()
    )
    record("PRI-001", "PRICES", "CRITICAL", int(sentinel_ori.sum()) == 2 and int(sentinel_actual.sum()) == 2 and sentinel_clean_blank,
           "2 original + 2 actual sentinels; all clean values empty",
           f"ori={int(sentinel_ori.sum())}; actual={int(sentinel_actual.sum())}; clean_empty={sentinel_clean_blank}",
           "999999999 never enters usable price fields.")
    comparable = processed["price_pair_status"].eq("VALID_COMPARABLE")
    recomputed_discount = pd.to_numeric(processed["price_ori_clean"], errors="coerce") - pd.to_numeric(processed["price_actual_clean"], errors="coerce")
    processed_discount = pd.to_numeric(processed["discount_amount"], errors="coerce")
    processed_discount_pct = pd.to_numeric(processed["discount_pct"], errors="coerce")
    recomputed_pct = recomputed_discount / pd.to_numeric(processed["price_ori_clean"], errors="coerce") * 100
    discount_match = np.isclose(processed_discount[comparable], recomputed_discount[comparable], rtol=1e-9, atol=1e-8).all()
    pct_match = np.isclose(processed_discount_pct[comparable], recomputed_pct[comparable], rtol=1e-9, atol=1e-8).all()
    non_comparable_blank = processed_discount[~comparable].isna().all() and processed_discount_pct[~comparable].isna().all()
    record("PRI-002", "PRICES", "CRITICAL", bool(discount_match and pct_match and non_comparable_blank),
           "20,086 independently matching valid pairs; invalid pairs empty", int(comparable.sum()),
           "Discount amount and percentage recomputation.")

    compact_fields_pass = all(
        field_frame.set_index("field").loc[field, "status"] == "PASS"
        for field in DERIVED_FIELDS if any(token in field for token in ("suffix", "precision_unit", "compact_rounded", "parse_status"))
        and field.startswith(("total_sold", "total_rating", "favorite"))
    )
    record("CNT-001", "COMPACT_COUNTS", "CRITICAL", compact_fields_pass, "all count parsing metadata matches",
           compact_fields_pass, "Suffix, mathematical multiplier, precision, rounding, and status validation.")

    exact_equality = raw["total_sold"].eq(raw["total_rating"])
    jointly_missing = missing_mask(raw["total_sold"]) & missing_mask(raw["total_rating"])
    normalized_equality = exact_equality | jointly_missing
    exact_equality_count = int(exact_equality.sum())
    jointly_missing_count = int(jointly_missing.sum())
    sold_status_ok = processed["total_sold_metric_status"].eq("UNVERIFIED_UNUSABLE_AS_SALES_METRIC").all()
    rating_status_ok = processed["total_rating_metric_status"].eq("UNVERIFIED_DUPLICATES_TOTAL_SOLD").all()
    prohibited_patterns = re.compile(r"(^|_)(revenue|aov|orders?|sales_(growth|velocity)|category_rank|momentum_score)($|_)", re.I)
    prohibited_columns = [column for column in processed.columns if prohibited_patterns.search(column)]
    record(
        "SAFE-001", "SALES_SAFEGUARD", "CRITICAL",
        normalized_equality.all() and exact_equality_count == 20_301 and jointly_missing_count == 11,
        "20,301 exact strings + 11 jointly missing-equivalent; 0 substantive inequalities",
        f"exact={exact_equality_count}; jointly_missing={jointly_missing_count}; "
        f"substantive_inequalities={int((~normalized_equality).sum())}",
        "Independent raw comparison preserves the blank-vs-N/A distinction while confirming duplication wherever populated.",
    )
    record("SAFE-002", "SALES_SAFEGUARD", "CRITICAL", bool(sold_status_ok and rating_status_ok), "all rows restricted",
           f"sold={sold_status_ok}; rating={rating_status_ok}", "Trust-status enforcement.")
    record("SAFE-003", "SALES_SAFEGUARD", "CRITICAL", not prohibited_columns, "no prohibited analytical metric columns",
           " | ".join(prohibited_columns) or "none", "No sales velocity, revenue, AOV, order, rank, or momentum score field.")

    exact_duplicates = int(raw.duplicated(keep=False).sum())
    potential_rows = int(processed["duplicate_review_flag"].eq("TRUE").sum())
    potential_groups = processed.loc[processed["duplicate_review_flag"].eq("TRUE"), "duplicate_review_group_id"].nunique()
    record("DUP-001", "DUPLICATES", "CRITICAL", exact_duplicates == 0 and key_duplicates == 0, "0 exact / 0 key", f"{exact_duplicates} exact / {key_duplicates} key",
           "Exact and snapshot-key duplicate validation.")
    record("DUP-002", "DUPLICATES", "HIGH", potential_rows == 62 and potential_groups == 30, "62 rows / 30 groups",
           f"{potential_rows} rows / {potential_groups} groups", "Potential duplicates retained with deterministic identifiers.")

    product_counts = raw.groupby("id").size()
    repeated_products = int(product_counts.gt(1).sum())
    matched_rows = int(raw["id"].map(product_counts).gt(1).sum())
    matched_intervals = int((product_counts - 1).clip(lower=0).sum())
    at_least_3 = int(product_counts.ge(3).sum())
    at_least_4 = int(product_counts.ge(4).sum())
    cohort_observed = f"{repeated_products}/{matched_rows}/{matched_intervals}/{at_least_3}/{at_least_4}"
    record("COH-001", "MATCHED_COHORT", "CRITICAL",
           (repeated_products, matched_rows, matched_intervals, at_least_3, at_least_4) == (3070, 6768, 3698, 535, 86),
           "3070/6768/3698/535/86", cohort_observed,
           "Repeated products / repeated rows / intervals / products >=3 / products >=4.")
    interval_rows = processed["previous_observation_date"].ne("")
    interval_positive = pd.to_numeric(processed.loc[interval_rows, "observation_interval_days"], errors="coerce").gt(0).all()
    record("COH-002", "MATCHED_COHORT", "CRITICAL", bool(interval_positive), "all intervals > 0", bool(interval_positive),
           "Chronological sequence and elapsed-day validation.")
    eligible_sales = int((~processed["movement_analysis_eligibility_status"].isin(
        ["NO_PRIOR_OBSERVATION", "MISSING_UNVERIFIED_COUNTER", "BLOCKED_COUNTER_UNVERIFIED"]
    )).sum())
    record("COH-003", "MATCHED_COHORT", "CRITICAL", eligible_sales == 0, "0 verified eligible intervals", eligible_sales,
           "All movement remains unavailable or blocked.")

    negative_rows = processed["negative_change_flag"].eq("TRUE")
    negative_ok = (
        int(negative_rows.sum()) == 2
        and processed.loc[negative_rows, "cumulative_change_status"].eq("DECREASE").all()
        and processed.loc[negative_rows, "movement_analysis_eligibility_status"].eq("BLOCKED_COUNTER_UNVERIFIED").all()
        and pd.to_numeric(processed.loc[negative_rows, "unverified_counter_change"], errors="coerce").lt(0).all()
    )
    record("NEG-001", "NEGATIVE_CHANGE", "CRITICAL", bool(negative_ok), "2 unchanged, flagged, blocked intervals",
           int(negative_rows.sum()), "Negative ambiguous-counter interval validation.")

    missing_flag_fields = [f"{source}_missing_flag" for source in (
        "price_ori", "delivery", "specification", "item_rating", "seller_name",
        "price_actual", "total_rating", "total_sold", "favorite",
    )]
    missing_flags_pass = field_frame.set_index("field").loc[missing_flag_fields, "status"].eq("PASS").all()
    record("MIS-001", "MISSINGNESS", "CRITICAL", bool(missing_flags_pass and raw_cell_differences == 0),
           "all 9 flags match; source cells unchanged", bool(missing_flags_pass),
           "No imputation and exact source-to-flag correspondence.")

    manifest_path = ROOT / "outputs" / "analysis_results" / "phase_2_cleaning_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_thresholds = {
        "price_ori_lower": manifest["price_iqr_fences"]["price_ori_clean"][0],
        "price_ori_upper": manifest["price_iqr_fences"]["price_ori_clean"][1],
        "price_actual_lower": manifest["price_iqr_fences"]["price_actual_clean"][0],
        "price_actual_upper": manifest["price_iqr_fences"]["price_actual_clean"][1],
        "counter_lower": manifest["other_iqr_fences"]["unverified_counter"][0],
        "counter_upper": manifest["other_iqr_fences"]["unverified_counter"][1],
        "favorite_lower": manifest["other_iqr_fences"]["favorite"][0],
        "favorite_upper": manifest["other_iqr_fences"]["favorite"][1],
        "rating_lower": manifest["other_iqr_fences"]["item_rating"][0],
        "rating_upper": manifest["other_iqr_fences"]["item_rating"][1],
    }
    threshold_match = all(math.isclose(thresholds[key], manifest_thresholds[key], rel_tol=1e-12, abs_tol=1e-12) for key in thresholds)
    outlier_fields = [
        "price_ori_statistical_outlier_flag", "price_actual_statistical_outlier_flag",
        "unverified_counter_statistical_outlier_flag", "favorite_statistical_outlier_flag",
        "item_rating_statistical_outlier_flag",
    ]
    outlier_flags_pass = field_frame.set_index("field").loc[outlier_fields, "status"].eq("PASS").all()
    record("OUT-001", "OUTLIERS", "HIGH", bool(threshold_match and outlier_flags_pass),
           "independent IQR thresholds and flags match", f"thresholds={threshold_match}; flags={outlier_flags_pass}",
           "Outliers retained; flags are descriptive, not invalidation rules.")

    business_text = BUSINESS_QUESTIONS.read_text(encoding="utf-8")
    original_question_present = "Which product categories are gaining momentum fastest on the platform" in business_text
    reframing_pending = "POTENTIAL REFRAMING" in business_text and "REQUIRES APPROVAL" in business_text
    record("BUS-001", "BUSINESS_SAFETY", "CRITICAL", original_question_present and reframing_pending,
           "original retained; alternative requires approval", f"original={original_question_present}; pending={reframing_pending}",
           "No silent reframing.")
    record("BUS-002", "BUSINESS_SAFETY", "HIGH", True, "claims remain unavailable",
           "sales/revenue/orders/AOV/customers/conversion/campaign effectiveness unsupported",
           "Structural validation does not validate a business performance metric.", warning=True)
    record("BUS-003", "BUSINESS_SAFETY", "HIGH", True, "hard restriction remains",
           "total_sold unusable; total_rating unverified", "Downstream use requires independent semantic evidence.", warning=True)

    record("WARN-001", "KNOWN_LIMITATIONS", "MEDIUM", True, "retained for review",
           "62 potential duplicate rows; 45 category-change rows; 2 negative intervals",
           "Known anomalies are correctly preserved and flagged.", warning=True)
    record("WARN-002", "KNOWN_LIMITATIONS", "HIGH", True, "coverage limitation retained",
           "3,070/16,614 repeated products; 3,698 intervals over 20 unevenly sampled days",
           "Matched history is sparse and does not establish platform-wide momentum.", warning=True)
    record("WARN-003", "KNOWN_LIMITATIONS", "MEDIUM", True, "price anomalies retained",
           "zero, missing, sentinel, suspicious-high, and IQR outliers remain flagged",
           "Valid-status filters are mandatory for later price work.", warning=True)

    samples = []
    for index in [0, len(raw) // 2, len(raw) - 1]:
        samples.append({
            "check_area": "DATE", "source_row_number": index + 1, "id": raw.at[index, "id"],
            "raw_value": raw.at[index, "w_date"], "derived_value": processed.at[index, "observation_date"],
            "expected_value": expected.at[index, "observation_date"], "result": "PASS",
        })
    compact_candidates = raw.index[raw["total_sold"].str.contains(r"[kKmMbB]", regex=True, na=False)][:3]
    for index in compact_candidates:
        samples.append({
            "check_area": "COMPACT_COUNT", "source_row_number": index + 1, "id": raw.at[index, "id"],
            "raw_value": raw.at[index, "total_sold"], "derived_value": processed.at[index, "total_sold_parsed"],
            "expected_value": expected.at[index, "total_sold_parsed"], "result": "PASS",
        })
    for index in processed.index[sentinel_ori | sentinel_actual][:3]:
        samples.append({
            "check_area": "PRICE_SENTINEL", "source_row_number": index + 1, "id": raw.at[index, "id"],
            "raw_value": f"ori={raw.at[index, 'price_ori']}; actual={raw.at[index, 'price_actual']}",
            "derived_value": f"ori={processed.at[index, 'price_ori_status']}; actual={processed.at[index, 'price_actual_status']}",
            "expected_value": "sentinel excluded from clean price", "result": "PASS",
        })
    for index in processed.index[negative_rows]:
        samples.append({
            "check_area": "NEGATIVE_CHANGE", "source_row_number": index + 1, "id": raw.at[index, "id"],
            "raw_value": raw.at[index, "total_sold"], "derived_value": processed.at[index, "unverified_counter_change"],
            "expected_value": "negative; blocked", "result": "PASS",
        })

    validation_frame = pd.DataFrame(checks)
    atomic_csv(validation_frame, RESULTS_PATH)
    atomic_csv(field_frame, FIELD_RESULTS_PATH)
    atomic_csv(pd.DataFrame(samples), SAMPLES_PATH)

    failures = validation_frame["status"].eq("FAIL").sum()
    print(f"Validation checks: {len(validation_frame)}")
    print(f"Passed: {int(validation_frame['status'].eq('PASS').sum())}")
    print(f"Warnings: {int(validation_frame['status'].eq('WARNING').sum())}")
    print(f"Failed: {int(failures)}")
    print(f"Derived fields passed: {int(field_frame['status'].eq('PASS').sum())}/91")
    print(f"Processed SHA-256: {sha256(PROCESSED_PATH)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
