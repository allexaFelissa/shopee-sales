"""Independent validation gate for the governed broad-category enrichment."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_PATHS = (ROOT / "data/raw/shopee_sales_data.csv", ROOT / "dataset/shopee_sales_data.csv")
EXPECTED_RAW_SHA256 = "afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69"
EXPECTED_PROCESSED_SHA256 = "407c6f5e654283461c8eba20a3a1721f5105650212e92ae99206ea6dbadd199d"
MAPPING_PATH = ROOT / "outputs/tables/broad_product_category_mapping.csv"
SOURCE_PATH = ROOT / "data/processed/shopee_sales_cleaned.csv"
SNAPSHOTS_PATH = ROOT / "data/processed/shopee_product_snapshots.csv"
MATCHED_PATH = ROOT / "data/processed/shopee_matched_observations.csv"
PRODUCTS_PATH = ROOT / "data/processed/shopee_product_coverage.csv"
RESULTS_PATH = ROOT / "outputs/tables/broad_product_category_validation_results.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    mapping = pd.read_csv(MAPPING_PATH, dtype=str, keep_default_na=False)
    source = pd.read_csv(SOURCE_PATH, usecols=["id", "observation_date", "category_level_2"], dtype=str)
    snapshots = pd.read_csv(SNAPSHOTS_PATH, dtype=str, keep_default_na=False)
    matched = pd.read_csv(MATCHED_PATH, dtype=str, keep_default_na=False)
    products = pd.read_csv(PRODUCTS_PATH, dtype=str, keep_default_na=False)
    raw_paths = [path for path in RAW_PATHS if path.is_file()]

    source_domain = set(source["category_level_2"])
    mapping_domain = set(mapping["category_level_2"])
    joined = source.merge(mapping, on="category_level_2", how="left", validate="many_to_one")
    expected_broad = snapshots["category_level_2"].map(
        mapping.set_index("category_level_2")["broad_product_category"]
    )
    level2_changed = products["level2_category_stable_flag"].eq("FALSE")
    same_broad_change = level2_changed & products["broad_product_category_stable_flag"].eq("TRUE")

    checks = [
        ("BPC-MAP-01", len(mapping) == 24 and not mapping["category_level_2"].duplicated().any(), "24 unique Level-2 mappings"),
        ("BPC-MAP-02", mapping["broad_product_category"].nunique() == 12, "12 governed broad groups"),
        ("BPC-MAP-03", source_domain == mapping_domain, "mapping domain exactly equals validated source domain"),
        ("BPC-MAP-04", not joined["broad_product_category"].isna().any(), "every validated source row maps"),
        ("BPC-DATA-01", len(source) == len(snapshots) == 20_312, "row count unchanged after enrichment"),
        ("BPC-DATA-02", snapshots["broad_product_category"].eq(expected_broad).all(), "snapshot broad values independently reproduce"),
        ("BPC-DATA-03", not snapshots["broad_product_category"].eq("").any(), "no unexpected broad-category blanks"),
        ("BPC-DATA-04", snapshots.groupby("category_level_2")["broad_product_category"].nunique().eq(1).all(), "Level-2 maps deterministically"),
        ("BPC-DATA-05", len(raw_paths) == 1 and sha256(raw_paths[0]) == EXPECTED_RAW_SHA256, "immutable raw hash unchanged"),
        ("BPC-DATA-06", sha256(SOURCE_PATH) == EXPECTED_PROCESSED_SHA256, "validated Phase 2 source hash unchanged"),
        ("BPC-STAB-01", {"previous_broad_product_category", "current_broad_product_category", "broad_product_category_stable_flag"}.issubset(matched.columns), "matched table exposes separate broad stability"),
        ("BPC-STAB-02", {"first_broad_product_category", "latest_broad_product_category", "distinct_broad_product_category_count", "broad_product_category_stable_flag"}.issubset(products.columns), "product table exposes separate broad stability"),
        ("BPC-STAB-03", (products.loc[level2_changed, "level2_category_stable_flag"] == "FALSE").all(), f"Level-2 change governance retained; {int(same_broad_change.sum())} same-broad changes remain identifiable"),
        ("BPC-SAFE-01", "category_level_2" in snapshots.columns, "original Level-2 field retained"),
    ]
    results = pd.DataFrame(checks, columns=["check_id", "passed", "evidence"])
    results["status"] = results["passed"].map({True: "PASS", False: "FAIL"})
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.drop(columns="passed").to_csv(RESULTS_PATH, index=False, encoding="utf-8", lineterminator="\n")
    failures = results.loc[~results["passed"]]
    print(f"Broad Product Category validation: {len(results) - len(failures)}/{len(results)} PASS")
    if not failures.empty:
        print(failures[["check_id", "evidence"]].to_string(index=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
