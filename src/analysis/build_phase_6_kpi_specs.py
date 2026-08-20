"""Build the governed Phase 6 KPI specification artifacts.

This script reads Phase 5 evidence only to verify the basis for governance
decisions. It does not calculate category results, ranks, scores, or campaign
recommendations, and it never writes to data/raw or data/processed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "outputs" / "tables"
RESULT_DIR = ROOT / "outputs" / "analysis_results"

OUTPUTS = {
    "kpi_specification": TABLE_DIR / "phase_6_kpi_specification.csv",
    "validation_rules": TABLE_DIR / "phase_6_kpi_validation_rules.csv",
    "dependency_map": TABLE_DIR / "phase_6_kpi_dependency_map.csv",
    "eligibility_rules": TABLE_DIR / "phase_6_category_eligibility_rules.csv",
}
MANIFEST_PATH = RESULT_DIR / "phase_6_kpi_design_manifest.json"

FINAL_QUESTION = (
    "Which Broad Product Categories show stronger observed favorite-engagement "
    "movement among eligible repeatedly tracked listings in this 20-day sampled "
    "dataset, when breadth, typical per-day movement, sampled scale, and evidence "
    "sufficiency are reported separately?"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, encoding="utf-8", lineterminator="\n")
    temporary.replace(path)


def verify_phase_5_evidence() -> dict[str, object]:
    evidence_path = TABLE_DIR / "phase_5_category_evidence.csv"
    sensitivity_path = TABLE_DIR / "phase_5_engagement_sensitivity_by_category.csv"
    validation_path = TABLE_DIR / "phase_5_validation_results.csv"
    evidence = pd.read_csv(evidence_path)
    sensitivity = pd.read_csv(sensitivity_path)
    validation = pd.read_csv(validation_path)

    scenario_counts = sensitivity.groupby("sensitivity_scenario")["valid_unit_count"].sum()
    assertions = {
        "category_count": int(evidence["category_level_2"].nunique()),
        "all_valid_interval_count": int(scenario_counts["ALL_VALID_INTERVALS"]),
        "exact_interval_count": int(scenario_counts["EXACT_DISPLAY_INTERVALS_ONLY"]),
        "product_level_all_valid_count": int(scenario_counts["PRODUCT_LEVEL_MEDIAN_DAILY_CHANGE"]),
        "phase_5_failed_checks": int(validation["status"].ne("PASS").sum()),
    }
    expected = {
        "category_count": 24,
        "all_valid_interval_count": 3489,
        "exact_interval_count": 2603,
        "product_level_all_valid_count": 2919,
        "phase_5_failed_checks": 0,
    }
    if assertions != expected:
        raise RuntimeError(f"Phase 5 evidence changed: observed={assertions}, expected={expected}")
    return {
        **assertions,
        "exact_interval_retention_percent": round(2603 / 3489 * 100, 6),
        "phase_5_sources": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in (evidence_path, sensitivity_path, validation_path)
        },
    }


def build_kpi_specification() -> pd.DataFrame:
    common_question = FINAL_QUESTION
    rows = [
        {
            "kpi_name": "Observed Stable-Category Product Count",
            "status": "APPROVED_CONTEXT",
            "business_question": common_question,
            "business_definition": "Distinct sampled products assigned to the active Broad Product Category whose Level-2 membership is stable; a sample-scale descriptor, not platform assortment or market share.",
            "formula": "DISTINCTCOUNT(product_id) over snapshot rows where level2_category_changed_over_time_flag = FALSE and the snapshot is inside the active filter context.",
            "unit_of_analysis": "product",
            "grain": "Broad Product Category x active date window",
            "source_table": "data/processed/shopee_product_snapshots.csv",
            "source_fields": "product_id; observation_date; broad_product_category; category_level_2; level2_category_changed_over_time_flag",
            "numerator": "Distinct eligible product_id count",
            "denominator": "None (count)",
            "aggregation_method": "Distinct count after stable-category and filter rules",
            "eligibility_rule": "Product has at least one snapshot in context and never changes Level-2 category in the study history.",
            "exclusion_rule": "Exclude products with level2_category_changed_over_time_flag = TRUE; exclude missing category/date/product keys.",
            "minimum_sample_rule": "No suppression; always show the observed count, including zero.",
            "approximate_value_rule": "Not applicable; no favorite value enters this KPI.",
            "outlier_rule": "Not applicable; counts are not filtered by price or favorite outlier flags.",
            "category_change_rule": "Exclude every product that changes Level-2 category so products do not contribute to multiple governed category cohorts.",
            "missing_value_rule": "Rows missing a required key are ineligible; validated Phase 4 keys are expected complete.",
            "insufficient_evidence_behavior": "Display the count but never interpret it as performance; movement KPIs may still be blank.",
            "interpretation": "Size of the stable-category product sample represented in the selected context.",
            "limitation": "Reflects scraper coverage and can change with sampling; it is not platform product count or category share.",
            "power_bi_measure_name": "Observed Stable-Category Products",
            "power_bi_implementation_notes": "DISTINCTCOUNT on snapshots with stable-category filter; respect category/date filters; do not sum category counts into a platform estimate.",
            "validation_rule": "Result is a nonnegative integer and cannot exceed distinct stable-category products in the snapshot table under the same filters.",
        },
        {
            "kpi_name": "Eligible Favorite-Movement Product Count",
            "status": "APPROVED_CONTEXT",
            "business_question": common_question,
            "business_definition": "Distinct products contributing at least one exact-display, valid, positive-elapsed-day, stable-category favorite interval to a category.",
            "formula": "DISTINCTCOUNT(product_id) after primary interval eligibility; materialize one product-category row before category aggregation.",
            "unit_of_analysis": "product",
            "grain": "Broad Product Category x active date window",
            "source_table": "data/processed/shopee_matched_observations.csv",
            "source_fields": "product_id; previous_observation_date; current_observation_date; elapsed_days; current_broad_product_category; current_category_level_2; favorite_comparison_status; favorite_count_change_approx; level2_category_changed_over_time_flag",
            "numerator": "Distinct products with at least one eligible interval",
            "denominator": "None (count); becomes the denominator for product-level movement KPIs",
            "aggregation_method": "Distinct count after interval eligibility, with one row per product-category in the prepared fact",
            "eligibility_rule": "Both dates in context; elapsed_days > 0; favorite_comparison_status = VALID_EXACT_DISPLAY_VALUES; product never changes Level-2 category.",
            "exclusion_rule": "Exclude missing/invalid or compact favorite comparisons, cross-category products, nonpositive elapsed days, and boundary-crossing intervals.",
            "minimum_sample_rule": "Always display; fewer than 30 products forces INSUFFICIENT evidence and suppresses movement KPIs.",
            "approximate_value_rule": "Exact-display intervals only enter the primary count; compact/rounded intervals are excluded and counted separately in sensitivity coverage.",
            "outlier_rule": "Retain valid exact favorite endpoints in the primary count; outlier-endpoint exclusion is a mandatory sensitivity only.",
            "category_change_rule": "Exclude all intervals for any product whose Level-2 category changes during the study.",
            "missing_value_rule": "Missing prerequisites make the interval ineligible; never convert missing favorite values to zero.",
            "insufficient_evidence_behavior": "Show the count and assign INSUFFICIENT when reliability gates fail.",
            "interpretation": "The independent product-level evidence base for favorite movement.",
            "limitation": "Products with exact displays may differ systematically from products shown with compact values.",
            "power_bi_measure_name": "Eligible Favorite-Movement Products",
            "power_bi_implementation_notes": "Prefer a Phase 7 product-category movement fact; both interval endpoints must fall inside the selected date range.",
            "validation_rule": "Count is a nonnegative integer, is no larger than Observed Stable-Category Product Count, and reconciles to distinct eligible product_id values.",
        },
        {
            "kpi_name": "Positive Favorite-Movement Breadth",
            "status": "APPROVED_CORE",
            "business_question": common_question,
            "business_definition": "Share of eligible products whose median exact displayed favorite change per elapsed day is positive.",
            "formula": "100 * COUNT(product_median_daily_favorite_change > 0) / COUNT(eligible product-category rows).",
            "unit_of_analysis": "product",
            "grain": "Broad Product Category x active date window",
            "source_table": "Phase 7 product-category favorite-movement fact derived from data/processed/shopee_matched_observations.csv",
            "source_fields": "product_id; current_broad_product_category; current_category_level_2; elapsed_days; favorite_count_change_approx; favorite_comparison_status; level2_category_changed_over_time_flag; derived product_median_daily_favorite_change",
            "numerator": "Eligible products with product_median_daily_favorite_change > 0",
            "denominator": "All eligible products, including zero and negative product medians",
            "aggregation_method": "First median(change / elapsed_days) within product-category; then proportion positive across products",
            "eligibility_rule": "Use the Eligible Favorite-Movement Product Count cohort and one product-level median per category.",
            "exclusion_rule": "Exclude compact/missing/invalid comparisons, category-changing products, nonpositive elapsed days, and intervals crossing the date-filter boundary.",
            "minimum_sample_rule": "Display only for HIGH or MODERATE evidence; internal calculation may be retained to derive Wilson precision.",
            "approximate_value_rule": "Exact-display only for the primary KPI; all-valid exact+compact product-level breadth is a labeled directional sensitivity.",
            "outlier_rule": "Retain valid exact endpoints; compare with outlier-endpoint-excluded product-level sensitivity. Do not winsorize signs.",
            "category_change_rule": "Exclude all products with any Level-2 category change.",
            "missing_value_rule": "Missing values are excluded from eligibility, not treated as zero; a zero denominator returns blank.",
            "insufficient_evidence_behavior": "Return BLANK and show INSUFFICIENT evidence, never 0%.",
            "interpretation": "Breadth: how widely positive displayed-favorite movement is distributed across eligible products; it does not measure movement size.",
            "limitation": "Favorites are an engagement display, not sales or demand; exact-only selection reduces coverage and Wilson intervals are descriptive.",
            "power_bi_measure_name": "Positive Favorite-Movement Breadth %",
            "power_bi_implementation_notes": "Use one prepared product-category row per product; DIVIDE positive-product count by eligible-product count; return BLANK when evidence tier is INSUFFICIENT.",
            "validation_rule": "If 100 of 200 eligible products have positive product medians, result = 50%; valid range is 0% to 100%.",
        },
        {
            "kpi_name": "Median Daily Favorite Movement per Product",
            "status": "APPROVED_CORE",
            "business_question": common_question,
            "business_definition": "Typical product-level daily change in exact displayed favorites among eligible products.",
            "formula": "MEDIAN across eligible products of [MEDIAN within product-category of (favorite_count_change_approx / elapsed_days)].",
            "unit_of_analysis": "product",
            "grain": "Broad Product Category x active date window",
            "source_table": "Phase 7 product-category favorite-movement fact derived from data/processed/shopee_matched_observations.csv",
            "source_fields": "product_id; current_broad_product_category; current_category_level_2; elapsed_days; favorite_count_change_approx; favorite_comparison_status; level2_category_changed_over_time_flag; derived product_median_daily_favorite_change",
            "numerator": "Favorite count change at each eligible interval before elapsed-day normalization",
            "denominator": "Elapsed days at interval level; no ratio denominator at the final median aggregation",
            "aggregation_method": "Two-stage median: interval daily changes to product median, then product medians to category median",
            "eligibility_rule": "Same exact-display, stable-category product cohort as Positive Favorite-Movement Breadth.",
            "exclusion_rule": "Exclude compact/missing/invalid comparisons, category-changing products, nonpositive elapsed days, and boundary-crossing intervals.",
            "minimum_sample_rule": "Display only for HIGH or MODERATE evidence.",
            "approximate_value_rule": "Exact-display only for primary; all-valid exact+compact median is a labeled directional sensitivity.",
            "outlier_rule": "Keep valid exact values because IQR flags do not prove error; two-stage median is primary robustness. Require outlier-endpoint-excluded sensitivity.",
            "category_change_rule": "Exclude all products with any Level-2 category change.",
            "missing_value_rule": "Exclude ineligible intervals; do not impute; return blank for no eligible products.",
            "insufficient_evidence_behavior": "Return BLANK and show INSUFFICIENT evidence.",
            "interpretation": "Magnitude of movement for the typical eligible product; zero means the typical product showed no displayed daily change.",
            "limitation": "Per-day normalization assumes change accrued over the interval and does not reveal when it occurred; the 20-day window is short.",
            "power_bi_measure_name": "Median Daily Favorite Movement per Product",
            "power_bi_implementation_notes": "Materialize product medians upstream for auditable MEDIAN aggregation; do not average interval rates directly.",
            "validation_rule": "For product medians [-1, 0, 3], category result = 0; value must be finite when present and blank when evidence is insufficient.",
        },
        {
            "kpi_name": "Evidence Sufficiency Tier",
            "status": "APPROVED_GOVERNANCE",
            "business_question": common_question,
            "business_definition": "Transparent category/window classification based on calendar presence, eligible product count, and Wilson precision for product-level positive breadth.",
            "formula": "HIGH if dates=20 AND eligible_products>=100 AND Wilson95 width<=20pp; else MODERATE if dates>=15 AND eligible_products>=30 AND width<=35pp; else INSUFFICIENT.",
            "unit_of_analysis": "Broad Product Category",
            "grain": "Broad Product Category x active date window",
            "source_table": "data/processed/shopee_category_daily_coverage.csv plus Phase 7 product-category favorite-movement fact",
            "source_fields": "broad_product_category; observation_date; eligible product count; positive product count",
            "numerator": "Positive eligible products for the Wilson interval; observed dates for date coverage",
            "denominator": "Eligible products for Wilson precision; dates in active window for coverage",
            "aggregation_method": "Rule-based tier; no weights and no averaging of evidence dimensions",
            "eligibility_rule": "Tier is evaluated after primary exact-display and stable-category rules; Wilson interval uses product outcomes.",
            "exclusion_rule": "No category can bypass a failed gate because another evidence dimension is strong.",
            "minimum_sample_rule": "HIGH: 20 dates, n>=100, width<=20pp. MODERATE: >=15 dates, n>=30, width<=35pp. Otherwise INSUFFICIENT.",
            "approximate_value_rule": "Primary tier uses exact-display products; compact-inclusive sensitivity is disclosed separately and cannot upgrade the tier.",
            "outlier_rule": "Outlier sensitivity cannot upgrade the tier; a material sensitivity conflict adds a REVIEW flag beside the tier.",
            "category_change_rule": "Tier denominator excludes all Level-2-changing products.",
            "missing_value_rule": "Zero/missing eligible denominator or missing Wilson width yields INSUFFICIENT.",
            "insufficient_evidence_behavior": "Show INSUFFICIENT and suppress comparative movement KPIs; retain coverage counts.",
            "interpretation": "Whether the sample supports high-precision comparison, coarse directional comparison, or no comparative movement claim.",
            "limitation": "A tier measures evidence within this sample, not external validity, representativeness, or business importance.",
            "power_bi_measure_name": "Evidence Sufficiency Tier",
            "power_bi_implementation_notes": "Calculate in current date/category context; accompany with dates, n, Wilson bounds, and a separate sensitivity-conflict flag.",
            "validation_rule": "Allowed values are HIGH, MODERATE, INSUFFICIENT; n=100/dates=20/width=19pp => HIGH, while n=29 => INSUFFICIENT.",
        },
    ]
    frame = pd.DataFrame(rows)
    frame["filter_behavior"] = [
        "Respects active snapshot date and Level-2 category filters; stable-category exclusion is always enforced.",
        "Respects category/date filters; an interval is eligible only when both endpoints are inside the date context.",
        "Respects category/date filters through the prepared product fact; evidence suppression remains active.",
        "Respects category/date filters through the prepared product fact; evidence suppression remains active.",
        "Recomputes from the active category/date context; sensitivity filters cannot upgrade the primary tier.",
    ]
    frame["denominator_behavior"] = [
        "No denominator; return a distinct count.",
        "No displayed denominator; this count is the denominator for movement KPIs.",
        "Denominator is all eligible product rows, including positive, zero, and negative outcomes; never all snapshots or intervals.",
        "Elapsed days is the interval divisor; final aggregation is a median across one product value each.",
        "Wilson denominator is eligible products; calendar denominator is the active study-date set.",
    ]
    frame["date_behavior"] = [
        "Count products with at least one snapshot in the active date context; default is the full 20-day window.",
        "Require previous and current interval dates inside the active date context; default is the full 20-day window.",
        "Uses only product facts built from intervals with both endpoints in context; date filters trigger recomputation.",
        "Uses only product facts built from intervals with both endpoints in context; date filters trigger recomputation.",
        "Counts observed category dates in context; HIGH requires all 20 study dates and is unavailable in shorter selections.",
    ]
    frame["category_behavior"] = [
        "Group by validated Level-2 category and exclude products that ever change Level 2.",
        "Attribute only to the single stable Level-2 category of the product; no reassignment or cross-category interval.",
        "Calculate within stable Level-2 category; do not aggregate suppressed categories into an overall rank.",
        "Calculate within stable Level-2 category; do not aggregate suppressed categories into an overall rank.",
        "Evaluate separately for each Level-2 category; a strong category cannot compensate for another category's failed gate.",
    ]
    frame["blank_handling"] = [
        "No eligible products returns 0, not blank.",
        "No eligible products returns 0, not blank.",
        "Zero denominator or INSUFFICIENT evidence returns blank, never 0%.",
        "No eligible products or INSUFFICIENT evidence returns blank.",
        "Missing/zero eligible denominator returns INSUFFICIENT; Wilson bounds remain blank.",
    ]
    return frame


def build_validation_rules() -> pd.DataFrame:
    columns = [
        "validation_rule_id", "kpi_name", "test_type", "input_condition",
        "expected_result", "expected_range", "edge_case",
        "source_reconciliation", "zero_denominator_behavior",
    ]
    rows = [
        ("P6-V01", "Observed Stable-Category Product Count", "range", "Any filter context", "Nonnegative whole number", "0 to distinct stable products", "No rows => 0", "Recount distinct product_id from eligible snapshots", "Not applicable"),
        ("P6-V02", "Observed Stable-Category Product Count", "category change", "A product appears in two Level-2 categories", "Product excluded from both governed cohorts", "Not applicable", "All products stable => no exclusion", "Compare exclusion count with level2_category_changed_over_time_flag", "Not applicable"),
        ("P6-V03", "Eligible Favorite-Movement Product Count", "reconciliation", "Eligible interval fact exists", "Equals distinct eligible product_id within category/window", "0 to observed stable-category product count", "No eligible intervals => 0", "Distinct count from matched rows equals prepared fact row count", "Not applicable"),
        ("P6-V04", "Eligible Favorite-Movement Product Count", "eligibility", "Compact or invalid endpoint appears", "Interval excluded from primary count", "Not applicable", "Exact value of zero remains eligible", "All primary rows have VALID_EXACT_DISPLAY_VALUES and elapsed_days > 0", "Not applicable"),
        ("P6-V05", "Positive Favorite-Movement Breadth", "worked example", "100 positive products; 200 eligible products", "50%", "0% to 100%", "Zero/negative products remain in denominator", "Positive + zero + negative product counts = eligible count", "Return BLANK"),
        ("P6-V06", "Positive Favorite-Movement Breadth", "boundary", "0 positive; 30 eligible; MODERATE evidence", "0%", "0% to 100%", "All positive => 100%", "Numerator cannot exceed denominator", "Return BLANK"),
        ("P6-V07", "Positive Favorite-Movement Breadth", "suppression", "Evidence tier = INSUFFICIENT", "Displayed KPI is BLANK", "Blank or 0%-100% when sufficient", "Internal proportion may exist for tier precision", "Tier and display behavior reconcile", "Return BLANK, never 0%"),
        ("P6-V08", "Median Daily Favorite Movement per Product", "worked example", "Product medians are -1, 0, 3", "0", "Finite number when present", "Even n uses standard median midpoint", "Recompute product medians then category median", "Return BLANK"),
        ("P6-V09", "Median Daily Favorite Movement per Product", "grain", "One product has three intervals and another has one", "Each product contributes one median", "Not applicable", "Duplicate product-category rows are impossible", "Prepared fact key product_id + category + window is unique", "Return BLANK"),
        ("P6-V10", "Median Daily Favorite Movement per Product", "elapsed time", "elapsed_days <= 0 or missing", "Interval excluded", "Finite daily changes only", "Elapsed_days = 1 is eligible", "No eligible row has elapsed_days <= 0", "Return BLANK"),
        ("P6-V11", "Evidence Sufficiency Tier", "high tier", "dates=20; n=100; Wilson width=19pp", "HIGH", "HIGH/MODERATE/INSUFFICIENT", "Any failed HIGH gate falls through", "Recompute all three gates independently", "INSUFFICIENT"),
        ("P6-V12", "Evidence Sufficiency Tier", "moderate tier", "dates=15; n=30; Wilson width=34pp", "MODERATE", "HIGH/MODERATE/INSUFFICIENT", "dates=14 or n=29 or width>35pp => INSUFFICIENT", "Recompute all three gates independently", "INSUFFICIENT"),
        ("P6-V13", "Evidence Sufficiency Tier", "zero denominator", "n=0", "INSUFFICIENT and Wilson bounds blank", "HIGH/MODERATE/INSUFFICIENT", "No division error", "Eligible count reconciles to zero", "INSUFFICIENT"),
        ("P6-V14", "Evidence Sufficiency Tier", "Wilson", "positive=50; n=100", "Wilson bounds approximately 40.38%-59.62%; width approximately 19.25pp", "0-100 bounds; nonnegative width", "positive cannot exceed n", "Independent Wilson score implementation with z=1.96", "INSUFFICIENT"),
        ("P6-V15", "All movement KPIs", "date filters", "Selected window excludes either interval endpoint", "Interval excluded", "Not applicable", "Full 20-day default includes both endpoints", "Previous and current dates both satisfy date context", "Counts 0; rates/medians BLANK"),
        ("P6-V16", "All movement KPIs", "approximate sensitivity", "All-valid sensitivity includes compact displays", "Primary exact-only result unchanged", "Not applicable", "Sensitivity may be blank", "Primary and sensitivity cohorts have separate flags/counts", "No effect on primary"),
        ("P6-V17", "All movement KPIs", "outlier sensitivity", "Favorite outlier endpoint excluded in sensitivity", "Primary remains unchanged; sensitivity is separately labeled", "Not applicable", "No movement => concentration may be blank", "Endpoint flags reconcile to snapshot lineage", "No effect on primary"),
        ("P6-V18", "Phase 6 safeguard", "prohibited metrics", "Specification inventory", "No approved sales, revenue, orders, AOV, customers, conversion, campaign-effectiveness, or composite momentum KPI", "Zero prohibited approved KPIs", "total_sold and total_rating absent from source_fields", "Search specification and dependency outputs", "Not applicable"),
    ]
    return pd.DataFrame(rows, columns=columns)


def build_dependency_map() -> pd.DataFrame:
    columns = [
        "dependency_id", "raw_field", "validated_field", "analytical_table",
        "base_calculation", "kpi_name", "business_interpretation", "governance_note",
    ]
    rows = [
        ("P6-D01", "id", "product_id", "shopee_product_snapshots.csv", "Distinct stable-category products", "Observed Stable-Category Product Count", "Observed sample scale", "Not platform assortment"),
        ("P6-D02", "item_category_detail", "category_level_2 + product_category_level2_change_flag", "shopee_product_snapshots.csv", "Exclude products with any Level-2 change", "Observed Stable-Category Product Count", "Stable broad-category cohort", "Level 2 only; no silent reassignment"),
        ("P6-D03", "w_date", "observation_date", "shopee_category_daily_coverage.csv", "Count observed dates in active window", "Evidence Sufficiency Tier", "Calendar presence", "Presence does not correct uneven volume"),
        ("P6-D04", "favorite", "favorite_parsed + favorite_parse_status + compact flag", "shopee_matched_observations.csv", "Require exact valid displays at both endpoints", "Eligible Favorite-Movement Product Count", "Exact-display movement evidence", "Compact values excluded from primary"),
        ("P6-D05", "id + w_date", "previous/current observation dates + observation interval days", "shopee_matched_observations.csv", "Consecutive matched interval with elapsed_days > 0 and both dates in context", "Eligible Favorite-Movement Product Count", "Repeated tracking evidence", "Irregular gaps retained"),
        ("P6-D06", "favorite + w_date", "favorite_count_change_approx + elapsed_days", "shopee_matched_observations.csv", "favorite change / elapsed days", "Median Daily Favorite Movement per Product", "Interval-normalized displayed engagement movement", "Change timing within interval is unknown"),
        ("P6-D07", "id + favorite", "product_id + eligible interval daily changes", "Phase 7 product-category favorite-movement fact", "Median eligible daily change within product", "Positive Favorite-Movement Breadth", "One outcome per product", "Prevents interval-heavy products dominating"),
        ("P6-D08", "id + favorite", "product_id + eligible interval daily changes", "Phase 7 product-category favorite-movement fact", "Median eligible daily change within product", "Median Daily Favorite Movement per Product", "Typical product movement", "Two-stage median"),
        ("P6-D09", "favorite", "positive product outcome", "Phase 7 product-category favorite-movement fact", "Positive products / eligible products + Wilson 95% interval", "Positive Favorite-Movement Breadth", "Breadth, not magnitude", "Zero and negative products remain in denominator"),
        ("P6-D10", "favorite", "positive product outcome", "Phase 7 product-category favorite-movement fact", "Wilson width plus dates and eligible n", "Evidence Sufficiency Tier", "Comparison precision within sample", "Not external representativeness"),
        ("P6-D11", "favorite", "favorite_statistical_outlier_flag", "shopee_product_snapshots.csv joined by source row", "Exclude flagged endpoints in sensitivity only", "All movement KPIs", "Outlier robustness diagnostic", "Flags do not prove invalidity"),
        ("P6-D12", "favorite", "compact favorite flag", "shopee_matched_observations.csv", "All-valid exact+compact product-level sensitivity", "All movement KPIs", "Directional sensitivity", "Never replaces exact-only primary"),
        ("P6-D13", "total_sold", "total_sold_metric_status", "Excluded from Phase 4 movement interfaces", "BLOCKED", "No KPI", "None", "UNVERIFIED_UNUSABLE_AS_SALES_METRIC"),
        ("P6-D14", "total_rating", "total_rating_metric_status", "Excluded from Phase 4 movement interfaces", "BLOCKED", "No KPI", "None", "UNVERIFIED_DUPLICATES_TOTAL_SOLD"),
    ]
    return pd.DataFrame(rows, columns=columns)


def build_eligibility_rules() -> pd.DataFrame:
    columns = ["rule_id", "scope", "rule_type", "condition", "action", "rationale"]
    rows = [
        ("P6-E01", "primary movement interval", "favorite validity", "favorite_comparison_status = VALID_EXACT_DISPLAY_VALUES", "Include", "Avoid treating compact/rounded endpoints as exact changes"),
        ("P6-E02", "primary movement interval", "time", "elapsed_days > 0 and both endpoints inside active date context", "Include", "Supports finite per-day normalization and consistent filter behavior"),
        ("P6-E03", "primary movement interval", "category", "level2_category_changed_over_time_flag = FALSE", "Include", "Creates mutually attributable stable Level-2 cohorts"),
        ("P6-E04", "product summary", "weighting", "At least one eligible interval in category/window", "Compute median daily change once per product", "Prevents products with more observations receiving more weight"),
        ("P6-E05", "breadth", "direction", "product median > 0 / = 0 / < 0", "Positive enters numerator; all three enter denominator", "Breadth measures participation, not net magnitude"),
        ("P6-E06", "primary values", "outliers", "Valid exact favorite endpoint is IQR-flagged", "Retain in primary; exclude in mandatory sensitivity", "IQR status is not proof of error; medians provide robustness"),
        ("P6-E07", "sensitivity", "approximate favorites", "Valid comparison contains a compact/rounded endpoint", "Include only in separately labeled all-valid product-level sensitivity", "Preserves coverage evidence without false precision"),
        ("P6-E08", "sensitivity", "interval weighting", "Eligible interval-level calculation", "Compare with product-level primary", "Detects dominance by frequently observed products"),
        ("P6-E09", "sensitivity", "material conflict", "Breadth differs by >10 percentage points, crosses 50%, or median direction changes under compact/outlier/interval sensitivity", "Set SENSITIVITY_REVIEW_REQUIRED; do not resolve with weights", "Makes consequential definition dependence visible"),
        ("P6-E10", "HIGH evidence", "tier", "20 observed dates AND >=100 eligible products AND Wilson width <=20pp", "Assign HIGH", "At n=100 the worst-case Wilson width is about 19.25pp; full short-window presence is required"),
        ("P6-E11", "MODERATE evidence", "tier", "Not HIGH; >=15 observed dates AND >=30 eligible products AND Wilson width <=35pp", "Assign MODERATE", "Allows coarse directional work with at least 75% calendar presence; n=30 worst-case width is about 33.7pp"),
        ("P6-E12", "INSUFFICIENT evidence", "tier", "Fails any MODERATE gate or denominator is zero", "Assign INSUFFICIENT; suppress movement KPIs", "Prevents sparse categories being compared as equally reliable"),
        ("P6-E13", "business follow-up", "decision gate", "HIGH evidence; Wilson lower bound >50%; median daily movement >0; no sensitivity conflict", "May label for further investigation only", "Requires breadth, magnitude, precision, and robustness without creating a campaign recommendation"),
        ("P6-E14", "campaign decision", "external evidence", "Any category passes analytical follow-up gate", "Do not recommend campaign priority without conversion, margin, inventory, campaign fit, and causal/outcome evidence", "Analytical traction proxy is insufficient for a campaign decision"),
    ]
    return pd.DataFrame(rows, columns=columns)


def assert_safeguards(specification: pd.DataFrame) -> None:
    required = {
        "kpi_name", "status", "business_question", "business_definition", "formula",
        "unit_of_analysis", "grain", "source_table", "source_fields", "numerator",
        "denominator", "eligibility_rule", "exclusion_rule", "minimum_sample_rule",
        "approximate_value_rule", "outlier_rule", "category_change_rule",
        "missing_value_rule", "insufficient_evidence_behavior", "interpretation",
        "limitation", "power_bi_implementation_notes", "validation_rule",
        "filter_behavior", "denominator_behavior", "date_behavior",
        "category_behavior", "blank_handling",
    }
    missing = required - set(specification.columns)
    if missing:
        raise RuntimeError(f"KPI specification missing required columns: {sorted(missing)}")
    prohibited = ("revenue", "orders", "aov", "customers", "conversion", "campaign effectiveness", "momentum score")
    approved_names = " ".join(specification["kpi_name"].str.lower())
    if any(term in approved_names for term in prohibited):
        raise RuntimeError("Prohibited KPI approved in Phase 6")
    if specification[list(required)].isna().any().any():
        raise RuntimeError("Required KPI specification cells cannot be blank")
    if specification["kpi_name"].duplicated().any():
        raise RuntimeError("KPI names must be unique")


def main() -> None:
    evidence = verify_phase_5_evidence()
    frames = {
        "kpi_specification": build_kpi_specification(),
        "validation_rules": build_validation_rules(),
        "dependency_map": build_dependency_map(),
        "eligibility_rules": build_eligibility_rules(),
    }
    assert_safeguards(frames["kpi_specification"])
    for name, frame in frames.items():
        write_csv(frame, OUTPUTS[name])

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "phase": 6,
        "status": "REVIEW_REQUIRED_AFTER_VALIDATION",
        "final_governed_question": FINAL_QUESTION,
        "phase_5_evidence": evidence,
        "outputs": {
            name: {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "rows": len(frames[name]),
                "columns": len(frames[name].columns),
                "sha256": sha256(path),
            }
            for name, path in OUTPUTS.items()
        },
        "safeguards": {
            "total_sold_blocked": True,
            "total_rating_blocked": True,
            "sales_kpi_created": False,
            "revenue_kpi_created": False,
            "composite_score_created": False,
            "category_ranking_created": False,
            "campaign_recommendation_created": False,
            "phase_4_data_modified": False,
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Phase 6 specification rows: {len(frames['kpi_specification'])}")
    print(f"Validation rules: {len(frames['validation_rules'])}")
    print("Category results, ranks, composite scores, and recommendations created: 0")


if __name__ == "__main__":
    main()
