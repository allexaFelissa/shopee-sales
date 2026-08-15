"""Deterministic, non-destructive Phase 2 cleaning pipeline.

All 20 raw columns are preserved as source text. Cleaning adds parsed values,
quality flags, category levels, observation/cohort metadata, and audit outputs.
The duplicated total_sold field is never promoted to a verified sales metric.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_RAW_SHA256 = "afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69"
SOURCE_CANDIDATES = (
    ROOT / "data" / "raw" / "shopee_sales_data.csv",
    ROOT / "dataset" / "shopee_sales_data.csv",
)
OUTPUT_PATH = ROOT / "data" / "processed" / "shopee_sales_cleaned.csv"
TABLE_DIR = ROOT / "outputs" / "tables"
REPORT_DIR = ROOT / "reports"
MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_2_cleaning_manifest.json"
SENTINEL_PRICE = 999_999_999.0
SUSPICIOUS_HIGH_PRICE = 1_000_000.0
MISSING_TEXT_TOKENS = {
    "",
    "n/a",
    "na",
    "nan",
    "none",
    "null",
    "<na>",
    "#n/a",
    "#na",
    "#n/a n/a",
    "-nan",
    "-1.#ind",
    "-1.#qnan",
    "1.#ind",
    "1.#qnan",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_source() -> Path:
    existing = [path for path in SOURCE_CANDIDATES if path.is_file()]
    if len(existing) != 1:
        raise RuntimeError(f"Expected exactly one raw source, found: {existing}")
    return existing[0]


def blank_to_na(series: pd.Series) -> pd.Series:
    text = series.astype("string")
    normalized = text.str.strip().str.casefold()
    return text.mask(normalized.isin(MISSING_TEXT_TOKENS), pd.NA)


def parse_compact(value: Any, extract_from_label: bool = False) -> tuple[Any, str, Any, bool, str]:
    """Return numeric value, suffix, precision unit, rounded flag, parse status."""
    if value is None or pd.isna(value) or str(value).strip() == "":
        return pd.NA, "", pd.NA, False, "MISSING"
    raw = str(value).strip()
    candidate = raw
    if extract_from_label:
        found = re.search(r"([0-9]+(?:\.[0-9]+)?\s*[kKmMbB]?)", raw)
        if not found:
            return pd.NA, "", pd.NA, False, "INVALID_LABEL"
        candidate = found.group(1)
    candidate = candidate.lower().replace(",", "").strip()
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([kmb]?)", candidate)
    if not match:
        return pd.NA, "", pd.NA, False, "INVALID_FORMAT"
    number_text, suffix = match.groups()
    multiplier = {"": 1.0, "k": 1_000.0, "m": 1_000_000.0, "b": 1_000_000_000.0}[suffix]
    value_numeric = float(number_text) * multiplier
    decimals = len(number_text.split(".", 1)[1]) if "." in number_text else 0
    precision_unit = multiplier / (10**decimals)
    rounded = suffix != ""
    status = "PARSED_COMPACT_ROUNDED" if rounded else "PARSED_EXACT_DISPLAY"
    return value_numeric, suffix, precision_unit, rounded, status


def parsed_count_frame(series: pd.Series, extract_from_label: bool = False) -> pd.DataFrame:
    values = [parse_compact(value, extract_from_label=extract_from_label) for value in series]
    return pd.DataFrame(
        values,
        columns=["parsed", "suffix", "precision_unit", "compact_rounded_flag", "parse_status"],
        index=series.index,
    )


def price_status(raw: pd.Series) -> tuple[pd.Series, pd.Series]:
    normalized = blank_to_na(raw)
    numeric = pd.to_numeric(normalized, errors="coerce")
    status = pd.Series("VALID", index=raw.index, dtype="string")
    status.loc[normalized.isna()] = "MISSING"
    status.loc[normalized.notna() & numeric.isna()] = "INVALID_FORMAT"
    status.loc[numeric.eq(0)] = "ZERO"
    status.loc[numeric.eq(SENTINEL_PRICE)] = "SENTINEL_999999999"
    status.loc[numeric.ge(SUSPICIOUS_HIGH_PRICE) & ~numeric.eq(SENTINEL_PRICE)] = "SUSPICIOUS_HIGH_GE_1000000"
    cleaned = numeric.where(status.eq("VALID"))
    return cleaned, status


def iqr_outlier_flag(series: pd.Series) -> tuple[pd.Series, float, float]:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    numeric = pd.to_numeric(series, errors="coerce")
    return ((numeric < lower) | (numeric > upper)).fillna(False), lower, upper


def boolean_text(series: pd.Series) -> pd.Series:
    return series.fillna(False).map({True: "TRUE", False: "FALSE"}).astype("string")


def safe_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return "<MISSING>"
    return str(value)


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, encoding="utf-8", lineterminator="\n", float_format="%.10g")
    temporary.replace(path)


def main() -> None:
    source = find_source()
    raw_hash_before = sha256(source)
    if raw_hash_before != EXPECTED_RAW_SHA256:
        raise RuntimeError(f"Raw SHA-256 mismatch: {raw_hash_before}")

    # keep_default_na=False preserves every raw cell's original text representation.
    raw = pd.read_csv(source, dtype=str, keep_default_na=False, low_memory=False)
    raw_columns = list(raw.columns)
    if len(raw) != 20_312 or len(raw_columns) != 20:
        raise RuntimeError(f"Unexpected source shape: {raw.shape}")
    cleaned = raw.copy()
    cleaned.insert(0, "source_row_number", np.arange(1, len(cleaned) + 1, dtype=np.int64))

    # Missingness flags preserve missing cells; no imputation occurs.
    for column in (
        "price_ori",
        "delivery",
        "specification",
        "item_rating",
        "seller_name",
        "price_actual",
        "total_rating",
        "total_sold",
        "favorite",
    ):
        cleaned[f"{column}_missing_flag"] = boolean_text(blank_to_na(raw[column]).isna())

    # Dates: preserve w_date/timestamp; add only useful analytical fields.
    raw_date = blank_to_na(raw["w_date"])
    observation_date = pd.to_datetime(raw_date, format="%Y-%m-%d", errors="coerce")
    timestamp_numeric = pd.to_numeric(blank_to_na(raw["timestamp"]), errors="coerce")
    timestamp_date = pd.to_datetime(timestamp_numeric, unit="ms", errors="coerce")
    cleaned["observation_date"] = observation_date.dt.strftime("%Y-%m-%d").fillna("")
    cleaned["observation_week_start"] = (
        observation_date - pd.to_timedelta(observation_date.dt.weekday, unit="D")
    ).dt.strftime("%Y-%m-%d").fillna("")
    cleaned["observation_month"] = observation_date.dt.strftime("%Y-%m").fillna("")
    cleaned["observation_day_of_week"] = observation_date.dt.day_name().fillna("")
    cleaned["date_parse_status"] = np.select(
        [raw_date.isna(), observation_date.isna()], ["MISSING", "INVALID"], default="VALID"
    )
    cleaned["timestamp_date_match_flag"] = boolean_text(
        observation_date.notna()
        & timestamp_date.notna()
        & observation_date.dt.date.eq(timestamp_date.dt.date)
    )

    # Category hierarchy: only trim path components; never reassign a product.
    raw_category = blank_to_na(raw["item_category_detail"])
    parts = raw_category.str.split("|", regex=False)
    part_count = parts.map(lambda value: len(value) if isinstance(value, list) else 0)
    for level in range(1, 5):
        cleaned[f"category_level_{level}"] = parts.str[level - 1].str.strip().fillna("")
    cleaned["category_path_clean"] = parts.map(
        lambda values: " | ".join(part.strip() for part in values)
        if isinstance(values, list)
        else ""
    )
    cleaned["category_path_parse_status"] = np.select(
        [raw_category.isna(), part_count.eq(3), part_count.eq(4)],
        ["MISSING", "VALID_3_LEVEL", "VALID_4_LEVEL"],
        default="MALFORMED_LEVEL_COUNT",
    )
    cleaned["primary_category_grain"] = "LEVEL_2"

    # Count-like fields: preserve raw text plus approximate numeric, suffix, precision, and status.
    for source_column in ("total_sold", "total_rating"):
        parsed = parsed_count_frame(blank_to_na(raw[source_column]))
        cleaned[f"{source_column}_parsed"] = parsed["parsed"]
        cleaned[f"{source_column}_suffix"] = parsed["suffix"]
        cleaned[f"{source_column}_precision_unit"] = parsed["precision_unit"]
        cleaned[f"{source_column}_compact_rounded_flag"] = boolean_text(parsed["compact_rounded_flag"])
        cleaned[f"{source_column}_parse_status"] = parsed["parse_status"]
    favorite_parsed = parsed_count_frame(blank_to_na(raw["favorite"]), extract_from_label=True)
    cleaned["favorite_parsed"] = favorite_parsed["parsed"]
    cleaned["favorite_suffix"] = favorite_parsed["suffix"]
    cleaned["favorite_precision_unit"] = favorite_parsed["precision_unit"]
    cleaned["favorite_compact_rounded_flag"] = boolean_text(favorite_parsed["compact_rounded_flag"])
    cleaned["favorite_parse_status"] = favorite_parsed["parse_status"]
    sold_rating_match = raw["total_sold"].eq(raw["total_rating"])
    cleaned["sold_rating_exact_match_flag"] = boolean_text(sold_rating_match)
    cleaned["total_sold_metric_status"] = "UNVERIFIED_UNUSABLE_AS_SALES_METRIC"
    cleaned["total_rating_metric_status"] = "UNVERIFIED_DUPLICATES_TOTAL_SOLD"

    # Average rating: distinguish missing, unrated label, valid number, and invalid label.
    rating_raw = blank_to_na(raw["item_rating"])
    rating_numeric = pd.to_numeric(rating_raw, errors="coerce")
    rating_status = pd.Series("VALID", index=raw.index, dtype="string")
    rating_status.loc[rating_raw.isna()] = "MISSING"
    rating_status.loc[rating_raw.str.casefold().eq("no ratings yet").fillna(False)] = "NO_RATINGS_YET"
    rating_status.loc[rating_raw.notna() & rating_numeric.isna() & ~rating_status.eq("NO_RATINGS_YET")] = "INVALID_LABEL"
    rating_status.loc[rating_numeric.notna() & ~rating_numeric.between(1, 5)] = "OUT_OF_RANGE"
    cleaned["item_rating_numeric"] = rating_numeric.where(rating_status.eq("VALID"))
    cleaned["item_rating_status"] = rating_status

    # Prices: raw text remains in original columns; cleaned values exclude explicit invalid states.
    price_ori_clean, price_ori_status = price_status(raw["price_ori"])
    price_actual_clean, price_actual_status = price_status(raw["price_actual"])
    cleaned["price_ori_clean"] = price_ori_clean
    cleaned["price_ori_status"] = price_ori_status
    cleaned["price_actual_clean"] = price_actual_clean
    cleaned["price_actual_status"] = price_actual_status
    ori_outlier, ori_lower, ori_upper = iqr_outlier_flag(price_ori_clean)
    actual_outlier, actual_lower, actual_upper = iqr_outlier_flag(price_actual_clean)
    cleaned["price_ori_statistical_outlier_flag"] = boolean_text(ori_outlier)
    cleaned["price_actual_statistical_outlier_flag"] = boolean_text(actual_outlier)
    price_pair_valid = price_ori_status.eq("VALID") & price_actual_status.eq("VALID")
    cleaned["price_pair_status"] = np.select(
        [
            ~price_pair_valid,
            price_pair_valid & price_actual_clean.gt(price_ori_clean),
            price_pair_valid & price_actual_clean.le(price_ori_clean),
        ],
        ["INVALID_COMPONENT", "ACTUAL_ABOVE_ORIGINAL", "VALID_COMPARABLE"],
        default="UNCLASSIFIED",
    )
    comparable = cleaned["price_pair_status"].eq("VALID_COMPARABLE")
    cleaned["discount_amount"] = (price_ori_clean - price_actual_clean).where(comparable)
    cleaned["discount_pct"] = ((price_ori_clean - price_actual_clean) / price_ori_clean * 100).where(comparable)
    cleaned["price_currency_status"] = "UNVERIFIED_CONTEXT_SUGGESTS_MYR"

    # Duplicate flags: preserve all rows; potential groups require record-level review.
    exact_duplicate = raw.duplicated(keep=False)
    key_duplicate = raw.duplicated(["id", "w_date"], keep=False)
    cleaned["exact_duplicate_flag"] = boolean_text(exact_duplicate)
    cleaned["snapshot_key_duplicate_flag"] = boolean_text(key_duplicate)
    duplicate_key_frame = pd.DataFrame(
        {
            "seller_name": blank_to_na(raw["seller_name"]),
            "title": blank_to_na(raw["title"]),
            "w_date": blank_to_na(raw["w_date"]),
            "id": blank_to_na(raw["id"]),
            "link_ori": blank_to_na(raw["link_ori"]),
        }
    )
    duplicate_groups = (
        duplicate_key_frame.groupby(["seller_name", "title", "w_date"], dropna=False)
        .agg(rows=("id", "size"), distinct_ids=("id", "nunique"), distinct_links=("link_ori", "nunique"))
        .reset_index()
    )
    duplicate_groups = duplicate_groups[
        duplicate_groups["rows"].gt(1) & duplicate_groups["distinct_ids"].gt(1)
    ].copy()
    duplicate_groups["duplicate_review_group_id"] = duplicate_groups.apply(
        lambda row: "DUP-"
        + hashlib.sha256(
            "|".join(safe_text(row[column]) for column in ("seller_name", "title", "w_date")).encode("utf-8")
        ).hexdigest()[:12],
        axis=1,
    )
    duplicate_map = duplicate_groups.set_index(["seller_name", "title", "w_date"])["duplicate_review_group_id"]
    row_duplicate_index = pd.MultiIndex.from_frame(duplicate_key_frame[["seller_name", "title", "w_date"]])
    cleaned["duplicate_review_group_id"] = duplicate_map.reindex(row_duplicate_index).to_numpy()
    cleaned["duplicate_review_group_id"] = cleaned["duplicate_review_group_id"].fillna("")
    cleaned["duplicate_review_flag"] = boolean_text(cleaned["duplicate_review_group_id"].ne(""))

    # Product-level cohort and category stability fields.
    work = pd.DataFrame(
        {
            "source_row_number": cleaned["source_row_number"],
            "id": blank_to_na(raw["id"]),
            "observation_date": observation_date,
            "category_path": cleaned["category_path_clean"].replace("", pd.NA),
            "category_level_2": cleaned["category_level_2"].replace("", pd.NA),
            "unverified_counter": pd.to_numeric(cleaned["total_sold_parsed"], errors="coerce"),
        }
    ).sort_values(["id", "observation_date", "source_row_number"])
    product_group = work.groupby("id", dropna=False)
    work["product_observation_count"] = product_group["source_row_number"].transform("size")
    work["product_first_observation_date"] = product_group["observation_date"].transform("min")
    work["product_last_observation_date"] = product_group["observation_date"].transform("max")
    work["product_observation_span_days"] = (
        work["product_last_observation_date"] - work["product_first_observation_date"]
    ).dt.days
    work["observation_sequence"] = product_group.cumcount() + 1
    work["previous_observation_date"] = product_group["observation_date"].shift()
    work["observation_interval_days"] = (
        work["observation_date"] - work["previous_observation_date"]
    ).dt.days
    work["previous_unverified_counter"] = product_group["unverified_counter"].shift()
    work["unverified_counter_change"] = work["unverified_counter"] - work["previous_unverified_counter"]
    work["product_category_path_count"] = product_group["category_path"].transform("nunique")
    work["product_category_level2_count"] = product_group["category_level_2"].transform("nunique")
    work["previous_category_path"] = product_group["category_path"].shift()
    work["previous_category_level_2"] = product_group["category_level_2"].shift()
    work["category_changed_from_previous_flag"] = (
        work["previous_category_path"].notna()
        & work["category_path"].notna()
        & work["category_path"].ne(work["previous_category_path"])
    )
    work["category_level2_changed_from_previous_flag"] = (
        work["previous_category_level_2"].notna()
        & work["category_level_2"].notna()
        & work["category_level_2"].ne(work["previous_category_level_2"])
    )
    work = work.sort_values("source_row_number").reset_index(drop=True)
    cleaned["product_observation_count"] = work["product_observation_count"]
    cleaned["product_first_observation_date"] = work["product_first_observation_date"].dt.strftime("%Y-%m-%d").fillna("")
    cleaned["product_last_observation_date"] = work["product_last_observation_date"].dt.strftime("%Y-%m-%d").fillna("")
    cleaned["product_observation_span_days"] = work["product_observation_span_days"]
    cleaned["matched_product_flag"] = boolean_text(work["product_observation_count"].gt(1))
    cleaned["observation_sequence"] = work["observation_sequence"]
    cleaned["previous_observation_date"] = work["previous_observation_date"].dt.strftime("%Y-%m-%d").fillna("")
    cleaned["observation_interval_days"] = work["observation_interval_days"]
    cleaned["unverified_counter_previous"] = work["previous_unverified_counter"]
    cleaned["unverified_counter_change"] = work["unverified_counter_change"]
    cleaned["negative_change_flag"] = boolean_text(work["unverified_counter_change"].lt(0))
    cleaned["cumulative_change_status"] = np.select(
        [
            work["previous_observation_date"].isna(),
            work["previous_unverified_counter"].isna() | work["unverified_counter"].isna(),
            work["unverified_counter_change"].lt(0),
            work["unverified_counter_change"].eq(0),
            work["unverified_counter_change"].gt(0),
        ],
        ["FIRST_OBSERVATION", "MISSING_UNVERIFIED_COUNTER", "DECREASE", "NO_CHANGE", "INCREASE"],
        default="UNCLASSIFIED",
    )
    cleaned["movement_analysis_eligibility_status"] = np.select(
        [
            work["previous_observation_date"].isna(),
            work["previous_unverified_counter"].isna() | work["unverified_counter"].isna(),
        ],
        ["NO_PRIOR_OBSERVATION", "MISSING_UNVERIFIED_COUNTER"],
        default="BLOCKED_COUNTER_UNVERIFIED",
    )
    cleaned["acceleration_structure_flag"] = boolean_text(work["product_observation_count"].ge(3))
    cleaned["product_category_change_flag"] = boolean_text(work["product_category_path_count"].gt(1))
    cleaned["product_category_level2_change_flag"] = boolean_text(work["product_category_level2_count"].gt(1))
    cleaned["product_category_path_count"] = work["product_category_path_count"]
    cleaned["product_category_level2_count"] = work["product_category_level2_count"]
    cleaned["previous_category_path"] = work["previous_category_path"].fillna("")
    cleaned["previous_category_level_2"] = work["previous_category_level_2"].fillna("")
    cleaned["category_changed_from_previous_flag"] = boolean_text(work["category_changed_from_previous_flag"])
    cleaned["category_level2_changed_from_previous_flag"] = boolean_text(
        work["category_level2_changed_from_previous_flag"]
    )

    # Coverage fields expose observed sampling; they do not weight or duplicate rows.
    date_key = cleaned["observation_date"].replace("", pd.NA)
    category_key = cleaned["category_level_2"].replace("", pd.NA)
    seller_key = blank_to_na(raw["seller_name"])
    id_key = blank_to_na(raw["id"])
    coverage_frame = pd.DataFrame(
        {"date": date_key, "category": category_key, "seller": seller_key, "id": id_key}
    )
    cleaned["daily_observation_count"] = coverage_frame.groupby("date", dropna=False)["id"].transform("size")
    cleaned["daily_unique_product_count"] = coverage_frame.groupby("date", dropna=False)["id"].transform("nunique")
    cleaned["daily_category_level2_count"] = coverage_frame.groupby("date", dropna=False)["category"].transform("nunique")
    cleaned["daily_seller_count"] = coverage_frame.groupby("date", dropna=False)["seller"].transform("nunique")
    cleaned["category_date_observation_count"] = coverage_frame.groupby(
        ["category", "date"], dropna=False
    )["id"].transform("size")
    cleaned["category_date_unique_product_count"] = coverage_frame.groupby(
        ["category", "date"], dropna=False
    )["id"].transform("nunique")
    cleaned["category_total_observation_count"] = coverage_frame.groupby("category", dropna=False)["id"].transform("size")
    cleaned["category_unique_product_count"] = coverage_frame.groupby("category", dropna=False)["id"].transform("nunique")
    repeated_id_set = set(work.loc[work["product_observation_count"].gt(1), "id"].dropna())
    repeated_by_category = (
        coverage_frame.assign(repeated=coverage_frame["id"].isin(repeated_id_set))
        .loc[lambda frame: frame["repeated"]]
        .groupby("category", dropna=False)["id"]
        .nunique()
    )
    cleaned["category_repeated_product_count"] = category_key.map(repeated_by_category).fillna(0).astype(int)

    # Statistical flags are descriptive and do not remove observations.
    sold_outlier, sold_lower, sold_upper = iqr_outlier_flag(cleaned["total_sold_parsed"])
    favorite_outlier, favorite_lower, favorite_upper = iqr_outlier_flag(cleaned["favorite_parsed"])
    rating_outlier, rating_lower, rating_upper = iqr_outlier_flag(cleaned["item_rating_numeric"])
    cleaned["unverified_counter_statistical_outlier_flag"] = boolean_text(sold_outlier)
    cleaned["favorite_statistical_outlier_flag"] = boolean_text(favorite_outlier)
    cleaned["item_rating_statistical_outlier_flag"] = boolean_text(rating_outlier)

    # Hard integrity assertions before writing any processed artifact.
    if len(cleaned) != len(raw):
        raise RuntimeError("Row count changed during cleaning")
    if cleaned[raw_columns].astype(str).ne(raw.astype(str)).any().any():
        raise RuntimeError("A preserved raw cell changed during cleaning")
    if cleaned.duplicated(["id", "w_date"]).any():
        raise RuntimeError("Processed snapshot key is unexpectedly duplicated")
    if not cleaned["total_sold_metric_status"].eq("UNVERIFIED_UNUSABLE_AS_SALES_METRIC").all():
        raise RuntimeError("Sales safeguard status is incomplete")

    # Required audit tables.
    missing_rows = []
    for column in raw_columns:
        missing = int(blank_to_na(raw[column]).isna().sum())
        missing_rows.append(
            {
                "field": column,
                "raw_missing_count": missing,
                "raw_missing_pct": round(missing / len(raw) * 100, 6),
                "treatment": "PRESERVED_NOT_IMPUTED",
                "processed_missing_flag": f"{column}_missing_flag"
                if f"{column}_missing_flag" in cleaned.columns
                else "NOT_CREATED_NOT_ANALYTICALLY_CRITICAL",
            }
        )
    missing_summary = pd.DataFrame(missing_rows)

    anomaly_summary = pd.DataFrame(
        [
            ("RAW_EXACT_DUPLICATE", int(exact_duplicate.sum()), "Retained; none found"),
            ("SNAPSHOT_KEY_DUPLICATE", int(key_duplicate.sum()), "Retained; none found"),
            ("POTENTIAL_DUPLICATE_REVIEW_ROW", int(cleaned["duplicate_review_flag"].eq("TRUE").sum()), "Retained and grouped"),
            ("PRODUCT_CATEGORY_PATH_CHANGE_ROW", int(cleaned["product_category_change_flag"].eq("TRUE").sum()), "Retained and flagged"),
            ("PRODUCT_LEVEL2_CATEGORY_CHANGE_ROW", int(cleaned["product_category_level2_change_flag"].eq("TRUE").sum()), "Retained and flagged"),
            ("NEGATIVE_UNVERIFIED_COUNTER_CHANGE", int(cleaned["negative_change_flag"].eq("TRUE").sum()), "Retained; no correction"),
            ("PRICE_ORI_MISSING", int(price_ori_status.eq("MISSING").sum()), "Raw retained; clean value missing"),
            ("PRICE_ORI_ZERO", int(price_ori_status.eq("ZERO").sum()), "Raw retained; clean value missing"),
            ("PRICE_ORI_SENTINEL", int(price_ori_status.eq("SENTINEL_999999999").sum()), "Raw retained; clean value missing"),
            ("PRICE_ORI_SUSPICIOUS_HIGH", int(price_ori_status.eq("SUSPICIOUS_HIGH_GE_1000000").sum()), "Raw retained; clean value missing"),
            ("PRICE_ACTUAL_MISSING", int(price_actual_status.eq("MISSING").sum()), "Raw retained; clean value missing"),
            ("PRICE_ACTUAL_ZERO", int(price_actual_status.eq("ZERO").sum()), "Raw retained; clean value missing"),
            ("PRICE_ACTUAL_SENTINEL", int(price_actual_status.eq("SENTINEL_999999999").sum()), "Raw retained; clean value missing"),
            ("PRICE_ACTUAL_SUSPICIOUS_HIGH", int(price_actual_status.eq("SUSPICIOUS_HIGH_GE_1000000").sum()), "Raw retained; clean value missing"),
            ("PRICE_ORI_STATISTICAL_OUTLIER", int(ori_outlier.sum()), "Retained; descriptive flag only"),
            ("PRICE_ACTUAL_STATISTICAL_OUTLIER", int(actual_outlier.sum()), "Retained; descriptive flag only"),
            ("FAVORITE_INVALID_LABEL", int(favorite_parsed["parse_status"].eq("INVALID_LABEL").sum()), "Raw retained; parsed value missing"),
            ("TOTAL_SOLD_UNUSABLE_STATUS", len(cleaned), "Preserved but excluded from sales metrics"),
            ("TOTAL_RATING_UNVERIFIED_STATUS", len(cleaned), "Preserved but not independently trusted"),
        ],
        columns=["anomaly", "affected_rows", "treatment"],
    )

    category_change_summary = (
        cleaned.loc[cleaned["product_category_change_flag"].eq("TRUE")]
        .groupby("id", dropna=False)
        .agg(
            observation_count=("source_row_number", "size"),
            first_date=("observation_date", "min"),
            last_date=("observation_date", "max"),
            category_path_count=("product_category_path_count", "max"),
            level2_category_count=("product_category_level2_count", "max"),
            observed_level2_categories=("category_level_2", lambda values: " || ".join(dict.fromkeys(values))),
            observed_category_paths=("category_path_clean", lambda values: " || ".join(dict.fromkeys(values))),
        )
        .reset_index()
    )
    duplicate_review_summary = duplicate_groups[
        ["duplicate_review_group_id", "seller_name", "title", "w_date", "rows", "distinct_ids", "distinct_links"]
    ].sort_values("duplicate_review_group_id")
    matched_product_summary = pd.DataFrame(
        [
            ("unique_products", int(work["id"].nunique())),
            ("products_observed_once", int(work.loc[work["product_observation_count"].eq(1), "id"].nunique())),
            ("matched_products", int(work.loc[work["product_observation_count"].gt(1), "id"].nunique())),
            ("products_with_at_least_3_observations", int(work.loc[work["product_observation_count"].ge(3), "id"].nunique())),
            ("products_with_at_least_4_observations", int(work.loc[work["product_observation_count"].ge(4), "id"].nunique())),
            ("matched_intervals", int(work["previous_observation_date"].notna().sum())),
            ("positive_unverified_counter_intervals", int(work["unverified_counter_change"].gt(0).sum())),
            ("zero_unverified_counter_intervals", int(work["unverified_counter_change"].eq(0).sum())),
            ("negative_unverified_counter_intervals", int(work["unverified_counter_change"].lt(0).sum())),
            ("movement_eligible_with_verified_sales_metric", 0),
        ],
        columns=["metric", "value"],
    )

    transformation_rows = [
        (1, "SOURCE_PROTECTION", "Verified raw SHA-256 before read", len(raw), "No raw write"),
        (2, "RAW_PRESERVATION", "Preserved all 20 raw columns as source text", len(raw), "No raw value changed"),
        (3, "MISSINGNESS", "Added flags for nine analytically important raw fields; no imputation", int(raw.apply(lambda col: blank_to_na(col).isna()).any(axis=1).sum()), "Rows retained"),
        (4, "DATE", "Parsed observation date and added week/month/day-of-week", int(observation_date.notna().sum()), "Raw w_date/timestamp retained"),
        (5, "CATEGORY", "Split and trimmed four hierarchy levels", len(raw), "No category reassignment"),
        (6, "COMPACT_COUNTS", "Parsed sold/rating/favorite displays with suffix, precision, and status", int(cleaned["total_sold_parsed"].notna().sum()), "Parsed values remain approximate where compact"),
        (7, "SALES_SAFEGUARD", "Marked total_sold unusable and total_rating unverified", len(raw), "No sales metric created"),
        (8, "ITEM_RATING", "Parsed numeric average rating and preserved unrated/missing states", int(cleaned["item_rating_numeric"].notna().sum()), "No imputation"),
        (9, "PRICE", "Created cleaned prices and missing/zero/sentinel/suspicious statuses", int((~price_ori_status.eq("VALID") | ~price_actual_status.eq("VALID")).sum()), "Rows/raw prices retained"),
        (10, "DISCOUNT", "Calculated discount only for valid comparable price pairs", int(comparable.sum()), "Not revenue or campaign data"),
        (11, "DUPLICATES", "Added exact/key/potential duplicate flags and review group IDs", int(cleaned["duplicate_review_flag"].eq("TRUE").sum()), "No deletion"),
        (12, "MATCHED_COHORT", "Added product history, intervals, and structural eligibility fields", int(cleaned["matched_product_flag"].eq("TRUE").sum()), "Final movement blocked"),
        (13, "NEGATIVE_CHANGE", "Flagged decreases in ambiguous cumulative counter", int(cleaned["negative_change_flag"].eq("TRUE").sum()), "No clamping/interpolation"),
        (14, "CATEGORY_CHANGE", "Added product/path/category change fields", int(cleaned["product_category_change_flag"].eq("TRUE").sum()), "No reassignment"),
        (15, "COVERAGE", "Added daily/category/product coverage counts", len(raw), "No weighting or row duplication"),
        (16, "OUTLIERS", "Added descriptive statistical outlier flags", int((ori_outlier | actual_outlier | sold_outlier | favorite_outlier | rating_outlier).sum()), "No removal"),
    ]
    transformation_summary = pd.DataFrame(
        transformation_rows,
        columns=["step", "area", "transformation", "affected_rows", "integrity_treatment"],
    )

    cleaning_summary = pd.DataFrame(
        [
            ("rows", len(raw), len(cleaned), len(cleaned) - len(raw)),
            ("columns", len(raw_columns), len(cleaned.columns), len(cleaned.columns) - len(raw_columns)),
            ("raw_columns_preserved", len(raw_columns), len(raw_columns), 0),
            ("exact_duplicate_rows", int(raw.duplicated().sum()), int(cleaned["exact_duplicate_flag"].eq("TRUE").sum()), 0),
            ("snapshot_key_duplicate_rows", int(raw.duplicated(["id", "w_date"]).sum()), int(cleaned["snapshot_key_duplicate_flag"].eq("TRUE").sum()), 0),
            ("rows_removed", 0, 0, 0),
            ("valid_observation_dates", int(observation_date.notna().sum()), int(cleaned["date_parse_status"].eq("VALID").sum()), 0),
            ("valid_comparable_price_pairs", 0, int(comparable.sum()), int(comparable.sum())),
            ("matched_products", 0, int(work.loc[work["product_observation_count"].gt(1), "id"].nunique()), int(work.loc[work["product_observation_count"].gt(1), "id"].nunique())),
            ("verified_sales_metric_fields", 0, 0, 0),
        ],
        columns=["metric", "raw", "processed", "change"],
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_csv(cleaned, OUTPUT_PATH)
    write_csv(cleaning_summary, TABLE_DIR / "phase_2_cleaning_summary.csv")
    write_csv(transformation_summary, TABLE_DIR / "phase_2_transformation_summary.csv")
    write_csv(missing_summary, TABLE_DIR / "phase_2_missingness_summary.csv")
    write_csv(anomaly_summary, TABLE_DIR / "phase_2_anomaly_summary.csv")
    write_csv(category_change_summary, TABLE_DIR / "phase_2_category_change_summary.csv")
    write_csv(duplicate_review_summary, TABLE_DIR / "phase_2_duplicate_review_summary.csv")
    write_csv(matched_product_summary, TABLE_DIR / "phase_2_matched_product_summary.csv")
    write_csv(transformation_summary, REPORT_DIR / "data_cleaning_audit_log.csv")

    raw_hash_after = sha256(source)
    if raw_hash_after != raw_hash_before:
        raise RuntimeError("Raw source changed while cleaning")
    manifest = {
        "source_path": str(source.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": raw_hash_after,
        "source_rows": len(raw),
        "source_columns": len(raw_columns),
        "processed_path": str(OUTPUT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "processed_sha256": sha256(OUTPUT_PATH),
        "processed_rows": len(cleaned),
        "processed_columns": len(cleaned.columns),
        "rows_removed": 0,
        "raw_columns_preserved": raw_columns,
        "verified_sales_metric_created": False,
        "total_sold_metric_status": "UNVERIFIED_UNUSABLE_AS_SALES_METRIC",
        "total_rating_metric_status": "UNVERIFIED_DUPLICATES_TOTAL_SOLD",
        "price_iqr_fences": {
            "price_ori_clean": [ori_lower, ori_upper],
            "price_actual_clean": [actual_lower, actual_upper],
        },
        "other_iqr_fences": {
            "unverified_counter": [sold_lower, sold_upper],
            "favorite": [favorite_lower, favorite_upper],
            "item_rating": [rating_lower, rating_upper],
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Raw: {len(raw):,} rows x {len(raw_columns)} columns")
    print(f"Processed: {len(cleaned):,} rows x {len(cleaned.columns)} columns")
    print(f"Rows removed: {len(raw) - len(cleaned)}")
    print(f"Raw SHA-256: {raw_hash_after}")
    print(f"Processed SHA-256: {manifest['processed_sha256']}")
    print(f"Output: {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
