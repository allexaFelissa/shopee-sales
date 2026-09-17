"""Independent Phase 7 validation against the frozen Phase 6 KPI contract."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "outputs" / "tables"
RESULT_PATH = TABLE_DIR / "phase_7_validation_results.csv"
PHASE4_MANIFEST = ROOT / "outputs" / "analysis_results" / "phase_4_transformation_manifest.json"
PHASE6_MANIFEST = ROOT / "outputs" / "analysis_results" / "phase_6_kpi_design_manifest.json"
PHASE7_MANIFEST = ROOT / "outputs" / "analysis_results" / "phase_7_business_analysis_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float, float]:
    if total == 0:
        return np.nan, np.nan, np.nan
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    half = z * math.sqrt(
        proportion * (1 - proportion) / total + z**2 / (4 * total**2)
    ) / denominator
    lower = max(0, centre - half) * 100
    upper = min(1, centre + half) * 100
    return lower, upper, upper - lower


def direction(value: float) -> str:
    if pd.isna(value):
        return "MISSING"
    if value > 0:
        return "POSITIVE"
    if value < 0:
        return "NEGATIVE"
    return "ZERO"


def product_summary(frame: pd.DataFrame, categories: list[str]) -> pd.DataFrame:
    products = frame.groupby(["current_broad_product_category", "product_id"])["daily"].median().reset_index()
    rows = []
    for category in categories:
        values = products.loc[products["current_broad_product_category"].eq(category), "daily"]
        rows.append({
            "category": category,
            "n": len(values),
            "positive": int(values.gt(0).sum()),
            "zero": int(values.eq(0).sum()),
            "negative": int(values.lt(0).sum()),
            "breadth": values.gt(0).mean() * 100 if len(values) else np.nan,
            "median": values.median() if len(values) else np.nan,
        })
    return pd.DataFrame(rows).set_index("category")


def main() -> None:
    checks: list[dict[str, str]] = []

    def check(check_id: str, area: str, condition: bool, evidence: str) -> None:
        checks.append({
            "check_id": check_id,
            "area": area,
            "status": "PASS" if condition else "FAIL",
            "evidence": evidence,
        })

    phase4 = json.loads(PHASE4_MANIFEST.read_text(encoding="utf-8"))
    changed_inputs = []
    tables = {}
    for name, metadata in phase4["tables"].items():
        path = ROOT / metadata["path"]
        if sha256(path) != metadata["sha256"]:
            changed_inputs.append(name)
        tables[name] = pd.read_csv(path, low_memory=False)
    check("P7-IN-phase4-hashes", "input integrity", not changed_inputs, f"changed={changed_inputs}")

    phase6 = json.loads(PHASE6_MANIFEST.read_text(encoding="utf-8"))
    changed_specs = []
    for metadata in phase6["outputs"].values():
        path = ROOT / metadata["path"]
        if sha256(path) != metadata["sha256"]:
            changed_specs.append(metadata["path"])
    check("P7-IN-phase6-hashes", "input integrity", not changed_specs, f"changed={changed_specs}")
    specification = pd.read_csv(TABLE_DIR / "phase_6_kpi_specification.csv")
    check("P7-IN-approved-kpis", "KPI contract", len(specification) == 5 and set(specification["status"]) == {"APPROVED_CONTEXT", "APPROVED_CORE", "APPROVED_GOVERNANCE"}, f"rows={len(specification)}")

    snapshots = tables["product_snapshots"]
    matched = tables["matched_observations"].copy()
    categories = sorted(snapshots["broad_product_category"].unique().tolist())
    check("P7-IN-snapshot-shape", "input structure", snapshots.shape == (20_312, 66), str(snapshots.shape))
    check("P7-IN-matched-shape", "input structure", matched.shape == (3_698, 65), str(matched.shape))
    check("P7-IN-category-count", "input structure", len(categories) == 12, f"categories={len(categories)}")
    check("P7-IN-date-count", "input structure", snapshots["observation_date"].nunique() == 20, f"dates={snapshots['observation_date'].nunique()}")
    check("P7-IN-keys", "input structure", not snapshots.duplicated(["product_id", "observation_date"]).any() and not matched.duplicated(["product_id", "current_observation_date"]).any(), "snapshot and interval keys unique")

    exact_all = matched["favorite_comparison_status"].eq("VALID_EXACT_DISPLAY_VALUES")
    valid_all = matched["favorite_comparison_status"].ne("NOT_COMPARABLE_MISSING_OR_INVALID")
    stable = ~matched["level2_category_changed_over_time_flag"]
    matched["daily"] = matched["favorite_count_change_approx"] / matched["elapsed_days"]
    audit = snapshots.set_index("source_row_number")["favorite_outlier_flag"]
    endpoint_outlier = (
        matched["previous_source_row_number"].astype(int).map(audit).fillna(False).astype(bool)
        | matched["current_source_row_number"].astype(int).map(audit).fillna(False).astype(bool)
    )
    check("P7-EL-exact-all", "eligibility", int(exact_all.sum()) == 2_603, f"exact={int(exact_all.sum())}")
    check("P7-EL-valid-all", "eligibility", int(valid_all.sum()) == 3_489, f"valid={int(valid_all.sum())}")
    check("P7-EL-retention", "eligibility", math.isclose(exact_all.sum() / valid_all.sum() * 100, 74.605904, abs_tol=1e-6), f"retention={exact_all.sum()/valid_all.sum()*100:.6f}%")
    check("P7-EL-stable-exact", "eligibility", int((exact_all & stable).sum()) == 2_590, f"primary intervals={int((exact_all & stable).sum())}")
    check("P7-EL-category-change", "eligibility", not matched.loc[exact_all & stable, "level2_category_changed_over_time_flag"].any(), "all primary products stable")
    check("P7-EL-elapsed", "eligibility", matched.loc[exact_all & stable, "elapsed_days"].gt(0).all(), "all elapsed days positive")

    primary = product_summary(matched.loc[exact_all & stable], categories)
    compact = product_summary(matched.loc[valid_all & stable], categories)
    outlier = product_summary(matched.loc[exact_all & stable & ~endpoint_outlier], categories)
    interval_rows = []
    for category in categories:
        values = matched.loc[
            exact_all & stable & matched["current_broad_product_category"].eq(category), "daily"
        ]
        interval_rows.append({
            "category": category,
            "n": len(values),
            "positive": int(values.gt(0).sum()),
            "zero": int(values.eq(0).sum()),
            "negative": int(values.lt(0).sum()),
            "breadth": values.gt(0).mean() * 100 if len(values) else np.nan,
            "median": values.median() if len(values) else np.nan,
        })
    interval = pd.DataFrame(interval_rows).set_index("category")

    stable_snapshots = snapshots.loc[~snapshots["level2_category_changed_over_time_flag"]]
    observed_counts = stable_snapshots.groupby("broad_product_category")["product_id"].nunique()
    date_counts = snapshots.groupby("broad_product_category")["observation_date"].nunique()

    business = pd.read_csv(TABLE_DIR / "phase_7_category_business_analysis.csv")
    comparison = pd.read_csv(TABLE_DIR / "phase_7_category_comparison.csv")
    sensitivity = pd.read_csv(TABLE_DIR / "phase_7_sensitivity_analysis.csv")
    findings = pd.read_csv(TABLE_DIR / "phase_7_business_findings.csv")
    figure_review = pd.read_csv(TABLE_DIR / "phase_7_figure_review.csv")
    check("P7-OUT-business-rows", "output structure", len(business) == 12 and business["broad_product_category"].nunique() == 12, f"rows={len(business)}")
    check("P7-OUT-comparison-rows", "output structure", len(comparison) == 12 and comparison["broad_product_category"].nunique() == 12, f"rows={len(comparison)}")
    check("P7-OUT-sensitivity-rows", "output structure", len(sensitivity) == 48 and sensitivity.groupby("broad_product_category").size().eq(4).all(), f"rows={len(sensitivity)}")
    check("P7-OUT-findings", "output structure", 3 <= len(findings) <= 7, f"findings={len(findings)}")
    check("P7-OUT-figures", "output structure", len(figure_review) == 6 and figure_review["review_status"].eq("PASS_ANALYTICAL_VISUAL_REVIEW").all(), f"figures={len(figure_review)}")

    comparison_indexed = comparison.set_index("broad_product_category")
    count_errors = []
    kpi_errors = []
    tier_errors = []
    blank_errors = []
    sensitivity_errors = []
    for category in categories:
        output = comparison_indexed.loc[category]
        n = int(primary.loc[category, "n"])
        positive = int(primary.loc[category, "positive"])
        lower, upper, width = wilson(positive, n)
        dates = int(date_counts.get(category, 0))
        expected_tier = (
            "HIGH" if dates == 20 and n >= 100 and width <= 20
            else "MODERATE" if dates >= 15 and n >= 30 and width <= 35
            else "INSUFFICIENT"
        )
        if int(output["observed_stable_category_product_count"]) != int(observed_counts.get(category, 0)):
            count_errors.append(f"{category}: observed")
        if int(output["eligible_favorite_movement_product_count"]) != n:
            count_errors.append(f"{category}: eligible")
        if int(output["positive_product_count"]) + int(output["zero_product_count"]) + int(output["negative_product_count"]) != n:
            count_errors.append(f"{category}: direction reconciliation")
        if output["evidence_sufficiency_tier"] != expected_tier:
            tier_errors.append(category)
        if not (pd.isna(width) and pd.isna(output["positive_breadth_wilson_95_width_percentage_points"])) and not np.isclose(output["positive_breadth_wilson_95_width_percentage_points"], width, rtol=0, atol=1e-8):
            tier_errors.append(f"{category}: Wilson")
        if expected_tier == "INSUFFICIENT":
            if pd.notna(output["positive_favorite_movement_breadth"]) or pd.notna(output["median_daily_favorite_movement_per_product"]):
                blank_errors.append(category)
        else:
            if not np.isclose(output["positive_favorite_movement_breadth"], primary.loc[category, "breadth"], atol=1e-8):
                kpi_errors.append(f"{category}: breadth")
            if not np.isclose(output["median_daily_favorite_movement_per_product"], primary.loc[category, "median"], atol=1e-8):
                kpi_errors.append(f"{category}: median")
            scenario_expected = {
                "PRIMARY_EXACT_PRODUCT": primary.loc[category],
                "COMPACT_INCLUSIVE_PRODUCT": compact.loc[category],
                "OUTLIER_EXCLUDED_PRODUCT": outlier.loc[category],
                "INTERVAL_WEIGHTED_EXACT": interval.loc[category],
            }
            for scenario_name, expected in scenario_expected.items():
                row = sensitivity.loc[
                    sensitivity["broad_product_category"].eq(category)
                    & sensitivity["sensitivity_scenario"].eq(scenario_name)
                ].iloc[0]
                if int(row["eligible_unit_count"]) != int(expected["n"]):
                    sensitivity_errors.append(f"{category}: {scenario_name}: n")
                if not np.isclose(row["positive_favorite_movement_breadth"], expected["breadth"], atol=1e-8):
                    sensitivity_errors.append(f"{category}: {scenario_name}: breadth")
                if not np.isclose(row["median_daily_favorite_movement"], expected["median"], atol=1e-8):
                    sensitivity_errors.append(f"{category}: {scenario_name}: median")
    check("P7-KPI-counts", "KPI reconciliation", not count_errors, f"errors={count_errors}")
    check("P7-KPI-values", "KPI reconciliation", not kpi_errors, f"errors={kpi_errors}")
    check("P7-KPI-tiers", "KPI reconciliation", not tier_errors, f"errors={tier_errors}")
    check("P7-KPI-blanks", "KPI reconciliation", not blank_errors, f"errors={blank_errors}")
    check("P7-KPI-sensitivities", "KPI reconciliation", not sensitivity_errors, f"errors={sensitivity_errors}")

    tier_counts = business["evidence_sufficiency_tier"].value_counts().to_dict()
    check("P7-KPI-tier-counts", "KPI reconciliation", tier_counts == {"MODERATE": 4, "INSUFFICIENT": 4, "HIGH": 4}, str(tier_counts))
    check("P7-KPI-no-candidate", "decision gate", not business["further_investigation_candidate_flag"].astype(bool).any(), "formal candidates=0")
    check("P7-KPI-primary-grain", "KPI reconciliation", primary["n"].sum() == 2_169, f"eligible product-broad-category rows={int(primary['n'].sum())}")

    suppressed_sensitivity = sensitivity["evidence_sufficiency_tier"].eq("INSUFFICIENT")
    check("P7-SEN-insufficient-blanks", "sensitivity", sensitivity.loc[suppressed_sensitivity, ["positive_favorite_movement_breadth", "median_daily_favorite_movement"]].isna().all().all(), "insufficient sensitivity values blank")
    check("P7-SEN-required-scenarios", "sensitivity", set(sensitivity["sensitivity_scenario"]) == {"PRIMARY_EXACT_PRODUCT", "COMPACT_INCLUSIVE_PRODUCT", "OUTLIER_EXCLUDED_PRODUCT", "INTERVAL_WEIGHTED_EXACT"}, str(sorted(sensitivity["sensitivity_scenario"].unique())))

    required_finding_columns = {"finding", "supporting_kpis", "category", "evidence_tier", "sample_size", "sensitivity_status", "interpretation", "limitation", "business_implication"}
    check("P7-FIND-schema", "business findings", required_finding_columns <= set(findings.columns), "required finding fields present")
    check("P7-FIND-complete", "business findings", not findings[list(required_finding_columns)].isna().any().any(), "finding fields complete")
    narrative = " ".join(findings.astype(str).to_numpy().ravel()).lower()
    unsupported = ["sales are increasing", "revenue is growing", "customers are buying more", "campaign will succeed", "feature this category"]
    check("P7-FIND-no-unsupported", "business findings", not any(term in narrative for term in unsupported), "no unsupported business claims")
    check("P7-FIND-sample-size", "business findings", findings["sample_size"].str.strip().ne("").all(), "all findings include sample size")
    check("P7-FIND-sensitivity", "business findings", findings["sensitivity_status"].str.strip().ne("").all(), "all findings include sensitivity status")

    prohibited_columns = " ".join(
        list(business.columns) + list(comparison.columns) + list(sensitivity.columns)
    ).lower()
    check("P7-SAFE-no-sales", "safeguards", not re.search(r"(^|_)(sales|revenue|orders?|aov|customers?|conversion|campaign_effectiveness)($|_)", prohibited_columns), "no prohibited metric columns")
    check("P7-SAFE-no-composite", "safeguards", "score" not in prohibited_columns and "rank" not in prohibited_columns, "no composite score or rank")
    check("P7-SAFE-broad-term", "terminology", business.columns[0] == "broad_product_category" and not figure_review.astype(str).apply(lambda col: col.str.contains("Level-2", regex=False)).any().any(), "business-facing category terminology used")

    phase7 = json.loads(PHASE7_MANIFEST.read_text(encoding="utf-8"))
    output_hash_errors = []
    for metadata in list(phase7["output_tables"].values()) + list(phase7["figures"].values()):
        path = ROOT / metadata["path"]
        if sha256(path) != metadata["sha256"]:
            output_hash_errors.append(metadata["path"])
    check("P7-REP-output-hashes", "reproducibility", not output_hash_errors, f"mismatches={output_hash_errors}")
    check("P7-REP-version", "reproducibility", phase7["analysis_version"] == "2.0.0" and bool(phase7["analysis_timestamp_utc"]), f"version={phase7['analysis_version']}; timestamp={phase7['analysis_timestamp_utc']}")
    safeguards = phase7["safeguards"]
    check("P7-REP-safeguards", "reproducibility", (
        not safeguards["phase6_kpis_changed"]
        and not safeguards["total_sold_used"]
        and not safeguards["total_rating_used"]
        and not safeguards["sales_metric_created"]
        and not safeguards["revenue_metric_created"]
        and not safeguards["campaign_effectiveness_metric_created"]
        and not safeguards["composite_score_created"]
        and not safeguards["campaign_recommendation_created"]
        and not safeguards["phase4_data_modified"]
    ), str(safeguards))

    required_figures = [ROOT / metadata["path"] for metadata in phase7["figures"].values()]
    check("P7-FIG-files", "visual validation", all(path.exists() and path.stat().st_size > 25_000 for path in required_figures), f"figure_count={len(required_figures)}")

    status_text = (ROOT / "docs" / "project_status.md").read_text(encoding="utf-8")
    check("P7-STATUS-7", "phase status", bool(re.search(r"\| 7 \| Business Analysis \| COMPLETED \|", status_text)), "Phase 7 COMPLETED after downstream authorization")
    check("P7-STATUS-8", "phase status", bool(re.search(r"\| 8 \| Visualization \| COMPLETED \|", status_text)), "Phase 8 COMPLETED after its gate and Phase 9 authorization")

    result = pd.DataFrame(checks)
    temporary = RESULT_PATH.with_suffix(".csv.tmp")
    result.to_csv(temporary, index=False, encoding="utf-8", lineterminator="\n")
    temporary.replace(RESULT_PATH)
    failed = result.loc[result["status"].eq("FAIL")]
    print(f"Phase 7 validation checks: {len(result)}")
    print(f"PASS: {(result['status'] == 'PASS').sum()}; FAIL: {len(failed)}")
    if len(failed):
        print(failed[["check_id", "evidence"]].to_string(index=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
