"""Read-only Phase 1 profiler for the Shopee listing-snapshot CSV.

The script validates the immutable source hash, reads the complete CSV, and writes
profiling evidence only to outputs/. It never writes to data/, mutates the source,
or applies cleaning decisions.
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
EXPECTED_SHA256 = "afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69"
SOURCE_CANDIDATES = (
    ROOT / "data" / "raw" / "shopee_sales_data.csv",
    ROOT / "dataset" / "shopee_sales_data.csv",
)
RESULT_PATH = ROOT / "outputs" / "analysis_results" / "phase_1_profile.json"
TABLE_DIR = ROOT / "outputs" / "tables"


def source_path() -> Path:
    existing = [path for path in SOURCE_CANDIDATES if path.is_file()]
    if len(existing) != 1:
        raise RuntimeError(f"Expected exactly one raw dataset, found: {existing}")
    return existing[0]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compact_number(value: Any) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower().replace(",", "")
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([kmb]?)", text)
    if not match:
        return np.nan
    multiplier = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    return float(match.group(1)) * multiplier[match.group(2)]


def favorite_number(value: Any) -> float:
    if pd.isna(value):
        return np.nan
    match = re.search(r"([0-9]+(?:\.[0-9]+)?\s*[kKmMbB]?)", str(value))
    return compact_number(match.group(1)) if match else np.nan


def finite_or_none(value: Any) -> Any:
    if isinstance(value, (float, np.floating)) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {str(key): finite_or_none(value) for key, value in row.items()}
        for row in frame.replace({pd.NA: None, np.nan: None}).to_dict(orient="records")
    ]


def numeric_profile(series: pd.Series) -> dict[str, Any]:
    values = pd.to_numeric(series, errors="coerce")
    valid = values.dropna()
    q = valid.quantile([0, 0.01, 0.25, 0.5, 0.75, 0.99, 1]) if len(valid) else pd.Series(dtype=float)
    q1 = valid.quantile(0.25) if len(valid) else np.nan
    q3 = valid.quantile(0.75) if len(valid) else np.nan
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return {
        "non_null_numeric": int(valid.size),
        "missing_or_unparseable": int(values.isna().sum()),
        "min": finite_or_none(valid.min()) if len(valid) else None,
        "max": finite_or_none(valid.max()) if len(valid) else None,
        "mean": finite_or_none(valid.mean()) if len(valid) else None,
        "median": finite_or_none(valid.median()) if len(valid) else None,
        "std": finite_or_none(valid.std()) if len(valid) else None,
        "quantiles": {str(index): finite_or_none(value) for index, value in q.items()},
        "zero_count": int((valid == 0).sum()),
        "negative_count": int((valid < 0).sum()),
        "iqr_lower_fence": finite_or_none(lower),
        "iqr_upper_fence": finite_or_none(upper),
        "iqr_outlier_count": int(((valid < lower) | (valid > upper)).sum()) if len(valid) else 0,
        "largest_values": [finite_or_none(value) for value in valid.nlargest(10).tolist()],
    }


def categorical_profile(series: pd.Series) -> dict[str, Any]:
    non_null = series.dropna().astype(str)
    stripped = non_null.str.strip()
    lowered = stripped.str.casefold()
    raw_unique = int(non_null.nunique())
    stripped_unique = int(stripped.nunique())
    lower_unique = int(lowered.nunique())
    case_groups = (
        pd.DataFrame({"raw": stripped, "normalized": lowered})
        .drop_duplicates()
        .groupby("normalized")["raw"]
        .agg(list)
    )
    collisions = case_groups[case_groups.map(len) > 1]
    counts = non_null.value_counts()
    return {
        "unique_non_null": raw_unique,
        "leading_or_trailing_whitespace_rows": int((non_null != stripped).sum()),
        "unique_after_strip": stripped_unique,
        "unique_after_strip_casefold": lower_unique,
        "case_collision_group_count": int(len(collisions)),
        "case_collision_examples": {str(index): values for index, values in collisions.head(20).items()},
        "rare_values_frequency_le_5": int((counts <= 5).sum()),
        "top_values": {str(index): int(value) for index, value in counts.head(20).items()},
    }


def group_missingness(df: pd.DataFrame, group: pd.Series, label: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for column in df.columns:
        if df[column].isna().sum() == 0:
            continue
        table = pd.DataFrame({label: group, "missing": df[column].isna()}).dropna(subset=[label])
        rates = table.groupby(label)["missing"].agg(["sum", "count"])
        rates = rates[rates["count"] >= 5]
        rates["rate_pct"] = rates["sum"] / rates["count"] * 100
        top = rates.sort_values(["rate_pct", "count"], ascending=[False, False]).head(10).reset_index()
        output[column] = records(top)
    return output


def main() -> None:
    source = source_path()
    source_hash = file_sha256(source)
    if source_hash != EXPECTED_SHA256:
        raise RuntimeError(f"Raw source hash mismatch: {source_hash}")

    df = pd.read_csv(source, low_memory=False)
    raw_columns = list(df.columns)
    dates = pd.to_datetime(df["w_date"], errors="coerce")
    timestamps = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
    category_parts = df["item_category_detail"].astype("string").str.split("|")
    for level in range(4):
        df[f"_category_l{level + 1}"] = category_parts.str[level].str.strip()

    parsed = {
        "price_ori": pd.to_numeric(df["price_ori"], errors="coerce"),
        "price_actual": pd.to_numeric(df["price_actual"], errors="coerce"),
        "item_rating": pd.to_numeric(df["item_rating"], errors="coerce"),
        "total_rating": df["total_rating"].map(compact_number),
        "total_sold": df["total_sold"].map(compact_number),
        "favorite": df["favorite"].map(favorite_number),
        "timestamp": pd.to_numeric(df["timestamp"], errors="coerce"),
    }

    field_rows = []
    for column in raw_columns:
        field_rows.append(
            {
                "column": column,
                "raw_dtype": str(df[column].dtype),
                "rows": int(len(df)),
                "non_null": int(df[column].notna().sum()),
                "missing": int(df[column].isna().sum()),
                "missing_pct": round(float(df[column].isna().mean() * 100), 4),
                "unique_non_null": int(df[column].nunique(dropna=True)),
                "cardinality_pct": round(float(df[column].nunique(dropna=True) / len(df) * 100), 4),
                "memory_bytes_deep": int(df[column].memory_usage(index=False, deep=True)),
            }
        )
    field_profile = pd.DataFrame(field_rows)

    daily = pd.DataFrame(
        {
            "date": dates,
            "product_id": df["id"],
            "category_l2": df["_category_l2"],
            "seller": df["seller_name"],
            "price_actual": parsed["price_actual"],
            "total_sold_parsed": parsed["total_sold"],
            "favorite_parsed": parsed["favorite"],
        }
    )
    daily_coverage = (
        daily.groupby("date")
        .agg(
            observations=("product_id", "size"),
            unique_products=("product_id", "nunique"),
            categories_l2=("category_l2", "nunique"),
            sellers=("seller", "nunique"),
            mean_price_actual=("price_actual", "mean"),
            median_price_actual=("price_actual", "median"),
            mean_total_sold_parsed=("total_sold_parsed", "mean"),
            median_total_sold_parsed=("total_sold_parsed", "median"),
            mean_favorite_parsed=("favorite_parsed", "mean"),
            median_favorite_parsed=("favorite_parsed", "median"),
        )
        .reset_index()
    )
    daily_coverage["date"] = daily_coverage["date"].dt.strftime("%Y-%m-%d")

    product_stats = (
        pd.DataFrame({"id": df["id"], "date": dates})
        .groupby("id")
        .agg(observations=("date", "size"), first_date=("date", "min"), last_date=("date", "max"))
    )
    product_stats["span_days"] = (product_stats["last_date"] - product_stats["first_date"]).dt.days
    repeated = product_stats[product_stats["observations"] > 1]

    ordered = pd.DataFrame(
        {"id": df["id"], "date": dates, "total_sold": parsed["total_sold"]}
    ).sort_values(["id", "date"])
    ordered["previous_date"] = ordered.groupby("id")["date"].shift()
    ordered["previous_sold"] = ordered.groupby("id")["total_sold"].shift()
    ordered["interval_days"] = (ordered["date"] - ordered["previous_date"]).dt.days
    ordered["sold_delta"] = ordered["total_sold"] - ordered["previous_sold"]
    intervals = ordered[ordered["previous_date"].notna()]

    category_daily = (
        pd.DataFrame({"category_l2": df["_category_l2"], "date": dates, "id": df["id"]})
        .groupby(["category_l2", "date"])
        .agg(observations=("id", "size"), unique_products=("id", "nunique"))
        .reset_index()
    )
    category_coverage = (
        category_daily.groupby("category_l2")
        .agg(
            first_date=("date", "min"),
            last_date=("date", "max"),
            days_present=("date", "nunique"),
            total_observations=("observations", "sum"),
            min_daily_products=("unique_products", "min"),
            max_daily_products=("unique_products", "max"),
            median_daily_products=("unique_products", "median"),
        )
        .reset_index()
    )
    repeat_categories = (
        df[df["id"].isin(repeated.index)]
        .groupby("_category_l2")["id"]
        .nunique()
        .rename("repeated_products")
    )
    category_coverage = category_coverage.merge(
        repeat_categories, how="left", left_on="category_l2", right_index=True
    )
    category_coverage["repeated_products"] = category_coverage["repeated_products"].fillna(0).astype(int)
    category_coverage["first_date"] = category_coverage["first_date"].dt.strftime("%Y-%m-%d")
    category_coverage["last_date"] = category_coverage["last_date"].dt.strftime("%Y-%m-%d")

    category_history = (
        df.groupby("id")["item_category_detail"]
        .agg(lambda values: list(dict.fromkeys(values.astype(str).tolist())))
    )
    changed_ids = category_history[category_history.map(len) > 1].index
    changing_rows = df[df["id"].isin(changed_ids)][
        ["id", "w_date", "title", "seller_name", "item_category_detail"]
    ].sort_values(["id", "w_date"])
    l2_changes = (
        df[df["id"].isin(changed_ids)].groupby("id")["_category_l2"].nunique(dropna=False)
    )
    l3_changes = (
        df[df["id"].isin(changed_ids)].groupby("id")["_category_l3"].nunique(dropna=False)
    )

    exact_equal = df["total_sold"].eq(df["total_rating"])
    both_missing = df["total_sold"].isna() & df["total_rating"].isna()
    equality = exact_equal | both_missing
    representative = df.loc[
        [0, 1, 2, len(df) // 2, len(df) - 1],
        ["id", "w_date", "title", "item_category_detail", "item_rating", "total_rating", "total_sold", "favorite", "price_actual"],
    ]
    repeated_examples = (
        df[df["id"].isin(repeated.index)]
        .sort_values(["id", "w_date"])
        .groupby("id")
        .filter(lambda group: len(group) >= 3)
        .groupby("id", group_keys=False)
        .head(3)
        .head(15)[["id", "w_date", "item_category_detail", "item_rating", "total_rating", "total_sold", "favorite", "price_actual"]]
    )

    price_pairs = parsed["price_ori"].notna() & parsed["price_actual"].notna()
    valid_discount_base = price_pairs & (parsed["price_ori"] > 0) & (parsed["price_actual"] >= 0)
    discount_pct = (1 - parsed["price_actual"][valid_discount_base] / parsed["price_ori"][valid_discount_base]) * 100

    potential_duplicate_groups = (
        df.groupby(["seller_name", "title", "w_date"], dropna=False)
        .agg(rows=("id", "size"), distinct_ids=("id", "nunique"), distinct_links=("link_ori", "nunique"))
        .reset_index()
    )
    potential_duplicate_groups = potential_duplicate_groups[
        (potential_duplicate_groups["rows"] > 1) & (potential_duplicate_groups["distinct_ids"] > 1)
    ].sort_values("rows", ascending=False)

    category_levels = {}
    for level in range(1, 5):
        column = f"_category_l{level}"
        counts = df[column].value_counts(dropna=False)
        category_levels[f"level_{level}"] = {
            "unique_non_null": int(df[column].nunique(dropna=True)),
            "missing": int(df[column].isna().sum()),
            "rare_values_frequency_le_5": int((counts <= 5).sum()),
            "top_values": {str(index): int(value) for index, value in counts.head(30).items()},
            "categorical_quality": categorical_profile(df[column]),
        }

    missing_columns = [column for column in raw_columns if df[column].isna().any()]
    missing_by_date = {}
    for column in missing_columns:
        table = pd.DataFrame({"date": dates, "missing": df[column].isna()})
        grouped = table.groupby("date")["missing"].agg(["sum", "count"])
        grouped["rate_pct"] = grouped["sum"] / grouped["count"] * 100
        missing_by_date[column] = records(grouped.reset_index().sort_values("rate_pct", ascending=False).head(10))

    profile = {
        "source": {
            "path": str(source.relative_to(ROOT)).replace("\\", "/"),
            "file_size_bytes": int(source.stat().st_size),
            "sha256": source_hash,
            "expected_sha256_match": source_hash == EXPECTED_SHA256,
        },
        "structure": {
            "rows": int(len(df)),
            "columns": int(len(raw_columns)),
            "column_names": raw_columns,
            "dataframe_memory_bytes_deep": int(df[raw_columns].memory_usage(index=True, deep=True).sum()),
            "exact_duplicate_rows": int(df[raw_columns].duplicated().sum()),
            "duplicate_id_date_extra_rows": int(df.duplicated(["id", "w_date"]).sum()),
            "duplicate_idelastic": int(df["idElastic"].duplicated().sum()),
        },
        "field_profile": records(field_profile),
        "numeric_profiles": {name: numeric_profile(series) for name, series in parsed.items()},
        "categorical_profiles": {
            column: categorical_profile(df[column])
            for column in raw_columns
            if not pd.api.types.is_numeric_dtype(df[column])
        },
        "missingness": {
            "by_date_top_rates": missing_by_date,
            "by_category_l2_top_rates": group_missingness(df[raw_columns], df["_category_l2"], "category_l2"),
            "by_seller_top_rates_min_5_rows": group_missingness(df[raw_columns], df["seller_name"], "seller_name"),
            "products_with_any_missing": int(df.loc[df[raw_columns].isna().any(axis=1), "id"].nunique()),
        },
        "sold_rating_investigation": {
            "equal_including_both_missing": int(equality.sum()),
            "unequal": int((~equality).sum()),
            "equal_pct": float(equality.mean() * 100),
            "unequal_pct": float((~equality).mean() * 100),
            "both_missing": int(both_missing.sum()),
            "exact_string_equal_nonmissing": int(exact_equal.sum()),
            "parsed_numeric_equal_nonmissing": int(
                (parsed["total_sold"].eq(parsed["total_rating"]) & parsed["total_sold"].notna()).sum()
            ),
            "total_sold_profile": numeric_profile(parsed["total_sold"]),
            "total_rating_profile": numeric_profile(parsed["total_rating"]),
            "sold_favorite_pearson": finite_or_none(parsed["total_sold"].corr(parsed["favorite"])),
            "sold_item_rating_pearson": finite_or_none(parsed["total_sold"].corr(parsed["item_rating"])),
            "representative_rows": records(representative),
            "repeated_product_examples": records(repeated_examples),
        },
        "snapshot_behavior": {
            "unique_products": int(df["id"].nunique()),
            "products_observed_once": int((product_stats["observations"] == 1).sum()),
            "products_observed_multiple_times": int(len(repeated)),
            "repeat_product_pct": float(len(repeated) / len(product_stats) * 100),
            "observations_per_product_distribution": {
                str(int(index)): int(value)
                for index, value in product_stats["observations"].value_counts().sort_index().items()
            },
            "repeated_span_days_distribution": {
                str(int(index)): int(value)
                for index, value in repeated["span_days"].value_counts().sort_index().items()
            },
            "observation_interval_days_distribution": {
                str(int(index)): int(value)
                for index, value in intervals["interval_days"].value_counts().sort_index().items()
            },
            "products_with_at_least_3_observations": int((product_stats["observations"] >= 3).sum()),
            "products_with_at_least_4_observations": int((product_stats["observations"] >= 4).sum()),
            "positive_sold_intervals": int((intervals["sold_delta"] > 0).sum()),
            "zero_sold_intervals": int((intervals["sold_delta"] == 0).sum()),
            "negative_sold_intervals": int((intervals["sold_delta"] < 0).sum()),
        },
        "time_coverage": {
            "first_date": dates.min().strftime("%Y-%m-%d"),
            "last_date": dates.max().strftime("%Y-%m-%d"),
            "distinct_dates": int(dates.nunique()),
            "invalid_dates": int(dates.isna().sum()),
            "missing_calendar_dates": [
                date.strftime("%Y-%m-%d")
                for date in pd.date_range(dates.min(), dates.max(), freq="D").difference(pd.DatetimeIndex(dates.dropna().unique()))
            ],
            "timestamp_matches_w_date": int((timestamps.dt.date == dates.dt.date).sum()),
        },
        "daily_coverage": records(daily_coverage),
        "category": {
            "levels": category_levels,
            "category_coverage": records(category_coverage),
            "products_changing_full_path": int(len(changed_ids)),
            "products_changing_level_2": int((l2_changes > 1).sum()),
            "products_changing_level_3": int((l3_changes > 1).sum()),
        },
        "price_investigation": {
            "price_pair_rows": int(price_pairs.sum()),
            "valid_discount_base_rows": int(valid_discount_base.sum()),
            "actual_below_original": int((parsed["price_actual"][price_pairs] < parsed["price_ori"][price_pairs]).sum()),
            "actual_equals_original": int((parsed["price_actual"][price_pairs] == parsed["price_ori"][price_pairs]).sum()),
            "actual_above_original": int((parsed["price_actual"][price_pairs] > parsed["price_ori"][price_pairs]).sum()),
            "actual_999999999": int((parsed["price_actual"] == 999999999).sum()),
            "original_999999999": int((parsed["price_ori"] == 999999999).sum()),
            "actual_zero": int((parsed["price_actual"] == 0).sum()),
            "original_zero": int((parsed["price_ori"] == 0).sum()),
            "discount_pct_profile": numeric_profile(discount_pct),
            "rows_with_currency_symbols_in_raw_price_fields": 0,
        },
        "duplicates": {
            "exact_duplicate_rows": int(df[raw_columns].duplicated().sum()),
            "duplicate_id_date_rows": int(df.duplicated(["id", "w_date"]).sum()),
            "duplicate_idelastic_rows": int(df["idElastic"].duplicated().sum()),
            "same_seller_title_date_multiple_id_groups": int(len(potential_duplicate_groups)),
            "same_seller_title_date_multiple_id_rows": int(potential_duplicate_groups["rows"].sum()),
            "potential_duplicate_examples": records(potential_duplicate_groups.head(20)),
        },
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    field_profile.to_csv(TABLE_DIR / "phase_1_field_profile.csv", index=False)
    daily_coverage.to_csv(TABLE_DIR / "phase_1_daily_coverage.csv", index=False)
    category_coverage.to_csv(TABLE_DIR / "phase_1_category_coverage.csv", index=False)
    changing_rows.to_csv(TABLE_DIR / "phase_1_category_changes.csv", index=False)

    print(f"Profiled {len(df):,} rows x {len(raw_columns)} columns")
    print(f"Source SHA-256: {source_hash}")
    print(f"Wrote: {RESULT_PATH.relative_to(ROOT)}")
    print(f"Wrote 4 audit tables to: {TABLE_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
