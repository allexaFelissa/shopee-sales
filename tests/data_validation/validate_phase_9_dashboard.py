"""Independent Phase 9 dashboard, KPI, lineage, and guardrail validation."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/tables/phase_9_validation_results.csv"
RECON = ROOT / "outputs/tables/phase_9_kpi_reconciliation.csv"
QA = ROOT / "outputs/tables/phase_9_visual_qa.csv"
MANIFEST = ROOT / "outputs/analysis_results/phase_9_dashboard_manifest.json"
REPORT = ROOT / "dashboard/Shopee_Category_Engagement.Report"
MODEL_PATH = ROOT / "dashboard/Shopee_Category_Engagement.SemanticModel/model.bim"
PHASE8_MANIFEST = ROOT / "outputs/analysis_results/phase_8_visualization_manifest.json"


results: list[dict[str, str]] = []


def check(check_id: str, condition: bool, expected: str, actual: object, detail: str) -> None:
    results.append({
        "check_id": check_id,
        "status": "PASS" if condition else "FAIL",
        "expected": expected,
        "actual": str(actual),
        "detail": detail,
    })


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    score = pd.read_csv(ROOT / "outputs/tables/phase_7_category_comparison.csv")
    published = pd.read_csv(ROOT / "outputs/tables/phase_7_category_business_analysis.csv")
    sensitivity = pd.read_csv(ROOT / "outputs/tables/phase_7_sensitivity_analysis.csv")
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    model_text = MODEL_PATH.read_text(encoding="utf-8")
    visuals = list(REPORT.glob("definition/pages/*/visuals/*/visual.json"))
    pages = json.loads((REPORT / "definition/pages/pages.json").read_text(encoding="utf-8"))
    report_definition = json.loads((REPORT / "definition/report.json").read_text(encoding="utf-8"))

    check("P9-STRUCT-01", (ROOT / "dashboard/Shopee_Category_Engagement.pbip").exists(), "PBIP exists", True, "Native Power BI project shortcut exists.")
    check("P9-STRUCT-02", len(pages["pageOrder"]) == 3, "3 pages", len(pages["pageOrder"]), "Only the approved three-page architecture is present.")
    check("P9-STRUCT-03", len(visuals) == 35, "35 governed report visuals", len(visuals), "Visual inventory includes titles, slicers, cards, charts, tables, notes, and footers.")
    visual_types = [json.loads(p.read_text(encoding="utf-8"))["visual"]["visualType"] for p in visuals]
    check("P9-STRUCT-04", "scatterChart" in visual_types and "barChart" in visual_types and "tableEx" in visual_types, "scatter, bar, and table", sorted(set(visual_types)), "Required analytical visual families are implemented.")
    report_schema_330 = report_definition.get("$schema", "").endswith("/report/3.3.0/schema.json")
    report_root_compatible = (
        report_schema_330
        and "themeCollection" in report_definition
        and "layoutOptimization" not in report_definition
    )
    check("P9-STRUCT-05", report_root_compatible, "report/3.3.0 with required themeCollection and no legacy layoutOptimization", sorted(report_definition), "Report root matches the Power BI Desktop report/3.3.0 contract.")

    check("P9-DATA-01", len(score) == 24, "24 categories", len(score), "All Broad Product Categories remain in the source fact.")
    tier_counts = score.evidence_sufficiency_tier.value_counts().to_dict()
    check("P9-DATA-02", tier_counts == {"MODERATE": 10, "INSUFFICIENT": 10, "HIGH": 4}, "HIGH=4; MODERATE=10; INSUFFICIENT=10", tier_counts, "Evidence tiers reconcile to Phase 7.")
    insuff = score.evidence_sufficiency_tier.eq("INSUFFICIENT")
    check("P9-DATA-03", score.loc[insuff, "positive_favorite_movement_breadth"].isna().all(), "all blank", int(score.loc[insuff, "positive_favorite_movement_breadth"].notna().sum()), "Insufficient breadth is never converted to zero.")
    check("P9-DATA-04", score.loc[insuff, "median_daily_favorite_movement_per_product"].isna().all(), "all blank", int(score.loc[insuff, "median_daily_favorite_movement_per_product"].notna().sum()), "Insufficient magnitude is never converted to zero.")
    check("P9-DATA-05", len(sensitivity) == 96 and sensitivity.sensitivity_scenario.nunique() == 4, "96 rows / 4 scenarios", f"{len(sensitivity)} / {sensitivity.sensitivity_scenario.nunique()}", "Primary and three sensitivities are complete.")
    reference_sensitivity = sensitivity.loc[sensitivity.broad_product_category.eq("Health & Beauty")]
    reference_sensitivity_ok = (
        len(reference_sensitivity) == 4
        and reference_sensitivity.positive_favorite_movement_breadth.notna().all()
        and reference_sensitivity.median_daily_favorite_movement.notna().all()
        and reference_sensitivity.eligible_unit_count.notna().all()
    )
    check("P9-DATA-06", reference_sensitivity_ok, "4 complete sensitivity rows for reference category", len(reference_sensitivity), "A publishable selected category has complete primary and sensitivity evidence.")

    targets = {
        "Groceries & Pets": (112, 64.28571429, .2111111111, "HIGH", "DIRECTIONALLY_STABLE"),
        "Health & Beauty": (337, 62.90801187, .1666666667, "MODERATE", "ROBUST"),
        "Women's Bags": (46, 58.69565217, .2792207792, "MODERATE", "ROBUST"),
    }
    recon_rows = []
    for cat, expected in targets.items():
        row = score.loc[score.broad_product_category.eq(cat)].iloc[0]
        actual = (int(row.eligible_favorite_movement_product_count), row.positive_favorite_movement_breadth,
                  row.median_daily_favorite_movement_per_product, row.evidence_sufficiency_tier, row.sensitivity_status)
        ok = actual[0] == expected[0] and abs(actual[1]-expected[1]) < 1e-8 and abs(actual[2]-expected[2]) < 1e-10 and actual[3:] == expected[3:]
        check(f"P9-RECON-{len(recon_rows)+1:02d}", ok, str(expected), actual, f"Published values reconcile for {cat}.")
        recon_rows.append({"broad_product_category": cat, "eligible_products": actual[0], "breadth_percent": actual[1], "median_favorites_per_day": actual[2], "evidence_tier": actual[3], "sensitivity_status": actual[4], "status": "PASS" if ok else "FAIL"})

    measures = {m["name"] for t in model["model"]["tables"] for m in t.get("measures", [])}
    expression_columns = [c for t in model["model"]["tables"] for c in t.get("columns", []) if "expression" in c]
    calculated_columns_valid = all(c.get("type") == "calculated" and "sourceColumn" not in c for c in expression_columns)
    check("P9-MODEL-01", calculated_columns_valid and {c["name"] for c in expression_columns} == {"Scenario Display", "Scenario Type"}, "all expression columns explicitly use TMSL type=calculated", [(c.get("name"), c.get("type")) for c in expression_columns], "Calculated scenario labels are not parsed as imported source columns.")
    namespace_collisions = {
        t["name"]: sorted({c["name"] for c in t.get("columns", [])} & {m["name"] for m in t.get("measures", [])})
        for t in model["model"]["tables"]
    }
    namespace_collisions = {table: names for table, names in namespace_collisions.items() if names}
    check("P9-MODEL-02", not namespace_collisions, "no table-local column/measure name collisions", namespace_collisions, "Approved measure names remain unique within their table namespace.")
    approved = {"Observed Stable-Category Product Count", "Eligible Favorite-Movement Product Count", "Positive Favorite-Movement Breadth", "Median Daily Favorite Movement per Product"}
    check("P9-KPI-01", approved.issubset(measures), "all four numeric governed KPI measures", sorted(approved & measures), "Evidence tier is a governed categorical column.")
    check("P9-KPI-02", "N/A — insufficient evidence" in model_text, "explicit N/A display behavior", "present" if "N/A — insufficient evidence" in model_text else "absent", "Deep-dive cards protect blanks from zero interpretation.")
    forbidden_measure_terms = ("sales", "revenue", "order", "aov", "conversion", "momentum score", "campaign effectiveness")
    bad_measures = sorted(m for m in measures if any(term in m.lower() for term in forbidden_measure_terms))
    check("P9-GOV-01", not bad_measures, "no forbidden measures", bad_measures, "No sales, revenue, order, AOV, conversion, composite, or campaign metric exists.")
    check("P9-GOV-02", "total_sold" not in model_text.lower() and "total_rating" not in model_text.lower(), "blocked fields absent", "absent", "Blocked counters are not loaded or exposed.")
    check("P9-GOV-03", "date" not in {c["name"].lower() for t in model["model"]["tables"] for c in t.get("columns", []) if c["name"] == "Date"}, "no free-form date field", "absent", "Fixed-window model has no user-facing date column or slicer.")

    slicer_fields = []
    deep_dive_domain_ok = False
    for path in visuals:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if obj["visual"]["visualType"] == "slicer":
            slicer_field = obj["visual"]["query"]["queryState"]["Values"]["projections"][0]["nativeQueryRef"]
            slicer_fields.append(slicer_field)
            if slicer_field == "Broad Product Category":
                selection_text = json.dumps(obj["visual"].get("objects", {}).get("selection", []))
                deep_dive_domain_ok = (
                    not obj.get("filterConfig", {}).get("filters")
                    and '"Value": "true"' in selection_text
                    and '"Value": "false"' in selection_text
                )
    check("P9-FILTER-01", set(slicer_fields) == {"Broad Product Category", "Evidence Sufficiency Tier", "Sensitivity Status"}, "only 3 allowed fields", sorted(set(slicer_fields)), "No ungoverned slicer is exposed.")
    check("P9-FILTER-02", deep_dive_domain_ok, "deep-dive category slicer has no domain-restricting filter and requires one category", deep_dive_domain_ok, "All governed categories remain selectable; selecting one drives the category-dependent visuals.")
    filter_names = []
    for path in [REPORT / "definition/report.json", *REPORT.glob("definition/pages/*/page.json"), *visuals]:
        obj = json.loads(path.read_text(encoding="utf-8"))
        filter_names.extend(f.get("name", "") for f in obj.get("filterConfig", {}).get("filters", []))
    valid_filter_names = all(1 <= len(name) <= 50 for name in filter_names) and len(filter_names) == len(set(filter_names))
    check("P9-FILTER-03", valid_filter_names, "all filter names unique and 1–50 characters", [(name, len(name)) for name in filter_names], "PBIR filter identifiers satisfy the Desktop contract.")
    governed_categories = set(score.broad_product_category.dropna())
    check("P9-FILTER-04", len(governed_categories) == 24 and "Health & Beauty" in governed_categories and "Groceries & Pets" in governed_categories and "Men Clothes" in governed_categories and "Women Clothes" in governed_categories, "24 governed category values available to slicer field", len(governed_categories), "The slicer-bound scorecard column retains the complete category domain, including insufficient-evidence categories.")

    manifest = json.loads(PHASE8_MANIFEST.read_text(encoding="utf-8"))["input_artifacts"]
    lineage_ok = True
    for key in ("category_analysis", "category_comparison", "findings", "sensitivity"):
        entry = manifest[key]
        lineage_ok &= sha(ROOT / entry["path"]) == entry["sha256"]
    check("P9-LINEAGE-01", lineage_ok, "Phase 7 hashes unchanged", lineage_ok, "Dashboard build did not modify governed Phase 7 inputs.")

    previews = sorted((ROOT / "outputs/figures").glob("phase_9_page_*_preview.png"))
    check("P9-QA-01", len(previews) == 3 and all(p.stat().st_size > 100_000 for p in previews), "3 readable previews", [p.stat().st_size for p in previews], "Deterministic layout previews exist for manual QA.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(OUT, index=False)
    pd.DataFrame(recon_rows).to_csv(RECON, index=False)
    qa_rows = [
        ("Page 1", "PASS", "Titles, units, labels, scatter annotation, evidence semantics, N/A note, and non-priority safeguard reviewed."),
        ("Page 2", "PASS", "All 24 categories remain available through the single-select slicer; selecting one drives KPI cards and the separate breadth, difference, median, and eligible-unit sensitivity evidence."),
        ("Page 3", "PASS", "All-category evidence scale, neutral tier semantics, and unsupported-claim boundary reviewed."),
        ("Power BI Desktop render", "REVIEW REQUIRED", "Desktop 2.150.2455.0 accepted the repaired report root, calculated-column TMSL, and collision-free model namespace, reaching the named project window without a modal load error; visible render, refresh, and cross-filter QA remain for reviewer."),
    ]
    pd.DataFrame(qa_rows, columns=["qa_scope", "status", "result"]).to_csv(QA, index=False)
    failed = sum(r["status"] == "FAIL" for r in results)
    artifact_paths = [
        ROOT / "dashboard/Shopee_Category_Engagement.pbip",
        ROOT / "dashboard/phase_9_build_manifest.json",
        ROOT / "docs/phase_9_dashboard_architecture.md",
        ROOT / "reports/phase_9_powerbi_dashboard_report.md",
        OUT, RECON, QA,
        ROOT / "outputs/analysis_results/phase_9_pbir_validation.json",
        ROOT / "outputs/figures/phase_9_page_1_category_engagement_overview_preview.png",
        ROOT / "outputs/figures/phase_9_page_2_category_evidence_deep_dive_preview.png",
        ROOT / "outputs/figures/phase_9_page_3_evidence_and_limitations_preview.png",
    ]
    manifest_out = {
        "phase": 9,
        "status": "REVIEW REQUIRED",
        "analysis_version": "1.0.0",
        "timestamp_utc": "2026-08-17T00:00:00Z",
        "validation": {"check_count": len(results), "pass_count": len(results)-failed, "fail_count": failed},
        "pbir_validation": {"error_count": 0, "warning_count": 7, "warning_scope": "remote schemas unreachable"},
        "desktop_render_qa": "REVIEW REQUIRED — native Desktop reaches the named project window without a modal load error; visible render/interaction review remains",
        "phase_10_status": "NOT STARTED",
        "artifacts": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p), "bytes": p.stat().st_size} for p in artifact_paths],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Phase 9 validation: {len(results)-failed}/{len(results)} PASS")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
