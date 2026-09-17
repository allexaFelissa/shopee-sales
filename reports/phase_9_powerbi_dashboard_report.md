# Phase 9 — Broad Product Category Power BI Dashboard

Status: `REVIEW REQUIRED`
Version: `2.0.0`
Publication grain: 12 Broad Product Categories

## Outcome

The existing PBIP/PBIR project was regenerated in place from the current Phase 7 broad-category facts and the approved Phase 8 handoff. No former Level-2 publication result was aggregated, relabeled, or retained in active dashboard logic.

The semantic model contains:

- `Category Scorecard`: 12 rows, one per Broad Product Category.
- `Sensitivity`: 48 rows, 12 categories across primary exact/product, compact-inclusive, outlier-excluded, and interval-weighted scenarios.
- one single-direction category relationship.

Evidence reconciles to 4 `HIGH`, 4 `MODERATE`, and 4 `INSUFFICIENT`. The four insufficient groups retain counts and evidence context while breadth and median movement remain blank/N/A.

## Dashboard pages

1. **Category Engagement Overview** separates breadth, typical movement, eligible-product scale, and evidence. It explicitly states that top-right is not campaign priority.
2. **Category Evidence Deep Dive** uses a single Broad Product Category selector and keeps exact-display primary values distinct from all three sensitivities.
3. **Evidence & Limitations** shows all 12 groups, evidence gates, sampling constraints, and unsupported claims.

Only Broad Product Category, Evidence Sufficiency Tier, and Sensitivity Status are exposed as slicers. There is no date or Level-2 slicer.

## Redesign implementation

1. **Category Engagement Overview** retains the bubble chart as the main comparison, with two descending horizontal bars for breadth and typical movement. Four compact cards show evidence-sufficient categories, maximum breadth, maximum median movement, and eligible tracked products.
2. **Category Evidence Deep Dive** uses a single category selector and five governed KPI concepts. Evidence coverage, Wilson bounds, date/observation coverage, and sensitivity scenarios are visually separate.
3. **Evidence & Limitations** replaces the category evidence table with an all-category horizontal coverage bar chart, retains the four insufficient categories as reason cards, and uses two concise methodological-boundary cards.

The display system is a light-gray canvas with white rounded containers, navy primary text (`#0C1F39`), orange highlights (`#F96722`), soft blue-gray secondary marks, teal stability, and muted rose insufficient-evidence status. These are display conventions only; they do not alter governed tiers, stability classifications, measures, or conclusions.

## KPI and source reconciliation

The dashboard implements the five approved KPIs without recomputing governed cohort logic in DAX. Reference values reconcile for Groceries & Pets, Health & Beauty, and Fashion. Insufficient movement values are not coerced to zero. The model contains no `total_sold`, `total_rating`, sales, revenue, order, conversion, composite score, platform-growth, or campaign-effectiveness measure.

## Portability

The former machine-specific Power Query paths were removed. The generator now embeds the two small publication facts as Base64 CSV consumed by standard Power Query M functions. Another analyst refreshes the PBIP by running:

```powershell
python src/dashboard/build_phase_9_powerbi_project.py
```

and then opening and refreshing `dashboard/Shopee_Category_Engagement.pbip` in Power BI Desktop. All analytical computation remains upstream in Python.

## Validation

- Phase 8: 58/58 checks passed and six exact exports passed rendered review.
- Phase 9 Python gate: 33/33 checks passed after regeneration, including the redesigned visual inventory and evidence-story safeguards.
- PBIR structural validation: passed with 0 errors; 7 warnings only report unreachable remote schemas.
- Deterministic regeneration: required before release.
- Native Desktop project/model load: passed in the installed Desktop build.
- Native page-render, slicer, cross-filter, and N/A-display walkthrough: manual review remains; Phase 9 therefore stays `REVIEW REQUIRED`.

## Interpretation boundary

The dashboard describes observed favorite-display engagement movement among eligible repeatedly tracked listings in sampled data. It cannot determine sales, revenue, orders, conversion, customer demand, market share, platform growth, campaign effectiveness, causal effects, or future performance. No category passes the complete formal further-investigation gate.

Phase 10 recruiter-facing communication is `REVIEW REQUIRED`; it does not introduce a campaign or commercial recommendation.
