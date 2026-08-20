# Phase 7 Broad Product Category Analysis Contract

Status: `REVIEW REQUIRED`

The publication grain is the governed 12-value `broad_product_category`; the 24-value `category_level_2` remains unchanged as detail. Every result is recalculated from eligible Phase 4 observations, never aggregated from old Level-2 KPI outputs.

## Governed calculation

- Base unit: consecutive product interval.
- Primary eligibility: exact favorite displays, valid comparison, positive elapsed days, full fixed 20-day context, and no Level-2 change anywhere in product history.
- Product unit: median daily favorite change per product within its deterministic Broad Product Category.
- Breadth numerator: eligible products with a positive product median.
- Breadth denominator: all eligible products, including zero and negative medians.
- Typical movement: median of product medians.
- Evidence: unchanged Phase 6 date, product-count, and Wilson-width thresholds.
- Suppression: `INSUFFICIENT` groups retain counts and evidence diagnostics but publish blank movement KPIs, never zero.

## Stability and sensitivity

Broad-category stability is diagnostic. The conservative Level-2-change exclusion remains authoritative, including a hypothetical change between Level-2 values in the same broad group. Required sensitivities are compact-inclusive product, outlier-excluded exact product, and interval-weighted exact. They never replace the exact-display product primary.

## Claim boundary

These are sampled favorite-display engagement results. They do not measure sales, revenue, orders, conversion, platform growth, campaign effectiveness, or causal effects. No composite score or automatic ranking is permitted.

## Validation and falsification

Publication fails if mapping coverage is incomplete, hashes change unexpectedly, denominators do not independently reconcile, Wilson intervals differ, insufficient values are nonblank, any required sensitivity is absent, or any Level-2-changing product enters the primary cohort.
