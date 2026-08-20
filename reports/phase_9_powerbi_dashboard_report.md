# Phase 9 — Power BI Dashboard Report

## Desktop compatibility repair

The report targets PBIR report schema `3.3.0`. Its generated root previously mixed that contract with a legacy `layoutOptimization` property and omitted the required `themeCollection`, causing Power BI Desktop to reject `definition/report.json` and open a blank report. The generator and project now use an empty `themeCollection` (delegating the default theme to Desktop) and omit `layoutOptimization`. Power BI Desktop `2.150.2455.0` accepted the repaired root without the prior schema diagnostic. Visible refresh, render, and interaction review remains required.

The next Desktop load exposed a separate TMSL issue in `model.bim`. `Sensitivity[Scenario Display]` and the adjacent `Sensitivity[Scenario Type]` were intended as DAX calculated columns but omitted the required `type: calculated` discriminator, so Desktop interpreted them as imported columns and rejected `expression`. Both now use the supported calculated-column representation. Their DAX expressions, visual bindings, model relationships, and analytical meaning are unchanged. Desktop subsequently created the local Analysis Services workspace and registered both fields without a project-load schema error.

A subsequent native load exposed five table-local namespace collisions in `Category Scorecard`: imported backing columns shared names with measures for the two count KPIs and three Wilson evidence measures. The backing columns were renamed with an internal `Value` suffix while preserving each original CSV `sourceColumn`; only the dependent DAX references changed. All public measure names and report bindings remain unchanged. A native Desktop retry reached the named project window with no modal load error.

The native deep-dive review then found a category-domain interaction defect rather than a metric defect. A visual-level categorical filter intended to persist `Health & Beauty` as a default instead restricted the slicer itself to that single value. That filter has been removed from visual `72bdab00c9b6b6435845`. The slicer remains bound to `Category Scorecard[Broad Product Category]`, remains single-select, and now exposes all 24 governed categories, including insufficient-evidence categories. Selecting one category filters the scorecard and sensitivity fact through the existing relationship. The sensitivity table shows eligible units, positive breadth, difference from primary, and median movement for the primary, compact-inclusive, outlier-excluded, and interval-weighted specifications.

The Phase 9 gate now verifies the 24-value slicer domain, absence of domain-restricting filters on the deep-dive slicer, and valid names for any remaining report-, page-, or visual-level filters.

Status: `REVIEW REQUIRED`  
Version: `1.0.0`

## Executive summary

Phase 9 produced a native, source-controlled Power BI Project with a local semantic model and the three approved report pages. It uses the frozen Phase 7 publication tables and implements the governed KPIs without a composite score, sales metric, ranking, or campaign recommendation.

The independent dashboard gate passed **20 of 20 checks**. Microsoft’s offline PBIR validator reported **zero errors**; seven warnings were limited to remote JSON schemas being unreachable from the restricted environment. Three deterministic page previews passed manual readability and semantic review. Power BI Desktop is not installed, so native Desktop rendering, refresh, cross-filter behavior, and screenshot QA remain required during review.

## Dashboard built

1. **Category Engagement Overview** — breadth-versus-magnitude scatter, eligible-product scale, evidence availability, guarded analytical callouts, and Evidence Tier / Sensitivity Status filters.
2. **Category Evidence Deep Dive** — category selector, primary KPI cards, observed dates, Wilson uncertainty, and separate compact-inclusive, outlier-excluded, and interval-weighted sensitivity results.
3. **Evidence & Limitations** — all-category evidence scale, evidence gates, sensitivity status, insufficient categories, and explicit unsupported claims.

## Data used

- `outputs/tables/phase_7_category_comparison.csv` — primary category scorecard and evidence context.
- `outputs/tables/phase_7_sensitivity_analysis.csv` — category-by-scenario sensitivity fact.
- `outputs/tables/phase_7_category_business_analysis.csv` — independent publication reconciliation.
- `outputs/tables/phase_7_business_findings.csv` — approved wording source for callouts.

The semantic model does not load raw data, `total_sold`, or `total_rating`. Phase 7 source hashes reconcile to the Phase 8 manifest and remained unchanged.

## KPI implementation

The model implements:

1. Observed Stable-Category Product Count
2. Eligible Favorite-Movement Product Count
3. Positive Favorite-Movement Breadth
4. Median Daily Favorite Movement per Product
5. Evidence Sufficiency Tier

Movement measures return blank for insufficient categories. Deep-dive display measures translate those blanks to `N/A — insufficient evidence`. Evidence tier is never encoded as performance, and the scatter keeps breadth and magnitude on separate axes.

## Reconciliation

All 24 category rows are present. Tier totals reconcile to **4 HIGH, 10 MODERATE, and 10 INSUFFICIENT**. All 10 insufficient categories have blank breadth and median movement. The sensitivity fact contains **96 rows across four scenarios**.

Spot reconciliation passed exactly for:

- Groceries & Pets: 112 eligible products, 64.28571429% breadth, 0.2111111111 favorites/day, HIGH, DIRECTIONALLY_STABLE.
- Health & Beauty: 337, 62.90801187%, 0.1666666667, MODERATE, ROBUST.
- Women's Bags: 46, 58.69565217%, 0.2792207792, MODERATE, ROBUST.

See `outputs/tables/phase_9_kpi_reconciliation.csv` and `outputs/tables/phase_9_validation_results.csv`.

## Filters and fixed-window behavior

Only Broad Product Category, Evidence Sufficiency Tier, and Sensitivity Status are exposed. No date slicer or date field is exposed because the published KPIs represent a fixed 20-day window and cannot be safely recomputed by arbitrary date filtering.

## Visual QA

The three design previews were inspected at rendered resolution. Titles, units, category terminology, label legibility, spacing, evidence semantics, primary/sensitivity distinction, N/A wording, and limitations were acceptable. No red/green performance convention or leaderboard presentation is used.

The PBIR validator also confirmed the visual roles and layout with zero errors. Native Desktop rendering could not be inspected because Desktop is unavailable. This unresolved item is explicitly retained as `REVIEW REQUIRED` in `outputs/tables/phase_9_visual_qa.csv`.

## Reproducibility

The project is rebuilt with `src/dashboard/build_phase_9_powerbi_project.py`; deterministic previews come from `src/dashboard/render_phase_9_previews.py`; independent checks run from `tests/data_validation/validate_phase_9_dashboard.py`. The PBIP model points directly to the governed Phase 7 CSV locations in this workspace.

## Limitations

The dashboard describes observed displayed-favorite engagement among eligible repeatedly tracked listings in sampled data. It cannot determine sales, revenue, orders, conversion, customer demand, platform-wide category growth, market share, campaign effectiveness, causal effects, or future category performance.

## Review actions

1. Open `dashboard/Shopee_Category_Engagement.pbip` in a current Power BI Desktop version.
2. Allow the two local Phase 7 CSV queries to refresh.
3. Confirm all three pages render and the permitted slicers filter as specified.
4. Test an insufficient category and confirm both movement cards show `N/A — insufficient evidence`.
5. Export or screenshot each page and complete the native-render row in `phase_9_visual_qa.csv`.

Phase 10 remains `NOT STARTED`.
