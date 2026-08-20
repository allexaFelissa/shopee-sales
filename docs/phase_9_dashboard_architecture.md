# Phase 9 Power BI Dashboard Architecture

Status: `REVIEW REQUIRED`  
Dashboard version: `1.0.0`  
Power BI project: `dashboard/Shopee_Category_Engagement.pbip`

## Governed purpose

The dashboard answers:

> Which Broad Product Categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

It is an evidence-aware listing-engagement dashboard. It is not a sales, revenue, demand, platform-growth, campaign-effectiveness, or forecasting dashboard.

## Architecture

```text
Phase 7 category comparison CSV ──> Category Scorecard (1 row/category)
                                         1
                                         │ Broad Product Category
                                         *
Phase 7 sensitivity CSV ──────────> Sensitivity (category × scenario)
                                         │
                                         v
                                Three-page PBIR report
```

The semantic model imports the governed publication tables through Power Query. No KPI cohort is re-derived from raw or Phase 4 data. The relationship is single-directional from `Category Scorecard` to `Sensitivity`. The fixed observation window is not modeled as a user-filterable date dimension.

## Pages

### 1. Category Engagement Overview

- Executive scatter: Positive Favorite-Movement Breadth versus Median Daily Favorite Movement per Product.
- Bubble size: Eligible Favorite-Movement Product Count.
- Evidence context: tier grouping and category counts.
- Filters: Evidence Sufficiency Tier and Sensitivity Status.
- Safeguard: the page states that the scatter is not a campaign-priority map.

### 2. Category Evidence Deep Dive

- Filter: Broad Product Category.
- Primary cards: breadth, median daily movement, eligible products, and evidence tier.
- Evidence table: observed dates and Wilson interval/width.
- Sensitivity comparison: exact-display primary versus compact-inclusive, outlier-excluded, and interval-weighted scenarios.
- Blank behavior: `N/A — insufficient evidence`, never a fabricated zero.

### 3. Evidence & Limitations

- Eligible tracked products by Broad Product Category.
- Evidence gates and sensitivity status table.
- Filters: Evidence Sufficiency Tier and Sensitivity Status.
- Explicit limitations and unsupported-claim boundary.

## Visual-to-KPI mapping

| Visual | Governed KPI / context | Source |
|---|---|---|
| Breadth–magnitude scatter | Positive Favorite-Movement Breadth; Median Daily Favorite Movement per Product; Eligible Favorite-Movement Product Count; Evidence Sufficiency Tier | Category Scorecard |
| Evidence bars and table | Eligible Favorite-Movement Product Count; Evidence Sufficiency Tier; observed dates; Wilson width | Category Scorecard |
| Deep-dive cards | Four numeric/categorical governed category values | Category Scorecard |
| Sensitivity bar and table | Governed primary plus three required sensitivities | Sensitivity |
| N/A cards | Governed blank behavior | DAX display measures over Category Scorecard |

## Filters and interactions

The only user-facing filter fields are:

1. Broad Product Category
2. Evidence Sufficiency Tier
3. Sensitivity Status

No date slicer is exposed. Page 2 category selection filters the scorecard and the sensitivity table through the category relationship. Page tabs provide navigation. The model contains no bidirectional or many-to-many relationship.

## Reproducibility

- Build: `python src/dashboard/build_phase_9_powerbi_project.py`
- Layout previews: `python src/dashboard/render_phase_9_previews.py`
- Independent validation: `python tests/data_validation/validate_phase_9_dashboard.py`
- PBIR structural validation: `powerbi-report-author validate dashboard/Shopee_Category_Engagement.Report`

The build uses deterministic page and visual identifiers. `dashboard/phase_9_build_manifest.json` records the generated project files and source lineage.

## Review limitation

Power BI Desktop is not installed in the execution environment. The report therefore passed offline PBIR role, formatting, layout, and structure validation, and three deterministic layout previews received manual QA. Opening the `.pbip`, refreshing the local CSV sources, and completing native Desktop render/cross-filter/slicer screenshot QA remains a reviewer action before the phase can be marked `COMPLETED`.

