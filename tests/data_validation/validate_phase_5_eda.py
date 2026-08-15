"""Independent validation gate for Phase 5 exploratory outputs."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd
from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "outputs/analysis_results/phase_5_eda_manifest.json"
RESULTS = ROOT / "outputs/tables/phase_5_validation_results.csv"
PHASE4_MANIFEST = ROOT / "outputs/analysis_results/phase_4_transformation_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []

    def add(self, check_id: str, area: str, condition: bool, evidence: str) -> None:
        self.rows.append({
            "check_id": check_id,
            "area": area,
            "status": "PASS" if condition else "FAIL",
            "evidence": evidence,
        })

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


def main() -> None:
    checks = Checks()
    phase4 = json.loads(PHASE4_MANIFEST.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # Inputs remain the exact validated Phase 4 artifacts.
    for name, expected in phase4["tables"].items():
        path = ROOT / expected["path"]
        actual = sha256(path)
        checks.add(f"P5-IN-{name}", "Phase 4 input integrity", actual == expected["sha256"], f"{expected['path']} SHA-256={actual}")

    expected_rows = {
        "descriptive_statistics": 14,
        "product_observation_distribution": 5,
        "interval_distribution": 19,
        "daily_coverage_diagnostics": 20,
        "category_evidence": 24,
        "price_sensitivity_by_category": 24,
        "engagement_sensitivity_by_category": 120,
        "category_change_impact": 4,
        "big_question_feasibility": 7,
        "figure_review": 12,
    }
    tables: dict[str, pd.DataFrame] = {}
    for name, expected in manifest["output_tables"].items():
        path = ROOT / expected["path"]
        frame = pd.read_csv(path, low_memory=False)
        tables[name] = frame
        condition = (
            sha256(path) == expected["sha256"]
            and len(frame) == expected_rows[name] == expected["rows"]
            and len(frame.columns) == expected["columns"]
        )
        checks.add(f"P5-OUT-{name}", "Output table integrity", condition, f"rows={len(frame)}, columns={len(frame.columns)}, SHA-256={sha256(path)}")

    evidence = tables["category_evidence"]
    daily = tables["daily_coverage_diagnostics"]
    product_dist = tables["product_observation_distribution"]
    interval_dist = tables["interval_distribution"]
    sensitivity = tables["engagement_sensitivity_by_category"]
    change = tables["category_change_impact"]
    feasibility = tables["big_question_feasibility"]

    checks.add("P5-REC-01", "Snapshot reconciliation", int(daily["sampled_snapshot_count"].sum()) == 20312 == int(evidence["sampled_snapshot_count"].sum()), "Daily and category snapshots both sum to 20,312.")
    checks.add("P5-REC-02", "Product reconciliation", int(product_dist["product_count"].sum()) == 16614, "Observation-frequency distribution sums to 16,614 products.")
    checks.add("P5-REC-03", "Matched interval reconciliation", int(interval_dist["interval_count"].sum()) == 3698 == int(evidence["matched_interval_count"].sum()), "Interval distribution and category evidence both sum to 3,698.")
    repeated = int(product_dist.loc[product_dist["observation_count"].gt(1), "product_count"].sum())
    checks.add("P5-REC-04", "Repeat-product reconciliation", repeated == 3070, f"Repeated products={repeated}; expected 3,070.")
    checks.add("P5-REC-05", "Date/category reconciliation", daily["observation_date"].nunique() == 20 and evidence["category_level_2"].nunique() == 24, "20 dates and 24 Level-2 categories represented.")

    all_valid = sensitivity.loc[sensitivity["sensitivity_scenario"].eq("ALL_VALID_INTERVALS")]
    direction_total = int(all_valid[["positive_unit_count", "zero_unit_count", "negative_unit_count"]].sum().sum())
    checks.add("P5-ENG-01", "Favorite denominator", int(all_valid["valid_unit_count"].sum()) == 3489 == direction_total, "3,489 valid favorite intervals reconcile to positive/zero/negative directions.")
    checks.add("P5-ENG-02", "Favorite directions", tuple(all_valid[["positive_unit_count", "zero_unit_count", "negative_unit_count"]].sum().astype(int)) == (1518, 1891, 80), "Positive=1,518; zero=1,891; negative=80.")
    exact = sensitivity.loc[sensitivity["sensitivity_scenario"].eq("EXACT_DISPLAY_INTERVALS_ONLY"), "valid_unit_count"].sum()
    stable = sensitivity.loc[sensitivity["sensitivity_scenario"].eq("LEVEL2_STABLE_INTERVALS_ONLY"), "valid_unit_count"].sum()
    no_outlier = sensitivity.loc[sensitivity["sensitivity_scenario"].eq("EXCLUDE_FAVORITE_OUTLIER_ENDPOINTS"), "valid_unit_count"].sum()
    checks.add("P5-ENG-03", "Sensitivity denominators", (int(exact), int(stable), int(no_outlier)) == (2603, 3480, 3006), f"Exact={int(exact)}, Level-2 stable={int(stable)}, no outlier endpoints={int(no_outlier)}.")
    wilson = all_valid[["positive_breadth_wilson_95_lower_percent", "positive_breadth_wilson_95_upper_percent"]].dropna()
    checks.add("P5-ENG-04", "Uncertainty bounds", bool(((wilson >= 0) & (wilson <= 100)).all().all()) and bool((wilson.iloc[:, 0] <= wilson.iloc[:, 1]).all()), "All reported Wilson bounds lie within 0–100 and lower <= upper.")

    level2 = change.loc[change["comparison_dimension"].eq("LEVEL2_STABILITY")].set_index("stability_group")
    full_path = change.loc[change["comparison_dimension"].eq("FULL_PATH_STABILITY")].set_index("stability_group")
    checks.add("P5-CAT-01", "Category-change sensitivity", int(level2.loc["STABLE", "matched_interval_count"]) == 3689 and int(level2.loc["CHANGED", "matched_interval_count"]) == 9, "Level-2 stable=3,689 and changed=9 matched intervals.")
    checks.add("P5-CAT-02", "Full-path sensitivity", int(full_path.loc["STABLE", "matched_interval_count"]) == 3678 and int(full_path.loc["CHANGED", "matched_interval_count"]) == 20, "Full-path stable=3,678 and changed=20 matched intervals.")

    prohibited = re.compile(r"(^|_)(revenue|aov|orders?|units_sold|sales_velocity|sales_growth|momentum_score|category_rank|campaign_priority)($|_)", re.I)
    violations = [(name, column) for name, frame in tables.items() for column in frame.columns if prohibited.search(column)]
    checks.add("P5-SAFE-01", "Unsupported metric safeguard", not violations, f"Prohibited output columns={violations}")
    safeguards = manifest["safeguards"]
    checks.add("P5-SAFE-02", "total_sold safeguard", safeguards["total_sold_status"] == "UNVERIFIED_UNUSABLE_AS_SALES_METRIC" and not safeguards["verified_sales_metric_created"], "total_sold remains blocked; no verified sales metric created.")
    checks.add("P5-SAFE-03", "Phase boundary", not any(safeguards[key] for key in ["revenue_metric_created", "final_kpi_created", "category_ranking_created", "momentum_score_created", "campaign_recommendation_created", "reframing_approved"]), "No Phase 6/final business outputs were created.")
    feasibility_map = feasibility.set_index("component")["phase_5_assessment"].to_dict()
    checks.add("P5-SAFE-04", "Question feasibility", feasibility_map["F"] == "NOT_DEFENSIBLY_ANSWERABLE" and feasibility_map["R"] == "CONDITIONALLY_SUPPORTABLE_REQUIRES_APPROVAL", "Original question unsupported; proposed reframing remains conditional and unapproved.")

    review = tables["figure_review"]
    checks.add("P5-VIS-01", "Visual review", review["review_status"].eq("PASS_EXPLORATORY_VISUAL_REVIEW").all(), "All 12 exact rendered PNGs recorded as visually reviewed.")
    for name, expected in manifest["figures"].items():
        path = ROOT / expected["path"]
        with Image.open(path) as picture:
            dimensions = picture.size
            variance = sum(ImageStat.Stat(picture.convert("RGB")).var)
        condition = sha256(path) == expected["sha256"] and min(dimensions) >= 700 and path.stat().st_size > 40000 and variance > 100
        checks.add(f"P5-FIG-{name}", "Figure integrity", condition, f"{dimensions[0]}x{dimensions[1]}, bytes={path.stat().st_size}, variance_sum={variance:.1f}")

    result = checks.frame()
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(RESULTS, index=False, lineterminator="\n")
    failed = result.loc[result["status"].eq("FAIL")]
    print(f"Phase 5 checks: {(result['status'] == 'PASS').sum()} passed, {len(failed)} failed")
    if len(failed):
        print(failed.to_string(index=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
