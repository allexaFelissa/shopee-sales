# Phase 8 Power BI Handoff — Broad Product Category Revision

Status: `COMPLETED` handoff consumed by the Phase 9 broad-category PBIP/PBIR build.

## Governed inputs

- `phase_7_category_business_analysis.csv`: one row per 12-value Broad Product Category.
- `phase_7_category_comparison.csv`: KPI, Wilson, evidence, and diagnostic fields.
- `phase_7_sensitivity_analysis.csv`: 12 categories × four scenarios.
- `broad_product_category_mapping.csv`: lineage from the preserved 24 Level-2 categories.

Phase 9 must consume these recalculated facts. It must not aggregate the old Level-2 KPI outputs.

## Required filters

1. Broad Product Category — primary publication filter; all 12 values selectable.
2. Evidence Sufficiency Tier.
3. Sensitivity Status.

Category Level 2 may remain a secondary lineage/detail field but must not replace the primary broad filter. No date slicer, ranking control, sales/revenue filter, or composite-score control is allowed.

## Page contract

### 1. Category Engagement Overview

Show breadth versus median movement, eligible tracked-product evidence, and evidence context. Do not frame top-right as priority. Four insufficient groups remain visible as N/A/unranked context.

### 2. Category Evidence Deep Dive

Use a single-select Broad Product Category filter. Show exact-display breadth, median movement, eligible products, date coverage, Wilson bounds, evidence tier, and separately labeled sensitivities. The primary result must remain fixed.

### 3. Evidence & Limitations

Show the evidence rules, all 12 groups, four insufficient groups, sensitivity instability, and unsupported claims. Cards reconcile to HIGH 4, MODERATE 4, INSUFFICIENT 4, formal further-investigation gate passes 0.

## N/A and semantic rules

- Entertainment & Hobbies, Others, Tickets & Vouchers, and Travel have blank published movement KPIs.
- Do not coalesce blank movement values to zero.
- Eligible product count is an analytical denominator, not market size.
- Evidence tier is evidence availability, not performance.
- ROBUST means specification stability, not positive or strong movement.
- Primary exact-display values remain visually dominant over compact-inclusive, outlier-excluded, and interval-weighted results.

## Required reconciliation

Phase 9 must reconcile all cards, marks, filters, and tooltips to the Phase 7 tables; retain all five approved KPIs; preserve the Level-2-change exclusion; and expose no sales, revenue, order, conversion, platform-growth, campaign-effectiveness, or composite score.
