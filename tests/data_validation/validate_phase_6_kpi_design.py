"""Independent validation gate for Phase 6 KPI governance artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "outputs" / "tables"
MANIFEST_PATH = ROOT / "outputs" / "analysis_results" / "phase_6_kpi_design_manifest.json"
RESULT_PATH = TABLE_DIR / "phase_6_kpi_design_validation_results.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    checks: list[dict[str, str]] = []

    def check(check_id: str, area: str, condition: bool, evidence: str) -> None:
        checks.append({
            "check_id": check_id,
            "area": area,
            "status": "PASS" if condition else "FAIL",
            "evidence": evidence,
        })

    required_paths = [
        ROOT / "docs" / "kpi_definitions.md",
        ROOT / "docs" / "business_question_governance.md",
        TABLE_DIR / "phase_6_kpi_specification.csv",
        TABLE_DIR / "phase_6_kpi_validation_rules.csv",
        TABLE_DIR / "phase_6_kpi_dependency_map.csv",
        TABLE_DIR / "phase_6_category_eligibility_rules.csv",
        ROOT / "reports" / "phase_6_kpi_design_report.md",
        ROOT / "src" / "analysis" / "build_phase_6_kpi_specs.py",
        MANIFEST_PATH,
    ]
    for path in required_paths:
        check(f"P6-A-{path.stem}", "artifact", path.exists() and path.stat().st_size > 0, str(path.relative_to(ROOT)))

    spec = pd.read_csv(TABLE_DIR / "phase_6_kpi_specification.csv")
    validations = pd.read_csv(TABLE_DIR / "phase_6_kpi_validation_rules.csv")
    dependencies = pd.read_csv(TABLE_DIR / "phase_6_kpi_dependency_map.csv")
    eligibility = pd.read_csv(TABLE_DIR / "phase_6_category_eligibility_rules.csv")

    required_spec_columns = {
        "kpi_name", "status", "business_question", "business_definition", "formula",
        "unit_of_analysis", "grain", "source_table", "source_fields", "numerator",
        "denominator", "eligibility_rule", "exclusion_rule", "minimum_sample_rule",
        "approximate_value_rule", "outlier_rule", "category_change_rule",
        "missing_value_rule", "insufficient_evidence_behavior", "interpretation",
        "limitation", "power_bi_implementation_notes", "validation_rule",
        "filter_behavior", "denominator_behavior", "date_behavior",
        "category_behavior", "blank_handling",
    }
    check("P6-S-schema", "KPI specification", required_spec_columns <= set(spec.columns), f"columns={len(spec.columns)}")
    check("P6-S-count", "KPI specification", len(spec) == 5 and spec["kpi_name"].nunique() == 5, f"rows={len(spec)}")
    check("P6-S-complete", "KPI specification", not spec[list(required_spec_columns)].isna().any().any(), "required cells nonblank")
    check("P6-S-formulas", "KPI specification", spec["formula"].str.strip().ne("").all(), "five explicit formulas")
    check("P6-S-grains", "KPI specification", spec["grain"].str.contains("Broad Product Category", regex=False).all(), "all grains state Broad Product Category")
    check("P6-S-powerbi", "KPI specification", spec["power_bi_measure_name"].notna().all() and spec["power_bi_implementation_notes"].notna().all(), "measure names and notes complete")

    approved_names = " ".join(spec["kpi_name"].str.lower())
    prohibited_names = ["sales", "revenue", "orders", "aov", "customers", "conversion", "campaign", "momentum score"]
    check("P6-G-no-prohibited-kpi", "safeguards", not any(term in approved_names for term in prohibited_names), approved_names)
    source_fields = " ".join(spec["source_fields"].str.lower())
    check("P6-G-no-blocked-source", "safeguards", "total_sold" not in source_fields and "total_rating" not in source_fields, "blocked counters absent from KPI source fields")
    check("P6-G-no-composite", "safeguards", not spec["kpi_name"].str.contains("composite|score", case=False, regex=True).any(), "no composite KPI")

    breadth = spec.loc[spec["kpi_name"].eq("Positive Favorite-Movement Breadth")].iloc[0]
    check("P6-G-product-breadth", "breadth governance", breadth["unit_of_analysis"] == "product" and "including zero and negative" in breadth["denominator"], breadth["denominator"])
    check("P6-G-exact-primary", "favorite governance", spec.loc[spec["kpi_name"].str.contains("Favorite") | spec["kpi_name"].str.contains("Evidence"), "approximate_value_rule"].str.contains("exact", case=False).all(), "exact primary stated")
    check("P6-G-category-change", "category governance", spec["category_change_rule"].str.contains("exclude", case=False).all(), "every KPI has explicit category-change exclusion")
    check("P6-G-outliers", "outlier governance", spec["outlier_rule"].notna().all(), "every KPI has an outlier rule")
    check("P6-G-missing", "missing governance", spec["missing_value_rule"].notna().all(), "every KPI has a missing-value rule")

    check("P6-V-count", "validation specification", len(validations) >= len(spec), f"rules={len(validations)}")
    covered = set(spec["kpi_name"]) - {"Evidence Sufficiency Tier"}
    covered -= set(validations["kpi_name"])
    check("P6-V-coverage", "validation specification", not covered, f"uncovered={sorted(covered)}")
    check("P6-V-zero", "validation specification", validations["zero_denominator_behavior"].notna().all(), "zero-denominator behavior complete")
    check("P6-V-examples", "validation specification", validations["test_type"].eq("worked example").sum() >= 2, "breadth and median worked examples")

    check("P6-D-count", "dependency map", len(dependencies) >= 10, f"rows={len(dependencies)}")
    blocked = dependencies.loc[dependencies["raw_field"].isin(["total_sold", "total_rating"])]
    check("P6-D-blocked", "dependency map", len(blocked) == 2 and blocked["base_calculation"].eq("BLOCKED").all() and blocked["kpi_name"].eq("No KPI").all(), "sold/rating dependency paths blocked")
    check("P6-E-tier-rules", "eligibility rules", {"HIGH evidence", "MODERATE evidence", "INSUFFICIENT evidence"} <= set(eligibility["scope"]), "three evidence tiers defined")
    check("P6-E-no-recommendation", "eligibility rules", eligibility["rule_id"].eq("P6-E14").any(), "campaign decision explicitly blocked")

    governance = (ROOT / "docs" / "business_question_governance.md").read_text(encoding="utf-8")
    kpi_doc = (ROOT / "docs" / "kpi_definitions.md").read_text(encoding="utf-8")
    report = (ROOT / "reports" / "phase_6_kpi_design_report.md").read_text(encoding="utf-8")
    for component in ["A. “categories”", "B. “gaining momentum”", "C. “fastest”", "D. “on the platform”", "E. “prioritize featuring”", "F. “upcoming campaigns and collections”"]:
        check(f"P6-Q-{ord(component[0])}", "question governance", component in governance, component)
    final_question = spec["business_question"].iloc[0]
    check("P6-Q-final", "question governance", spec["business_question"].nunique() == 1 and final_question in governance and final_question in kpi_doc and final_question in report, final_question)
    check("P6-Q-claims", "question governance", "Claims the dashboard must not make" in governance and "Legitimate dashboard claims" in governance, "allowed and prohibited claims documented")

    phase4_manifest_path = ROOT / "outputs" / "analysis_results" / "phase_4_transformation_manifest.json"
    phase4_manifest = json.loads(phase4_manifest_path.read_text(encoding="utf-8"))
    changed_phase4 = []
    for name, metadata in phase4_manifest["tables"].items():
        path = ROOT / metadata["path"]
        if sha256(path) != metadata["sha256"]:
            changed_phase4.append(name)
    check("P6-I-phase4-immutable", "input integrity", not changed_phase4, f"changed={changed_phase4}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    output_mismatches = []
    for metadata in manifest["outputs"].values():
        path = ROOT / metadata["path"]
        if sha256(path) != metadata["sha256"]:
            output_mismatches.append(metadata["path"])
    check("P6-R-manifest", "reproducibility", not output_mismatches, f"hash mismatches={output_mismatches}")
    check("P6-R-safeguards", "reproducibility", (
        manifest["safeguards"]["total_sold_blocked"]
        and manifest["safeguards"]["total_rating_blocked"]
        and not manifest["safeguards"]["sales_kpi_created"]
        and not manifest["safeguards"]["revenue_kpi_created"]
        and not manifest["safeguards"]["composite_score_created"]
        and not manifest["safeguards"]["category_ranking_created"]
        and not manifest["safeguards"]["campaign_recommendation_created"]
    ), str(manifest["safeguards"]))

    status_text = (ROOT / "docs" / "project_status.md").read_text(encoding="utf-8")
    phase6_complete = bool(re.search(r"\| 6 \| Business Questions & KPI Design \| COMPLETED \|", status_text))
    phase7_review = bool(re.search(r"\| 7 \| Business Analysis \| REVIEW REQUIRED \|", status_text))
    check("P6-STATUS-6", "phase status", phase6_complete, "Phase 6 COMPLETED after passing its gate")
    check("P6-STATUS-7", "phase status", phase7_review, "Phase 7 REVIEW REQUIRED")

    result = pd.DataFrame(checks)
    temporary = RESULT_PATH.with_suffix(".csv.tmp")
    result.to_csv(temporary, index=False, encoding="utf-8", lineterminator="\n")
    temporary.replace(RESULT_PATH)
    failed = result.loc[result["status"].eq("FAIL")]
    print(f"Phase 6 validation checks: {len(result)}")
    print(f"PASS: {(result['status'] == 'PASS').sum()}; FAIL: {len(failed)}")
    if len(failed):
        print(failed[["check_id", "evidence"]].to_string(index=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
