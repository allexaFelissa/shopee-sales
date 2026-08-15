"""Independent reconciliation checks for Phase 4 analytical tables."""

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
SOURCE_SHA256 = "407c6f5e654283461c8eba20a3a1721f5105650212e92ae99206ea6dbadd199d"
RAW_PATH = ROOT / "dataset" / "shopee_sales_data.csv"
RAW_SHA256 = "afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69"
MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_4_transformation_manifest.json"
RESULTS_PATH = ROOT / "outputs" / "tables" / "phase_4_validation_results.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)


def number(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column].replace("", pd.NA), errors="coerce")


def close(left: pd.Series, right: pd.Series, tolerance: float = 1e-8) -> bool:
    left_num = pd.to_numeric(left, errors="coerce")
    right_num = pd.to_numeric(right, errors="coerce")
    both_missing = left_num.isna() & right_num.isna()
    equal = np.isclose(left_num.fillna(0), right_num.fillna(0), rtol=1e-9, atol=tolerance)
    return bool((both_missing | equal).all())


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, encoding="utf-8", lineterminator="\n")
    temporary.replace(path)


def main() -> int:
    checks: list[dict[str, Any]] = []

    def check(check_id: str, area: str, severity: str, passed: bool, expected: Any,
              observed: Any, detail: str) -> None:
        checks.append({
            "check_id": check_id,
            "area": area,
            "severity": severity,
            "status": "PASS" if passed else "FAIL",
            "expected": expected,
            "observed": observed,
            "detail": detail,
        })

    source_hash = sha256(SOURCE_PATH)
    raw_hash = sha256(RAW_PATH)
    check("SRC-001", "SOURCE_INTEGRITY", "CRITICAL", source_hash == SOURCE_SHA256, SOURCE_SHA256,
          source_hash, "Validated Phase 2 source hash.")
    check("SRC-002", "SOURCE_INTEGRITY", "CRITICAL", raw_hash == RAW_SHA256, RAW_SHA256,
          raw_hash, "Immutable raw source hash.")
    source = read_csv(SOURCE_PATH)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expected_names = {
        "product_snapshots", "matched_observations", "product_coverage", "daily_coverage",
        "category_daily_coverage", "category_level2_summary",
    }
    check("TAB-001", "TABLE_INVENTORY", "CRITICAL", set(manifest["tables"]) == expected_names,
          sorted(expected_names), sorted(manifest["tables"]), "Exact analytical table inventory.")

    tables: dict[str, pd.DataFrame] = {}
    for name in sorted(expected_names):
        metadata = manifest["tables"][name]
        path = ROOT / metadata["path"]
        exists = path.is_file()
        check(f"TAB-{name}", "TABLE_INVENTORY", "CRITICAL", exists, "exists", exists,
              metadata["path"])
        if exists:
            frame = read_csv(path)
            tables[name] = frame
            shape_ok = frame.shape == (metadata["rows"], metadata["columns"])
            schema_ok = list(frame.columns) == metadata["schema"]
            hash_ok = sha256(path) == metadata["sha256"]
            check(f"SCH-{name}", "SCHEMA", "CRITICAL", shape_ok and schema_ok and hash_ok,
                  f"{metadata['rows']}x{metadata['columns']}; documented schema/hash",
                  f"{frame.shape[0]}x{frame.shape[1]}; schema={schema_ok}; hash={hash_ok}",
                  "Manifest reconciliation.")

    if set(tables) != expected_names:
        write_csv(pd.DataFrame(checks), RESULTS_PATH)
        return 1

    snapshots = tables["product_snapshots"]
    matched = tables["matched_observations"]
    products = tables["product_coverage"]
    daily = tables["daily_coverage"]
    category_daily = tables["category_daily_coverage"]
    category_summary = tables["category_level2_summary"]

    key_specs = {
        "product_snapshots": ["product_id", "observation_date"],
        "matched_observations": ["product_id", "current_observation_date"],
        "product_coverage": ["product_id"],
        "daily_coverage": ["observation_date"],
        "category_daily_coverage": ["category_level_2", "observation_date"],
        "category_level2_summary": ["category_level_2"],
    }
    for name, keys in key_specs.items():
        duplicate_count = int(tables[name].duplicated(keys).sum())
        missing_count = int(tables[name][keys].eq("").any(axis=1).sum())
        check(f"KEY-{name}", "GRAIN_AND_KEYS", "CRITICAL",
              duplicate_count == 0 and missing_count == 0, "0 duplicate / 0 missing",
              f"duplicates={duplicate_count}; missing={missing_count}", "+".join(keys))

    source_rows = source[[
        "source_row_number", "id", "observation_date", "title", "seller_name", "link_ori",
        "category_level_2", "category_level_3", "category_level_4", "category_path_clean",
        "price_actual_clean", "price_actual_status", "price_ori_clean", "price_ori_status",
        "discount_amount", "discount_pct", "favorite_parsed", "favorite_parse_status",
        "item_rating_numeric", "item_rating_status", "total_sold_metric_status",
        "total_rating_metric_status",
    ]].copy()
    merged = snapshots.merge(source_rows, on="source_row_number", how="outer", indicator=True, validate="one_to_one")
    identity_ok = (
        merged["_merge"].eq("both").all()
        and merged["product_id"].eq(merged["id"]).all()
        and merged["observation_date_x"].eq(merged["observation_date_y"]).all()
        and merged["product_title"].eq(merged["title"]).all()
        and merged["seller_name_x"].eq(merged["seller_name_y"]).all()
        and merged["product_url"].eq(merged["link_ori"]).all()
        and merged["category_level_2_x"].eq(merged["category_level_2_y"]).all()
        and merged["category_level_3_x"].eq(merged["category_level_3_y"]).all()
        and merged["category_level_4_x"].eq(merged["category_level_4_y"]).all()
        and merged["category_path"].eq(merged["category_path_clean"]).all()
    )
    check("SNP-001", "SNAPSHOT_LINEAGE", "CRITICAL", bool(identity_ok),
          "20,312 one-to-one source mappings", int(merged["_merge"].eq("both").sum()),
          "Identifiers, dates, product labels, and categories map to validated source rows.")
    value_ok = (
        close(merged["actual_price"], merged["price_actual_clean"])
        and close(merged["original_price"], merged["price_ori_clean"])
        and close(merged["discount_amount_x"], merged["discount_amount_y"])
        and close(merged["discount_percent"], merged["discount_pct"])
        and close(merged["favorite_count_approx"], merged["favorite_parsed"])
        and close(merged["average_rating"], merged["item_rating_numeric"])
        and merged["actual_price_status"].eq(merged["price_actual_status"]).all()
        and merged["original_price_status"].eq(merged["price_ori_status"]).all()
        and merged["favorite_status"].eq(merged["favorite_parse_status"]).all()
        and merged["average_rating_status"].eq(merged["item_rating_status"]).all()
    )
    check("SNP-002", "SNAPSHOT_LINEAGE", "CRITICAL", bool(value_ok), "all analytical values/statuses match",
          bool(value_ok), "Validity-aware price and engagement mapping.")

    expected_intervals = len(source) - source["id"].nunique()
    check("MAT-001", "MATCHED_OBSERVATIONS", "CRITICAL", len(matched) == expected_intervals,
          expected_intervals, len(matched), "Exactly one row for every non-first product observation.")
    snapshot_lookup = snapshots.copy()
    snapshot_lookup["source_row_number"] = number(snapshot_lookup, "source_row_number").astype("int64")
    current_lookup = snapshot_lookup.set_index("source_row_number")
    matched_current_rows = number(matched, "current_source_row_number").astype("int64")
    matched_previous_rows = number(matched, "previous_source_row_number").astype("int64")
    current_dates = pd.to_datetime(matched["current_observation_date"])
    previous_dates = pd.to_datetime(matched["previous_observation_date"])
    interval_ok = (
        matched_current_rows.isin(current_lookup.index).all()
        and matched_previous_rows.isin(current_lookup.index).all()
        and (current_dates - previous_dates).dt.days.eq(number(matched, "elapsed_days")).all()
        and number(matched, "elapsed_days").gt(0).all()
    )
    check("MAT-002", "MATCHED_OBSERVATIONS", "CRITICAL", bool(interval_ok),
          "valid source rows and positive date differences", bool(interval_ok), "Interval lineage and elapsed days.")
    valid_price = matched["actual_price_comparison_status"].eq("VALID_COMPARISON")
    expected_price_change = number(matched, "current_actual_price") - number(matched, "previous_actual_price")
    expected_price_pct = expected_price_change / number(matched, "previous_actual_price") * 100
    price_changes_ok = (
        close(number(matched.loc[valid_price], "actual_price_change"), expected_price_change[valid_price])
        and close(number(matched.loc[valid_price], "actual_price_change_percent"), expected_price_pct[valid_price])
        and matched.loc[~valid_price, ["actual_price_change", "actual_price_change_percent"]].eq("").all().all()
    )
    check("MAT-003", "MATCHED_OBSERVATIONS", "CRITICAL", bool(price_changes_ok),
          "valid comparisons recompute; invalid comparisons empty", bool(price_changes_ok), "Price-change logic.")
    movement_status_ok = (
        matched["sales_movement_metric_status"].eq("NO_VERIFIED_SALES_MOVEMENT_METRIC").all()
        and matched["total_sold_metric_status"].eq("UNVERIFIED_UNUSABLE_AS_SALES_METRIC").all()
        and matched["total_rating_metric_status"].eq("UNVERIFIED_DUPLICATES_TOTAL_SOLD").all()
    )
    check("MAT-004", "MATCHED_OBSERVATIONS", "CRITICAL", bool(movement_status_ok),
          "all rows retain restrictions", bool(movement_status_ok), "Sales-counter safeguard.")

    source_product_counts = source.groupby("id").size().sort_index()
    product_counts = number(products.set_index("product_id"), "observation_count").sort_index()
    product_ok = (
        len(products) == source["id"].nunique()
        and product_counts.equals(source_product_counts.astype("int64"))
        and int(number(products, "matched_interval_count").sum()) == expected_intervals
    )
    check("PRD-001", "PRODUCT_COVERAGE", "CRITICAL", bool(product_ok),
          "16,614 products; 20,312 observations; 3,698 intervals",
          f"{len(products)} products; {int(product_counts.sum())} observations; "
          f"{int(number(products, 'matched_interval_count').sum())} intervals",
          "Product-grain coverage reconciliation.")

    source_daily = source.groupby("observation_date").size().sort_index()
    daily_counts = number(daily.set_index("observation_date"), "sampled_snapshot_count").sort_index()
    daily_ok = len(daily) == 20 and daily_counts.equals(source_daily.astype("int64"))
    check("DAY-001", "DAILY_COVERAGE", "CRITICAL", bool(daily_ok), "20 dates and exact source counts",
          f"dates={len(daily)}; snapshots={int(daily_counts.sum())}", "Daily coverage reconciliation.")

    expected_grid_rows = source["category_level_2"].nunique() * source["observation_date"].nunique()
    category_daily_ok = (
        len(category_daily) == expected_grid_rows
        and int(number(category_daily, "sampled_snapshot_count").sum()) == len(source)
        and category_daily["category_level_2"].nunique() == 24
        and category_daily["observation_date"].nunique() == 20
    )
    check("CDY-001", "CATEGORY_DAILY_COVERAGE", "CRITICAL", bool(category_daily_ok),
          "480 grid rows; 20,312 sampled snapshots", f"{len(category_daily)} rows; "
          f"{int(number(category_daily, 'sampled_snapshot_count').sum())} snapshots",
          "Complete Level-2 category/date grid reconciliation.")

    source_category_counts = source.groupby("category_level_2").size().sort_index()
    summary_counts = number(category_summary.set_index("category_level_2"), "sampled_snapshot_count").sort_index()
    share_sum = number(category_summary, "sampled_snapshot_share_percent").sum()
    category_summary_ok = (
        len(category_summary) == 24
        and summary_counts.equals(source_category_counts.astype("int64"))
        and np.isclose(share_sum, 100, rtol=1e-9, atol=1e-8)
        and category_summary["performance_metric_status"].eq("NO_VERIFIED_SALES_OR_REVENUE_METRIC").all()
    )
    check("CAT-001", "CATEGORY_SUMMARY", "CRITICAL", bool(category_summary_ok),
          "24 categories; source counts; shares sum to 100%; no performance metric",
          f"categories={len(category_summary)}; snapshots={int(summary_counts.sum())}; share={share_sum}",
          "Level-2 structural summary reconciliation.")

    all_frames = list(tables.values())
    tier_ok = all(
        frame[column].eq("NOT_ASSIGNED_REQUIRES_APPROVED_THRESHOLDS").all()
        for frame in all_frames for column in frame.columns if column == "coverage_reliability_tier_status"
    )
    check("REL-001", "RELIABILITY", "HIGH", bool(tier_ok), "no tier assigned", bool(tier_ok),
          "Evidence fields are present; thresholds remain unapproved.")

    forbidden = re.compile(
        r"(^|_)(revenue|aov|orders?|units_sold|sales_velocity|sales_growth|momentum_score|category_rank)($|_)", re.I
    )
    forbidden_columns = []
    exposed_counters = []
    for name, frame in tables.items():
        forbidden_columns.extend(f"{name}.{column}" for column in frame.columns if forbidden.search(column))
        exposed_counters.extend(
            f"{name}.{column}" for column in frame.columns
            if ("total_sold" in column or "total_rating" in column) and not column.endswith("metric_status")
        )
    check("SAFE-001", "BUSINESS_SAFETY", "CRITICAL", not forbidden_columns and not exposed_counters,
          "no unsupported KPIs or exposed counters", " | ".join(forbidden_columns + exposed_counters) or "none",
          "No sales, revenue, order, AOV, momentum, ranking, or counter-value interface.")
    manifest_safety = manifest["safeguards"]
    safeguards_ok = (
        manifest_safety["verified_sales_metric_created"] is False
        and manifest_safety["category_ranking_created"] is False
        and manifest_safety["momentum_score_created"] is False
        and manifest_safety["reliability_tier_assigned"] is False
    )
    check("SAFE-002", "BUSINESS_SAFETY", "CRITICAL", safeguards_ok, "all false", safeguards_ok,
          "Transformation manifest safeguard declarations.")

    source_hash_after = sha256(SOURCE_PATH)
    raw_hash_after = sha256(RAW_PATH)
    check("SRC-003", "SOURCE_INTEGRITY", "CRITICAL",
          source_hash_after == source_hash and raw_hash_after == raw_hash,
          "source and raw hashes unchanged", f"processed={source_hash_after}; raw={raw_hash_after}",
          "No protected input changed during validation.")

    results = pd.DataFrame(checks)
    write_csv(results, RESULTS_PATH)
    failed = int(results["status"].eq("FAIL").sum())
    print(f"Phase 4 validation checks: {len(results)}")
    print(f"Passed: {int(results['status'].eq('PASS').sum())}")
    print(f"Failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
