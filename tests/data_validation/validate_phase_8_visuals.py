"""Independent validation gate for Phase 8 visualization artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"
RESULT_PATH = TABLE_DIR / "phase_8_visual_validation_results.csv"
MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_8_visualization_manifest.json"
PHASE7_MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_7_business_analysis_manifest.json"

APPROVED_KPIS = {
    "Observed Stable-Category Product Count",
    "Eligible Favorite-Movement Product Count",
    "Positive Favorite-Movement Breadth",
    "Median Daily Favorite Movement per Product",
    "Evidence Sufficiency Tier",
}
EXPECTED_VISUAL_IDS = {f"V{i:02d}" for i in range(1, 7)}
EXPECTED_PAGES = {"Category Engagement Overview", "Category Evidence Deep Dive", "Evidence & Limitations"}
EXPECTED_SCENARIOS = {
    "PRIMARY_EXACT_PRODUCT",
    "COMPACT_INCLUSIVE_PRODUCT",
    "OUTLIER_EXCLUDED_PRODUCT",
    "INTERVAL_WEIGHTED_EXACT",
}
EXPECTED_CATEGORIES = {
    "Automotive", "Baby & Kids", "Entertainment & Hobbies", "Fashion",
    "Groceries & Pets", "Health & Beauty", "Home", "Mobile & Technology",
    "Others", "Sports & Outdoor", "Tickets & Vouchers", "Travel",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    results: list[dict[str, Any]] = []

    def check(check_id: str, area: str, condition: bool, expected: str, actual: Any, note: str) -> None:
        results.append(
            {
                "check_id": check_id,
                "validation_area": area,
                "status": "PASS" if bool(condition) else "FAIL",
                "expected": expected,
                "actual": str(actual),
                "validation_note": note,
            }
        )

    required = {
        "visual_spec": TABLE_DIR / "phase_8_visual_specification.csv",
        "dashboard_spec": TABLE_DIR / "phase_8_dashboard_specification.csv",
        "visual_qa": TABLE_DIR / "phase_8_visual_qa.csv",
        "category": TABLE_DIR / "phase_7_category_business_analysis.csv",
        "comparison": TABLE_DIR / "phase_7_category_comparison.csv",
        "sensitivity": TABLE_DIR / "phase_7_sensitivity_analysis.csv",
        "phase6_kpis": TABLE_DIR / "phase_6_kpi_specification.csv",
        "manifest": MANIFEST_PATH,
        "phase7_manifest": PHASE7_MANIFEST_PATH,
    }
    for index, (name, path) in enumerate(required.items(), start=1):
        check(f"P8-F{index:02d}", "Required artifacts", path.exists(), "file exists", path.relative_to(ROOT), name)
    if any(row["status"] == "FAIL" for row in results):
        pd.DataFrame(results).to_csv(RESULT_PATH, index=False, lineterminator="\n")
        raise SystemExit("Phase 8 validation failed: required artifact missing.")

    spec = pd.read_csv(required["visual_spec"])
    dashboard = pd.read_csv(required["dashboard_spec"])
    qa = pd.read_csv(required["visual_qa"])
    category = pd.read_csv(required["category"])
    comparison = pd.read_csv(required["comparison"])
    sensitivity = pd.read_csv(required["sensitivity"])
    phase6 = pd.read_csv(required["phase6_kpis"])
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    phase7_manifest = json.loads(PHASE7_MANIFEST_PATH.read_text(encoding="utf-8"))

    check("P8-S01", "Visual inventory", len(spec) == 6, "6 core visuals", len(spec), "One row per governed visual")
    check("P8-S02", "Visual inventory", set(spec["visual_id"]) == EXPECTED_VISUAL_IDS, str(sorted(EXPECTED_VISUAL_IDS)), sorted(spec["visual_id"]), "Stable visual identifiers")
    required_spec_columns = {
        "visual_id", "visual_title", "business_question_answered", "chart_type", "x_axis", "y_axis",
        "category_or_series", "measures_used", "filters", "sorting", "tooltip_fields", "evidence_treatment",
        "missing_value_treatment", "why_appropriate", "potential_misinterpretation", "design_safeguards",
        "power_bi_visual", "source_table", "figure_file",
    }
    check("P8-S03", "Visual inventory", required_spec_columns.issubset(spec.columns), "all required specification columns", sorted(spec.columns), "Formal chart contract completeness")
    check("P8-S04", "Visual inventory", spec["figure_file"].nunique() == 6, "6 unique figure files", spec["figure_file"].nunique(), "No duplicate visual artifact")
    check("P8-S05", "Terminology", spec["visual_title"].str.contains("Level-2", case=False, na=False).sum() == 0, "0 business-facing Level-2 titles", int(spec["visual_title"].str.contains("Level-2", case=False, na=False).sum()), "Use Broad Product Category terminology")

    approved = set(phase6.loc[phase6["status"].str.startswith("APPROVED"), "kpi_name"])
    check("P8-K01", "KPI governance", approved == APPROVED_KPIS, str(sorted(APPROVED_KPIS)), sorted(approved), "Phase 6 KPI set remains frozen")
    measure_text = " ".join(spec["measures_used"].astype(str)).lower()
    for idx, blocked in enumerate(["total_sold", "total_rating", "revenue", "orders", "conversion", "composite"], start=2):
        check(f"P8-K{idx:02d}", "KPI governance", blocked not in measure_text, f"{blocked} absent from visual measures", blocked in measure_text, "Blocked metric safeguard")
    check("P8-K08", "KPI governance", spec["measures_used"].str.contains("Positive Favorite-Movement Breadth").any(), "breadth included", True, "Governed breadth KPI present")
    check("P8-K09", "KPI governance", spec["measures_used"].str.contains("Median Daily Favorite Movement per Product").any(), "median movement included", True, "Governed magnitude KPI present")
    check("P8-K10", "KPI governance", not spec["visual_title"].str.contains("momentum score", case=False, na=False).any(), "no composite score title", False, "No score framing")

    check("P8-D01", "Governed data", len(category) == 12 and set(category["broad_product_category"]) == EXPECTED_CATEGORIES, "12 governed Broad Product Categories", sorted(category["broad_product_category"]), "All broad groups retained; no Level-2 publication rows")
    tier_counts = category["evidence_sufficiency_tier"].value_counts().to_dict()
    check("P8-D02", "Governed data", tier_counts == {"MODERATE": 4, "INSUFFICIENT": 4, "HIGH": 4}, "HIGH=4; MODERATE=4; INSUFFICIENT=4", tier_counts, "Evidence distribution")
    insufficient = category["evidence_sufficiency_tier"].eq("INSUFFICIENT")
    movement_fields = ["positive_favorite_movement_breadth", "median_daily_favorite_movement_per_product"]
    check("P8-D03", "Missing values", category.loc[insufficient, movement_fields].isna().all().all(), "all insufficient movement values blank", int(category.loc[insufficient, movement_fields].notna().sum().sum()), "No fake zero")
    check("P8-D04", "Missing values", int(insufficient.sum()) == 4, "4 N/A categories", int(insufficient.sum()), "Unranked universe")
    check("P8-D05", "Sensitivity", len(sensitivity) == 48, "48 category-scenario rows", len(sensitivity), "12 categories x 4 scenarios")
    check("P8-D06", "Sensitivity", set(sensitivity["sensitivity_scenario"]) == EXPECTED_SCENARIOS, str(sorted(EXPECTED_SCENARIOS)), sorted(sensitivity["sensitivity_scenario"].unique()), "All governed scenarios represented")
    primary = sensitivity.loc[sensitivity["sensitivity_scenario"].eq("PRIMARY_EXACT_PRODUCT"), ["broad_product_category", "positive_favorite_movement_breadth", "median_daily_favorite_movement"]]
    merged = category[["broad_product_category", "positive_favorite_movement_breadth", "median_daily_favorite_movement_per_product"]].merge(primary, on="broad_product_category", suffixes=("_category", "_sensitivity"))
    differences = (merged["positive_favorite_movement_breadth_category"] - merged["positive_favorite_movement_breadth_sensitivity"]).abs()
    check("P8-D07", "Sensitivity", differences.dropna().le(1e-9).all(), "primary values reconcile", float(differences.dropna().max()), "Primary exact result preserved")
    median_differences = (merged["median_daily_favorite_movement_per_product"] - merged["median_daily_favorite_movement"]).abs()
    check("P8-D07B", "Sensitivity", median_differences.dropna().le(1e-9).all(), "primary medians reconcile", float(median_differences.dropna().max()), "Primary exact median preserved")
    outlier = sensitivity.loc[sensitivity["sensitivity_scenario"].eq("OUTLIER_EXCLUDED_PRODUCT"), ["broad_product_category", "positive_favorite_movement_breadth"]]
    outlier_compare = primary.merge(outlier, on="broad_product_category", suffixes=("_primary", "_outlier"))
    outlier_diff = (outlier_compare["positive_favorite_movement_breadth_primary"] - outlier_compare["positive_favorite_movement_breadth_outlier"]).abs()
    published_names = set(category.loc[~insufficient, "broad_product_category"])
    unchanged = outlier_compare.loc[outlier_compare["broad_product_category"].isin(published_names)]
    unchanged_diff = (unchanged["positive_favorite_movement_breadth_primary"] - unchanged["positive_favorite_movement_breadth_outlier"]).abs()
    check("P8-D08", "Sensitivity", unchanged_diff.le(1e-9).all(), "8 published categories unchanged under outlier exclusion", int(unchanged_diff.gt(1e-9).sum()), "Phase 7 finding retained")

    missing_notes = " ".join(spec["missing_value_treatment"].astype(str)).lower()
    check("P8-M01", "Missing values", "never plotted as zero" in missing_notes or "never plotted" in missing_notes, "explicit no-fake-zero rule", missing_notes[:160], "Missingness is semantic, not formatting")
    check("P8-M02", "Evidence semantics", spec.loc[spec["visual_id"].eq("V02"), "design_safeguards"].str.contains("not performance", case=False).all(), "evidence not performance safeguard", True, "Evidence tier is not an outcome")
    check("P8-M03", "Primary treatment", spec.loc[spec["visual_id"].eq("V06"), "design_safeguards"].str.contains("Primary", case=False).all(), "primary explicitly foregrounded", True, "Sensitivities cannot replace primary")
    check("P8-M04", "Breadth denominator", spec.loc[spec["visual_id"].eq("V04"), "why_appropriate"].str.contains("breadth", case=False).all(), "breadth meaning explicit", True, "Breadth remains distinct from magnitude")
    check("P8-M05", "Magnitude meaning", spec.loc[spec["visual_id"].eq("V05"), "design_safeguards"].str.contains("two-stage median", case=False).all(), "two-stage median disclosed", True, "Magnitude grain preserved")

    check("P8-P01", "Dashboard plan", len(dashboard) == 3, "3 pages", len(dashboard), "Concise Power BI architecture")
    check("P8-P02", "Dashboard plan", set(dashboard["page_name"]) == EXPECTED_PAGES, str(sorted(EXPECTED_PAGES)), sorted(dashboard["page_name"]), "Required page flow")
    check("P8-P03", "Dashboard plan", dashboard["filters"].str.contains("every field", case=False, na=False).sum() == 0, "no indiscriminate slicers", 0, "Only useful interactions")
    check("P8-P04", "Dashboard plan", dashboard["limitations_footnote"].str.contains("sales|performance|claim", case=False, regex=True).all(), "limitations on every page", True, "Claim boundary remains visible")
    check("P8-P05", "Dashboard plan", dashboard.loc[dashboard["page_number"].eq(2), "filters"].str.contains("Single-select Broad Product Category", case=False).all(), "single category deep-dive selector", True, "Controlled denominator behavior")

    check("P8-Q01", "Visual QA", len(qa) == 6, "6 QA rows", len(qa), "One QA row per export")
    pass_columns = [c for c in qa.columns if c not in {"visual_id", "figure_file", "primary_vs_sensitivity_distinction", "manual_review_status", "qa_note"}]
    qa_failures = int((qa[pass_columns] != "PASS").sum().sum())
    check("P8-Q02", "Visual QA", qa_failures == 0, "all applicable automated QA fields PASS", qa_failures, "Structured visual review")
    check("P8-Q03", "Visual QA", qa["manual_review_status"].eq("PASS_VISUAL_QA").all(), "all exports manually reviewed", qa["manual_review_status"].value_counts().to_dict(), "Exact PNG inspection gate")
    check("P8-Q04", "Visual QA", qa.loc[qa["visual_id"].ne("V06"), "primary_vs_sensitivity_distinction"].eq("NOT_APPLICABLE").all(), "N/A only outside sensitivity visual", True, "QA semantics")
    check("P8-Q05", "Visual QA", qa.loc[qa["visual_id"].eq("V06"), "primary_vs_sensitivity_distinction"].eq("PASS").all(), "V06 primary distinction PASS", True, "Sensitivity legibility")

    min_width, min_height = 1500, 900
    figure_failures = []
    for row in spec.itertuples(index=False):
        path = FIGURE_DIR / row.figure_file
        if not path.exists():
            figure_failures.append(f"{row.visual_id}:missing")
            continue
        with Image.open(path) as image:
            width, height = image.size
        if width < min_width or height < min_height or path.stat().st_size < 50_000:
            figure_failures.append(f"{row.visual_id}:{width}x{height}:{path.stat().st_size}")
    check("P8-R01", "Rendered figures", not figure_failures, f"all PNGs >= {min_width}x{min_height} and >=50KB", figure_failures or "all pass", "Delivery-size export check")
    check("P8-R02", "Rendered figures", all((FIGURE_DIR / file).suffix.lower() == ".png" for file in spec["figure_file"]), "all PNG", sorted(set(Path(x).suffix for x in spec["figure_file"])), "Stable raster handoff")

    guardrails = manifest.get("guardrails", {})
    expected_false = ["composite_score_created", "sales_metric_created", "revenue_metric_created", "campaign_recommendation_created", "insufficient_categories_plotted_as_zero", "power_bi_dashboard_built", "upstream_artifacts_modified"]
    check("P8-G01", "Manifest guardrails", all(guardrails.get(key) is False for key in expected_false), "all blocked actions false", {key: guardrails.get(key) for key in expected_false}, "Phase scope retained")
    check("P8-G02", "Manifest guardrails", guardrails.get("primary_exact_result_remains_primary") is True, "primary exact remains primary", guardrails.get("primary_exact_result_remains_primary"), "Primary KPI rule")
    check("P8-G03", "Manifest", manifest.get("visual_count") == 6 and manifest.get("dashboard_page_count") == 3, "6 visuals and 3 pages", (manifest.get("visual_count"), manifest.get("dashboard_page_count")), "Manifest inventory")
    check("P8-G04", "Manifest", manifest.get("manual_qa_status") == "PASS_VISUAL_QA", "PASS_VISUAL_QA", manifest.get("manual_qa_status"), "Release review recorded")

    phase7_hash_failures = []
    phase7_records = {}
    phase7_records.update(phase7_manifest.get("output_tables", {}))
    phase7_records.update(phase7_manifest.get("figures", {}))
    for record in phase7_records.values():
        path = ROOT / record["path"]
        if not path.exists() or sha256(path) != record["sha256"]:
            phase7_hash_failures.append(record["path"])
    check("P8-H01", "Upstream integrity", not phase7_hash_failures, "all Phase 7 outputs unchanged", phase7_hash_failures or "all hashes match", "Phase 7 immutable input gate")

    phase4_hash_failures = []
    for record in phase7_manifest.get("input_tables", {}).values():
        path = ROOT / record["path"]
        if not path.exists() or sha256(path) != record["sha256"]:
            phase4_hash_failures.append(record["path"])
    check("P8-H02", "Upstream integrity", not phase4_hash_failures, "all Phase 4 analytical tables unchanged", phase4_hash_failures or "all hashes match", "Phase 4 immutability")

    phase6_hash_failures = []
    for record in phase7_manifest.get("phase6_specification_inputs", {}).values():
        path = ROOT / record["path"]
        if not path.exists() or sha256(path) != record["sha256"]:
            phase6_hash_failures.append(record["path"])
    check("P8-H03", "Upstream integrity", not phase6_hash_failures, "all Phase 6 specification inputs unchanged", phase6_hash_failures or "all hashes match", "KPI governance immutability")
    check("P8-H04", "Input lineage", all(sha256(ROOT / record["path"]) == record["sha256"] for record in manifest["input_artifacts"].values()), "all manifest inputs hash-match", True, "Phase 8 provenance")

    output = pd.DataFrame(results)
    output.to_csv(RESULT_PATH, index=False, lineterminator="\n")
    failures = output.loc[output["status"].eq("FAIL")]
    print(f"Phase 8 validation: {int((output['status'] == 'PASS').sum())}/{len(output)} checks passed.")
    if not failures.empty:
        print(failures[["check_id", "validation_area", "actual"]].to_string(index=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
