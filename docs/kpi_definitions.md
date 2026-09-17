# Phase 6 KPI Definitions

Status: `COMPLETED`
Final governed question: Which Broad Product Categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

## Design principles

1. No KPI represents verified sales, revenue, orders, customers, conversion, or campaign outcomes.
2. `total_sold` is blocked; `total_rating` is blocked as a proxy; price × sold is prohibited.
3. Every claim is sample-bound and carries a product denominator, date coverage, and evidence status.
4. Movement is first calculated at interval level, summarized once per product, and only then aggregated to category.
5. Primary favorite movement uses exact displays only. Compact/rounded values appear only in a labeled sensitivity.
6. Products that change Level-2 category are excluded from governed cohorts; no observation is reassigned.
7. Missing and invalid values are excluded, never converted to zero.
8. Valid statistical outliers remain in the primary analysis because flags do not prove error; robust medians are used and outlier exclusion is tested separately.
9. Sparse categories are suppressed, not ranked beside categories with stronger evidence.
10. The scorecard keeps scale, breadth, magnitude, and evidence separate. No weighted composite is permitted.

The machine-readable contract is `outputs/tables/phase_6_kpi_specification.csv`.

## Approved scorecard

| KPI | Role | Primary grain | Headline use |
|---|---|---|---|
| Observed Stable-Category Product Count | Context | Product → category/window | Sample scale only |
| Eligible Favorite-Movement Product Count | Context/denominator | Product → category/window | Evidence base |
| Positive Favorite-Movement Breadth | Core movement | Product → category/window | Breadth of positive movement |
| Median Daily Favorite Movement per Product | Core movement | Interval → product → category/window | Typical movement magnitude |
| Evidence Sufficiency Tier | Governance | Category/window | Comparison permission and suppression |

## Common primary cohort

An interval is eligible when all conditions hold:

- it is a consecutive matched observation for the same product;
- `elapsed_days > 0`;
- both interval endpoints fall inside the active date context;
- `favorite_comparison_status = VALID_EXACT_DISPLAY_VALUES`;
- the product has no Level-2 category change during the study;
- required product, category, and date keys are present.

The product-level fact contains one row per eligible product/category/window. Its base measure is:

```text
product_median_daily_favorite_change
    = median within product/category/window of
      (favorite_count_change_approx / elapsed_days)
```

Zero and negative product medians remain valid. A product with more intervals still contributes only once to category KPIs.

## KPI 1 — Observed Stable-Category Product Count

- Business meaning: sampled product scale for the governed stable-category cohort.
- Formula: distinct `product_id` in snapshot context where `level2_category_changed_over_time_flag = FALSE`.
- Unit/grain: product; Broad Product Category × active date window.
- Numerator: distinct eligible products. Denominator: none.
- Aggregation: distinct count; do not sum into a platform estimate.
- Eligibility/exclusion: include products with a snapshot in context; exclude all Level-2-changing products and missing keys.
- Minimum sample: none; always display the count.
- Missing/approximate/outlier handling: missing keys are ineligible; favorites and outliers do not enter this measure.
- Category changes: exclude the entire changing product so governed category cohorts remain unambiguous.
- Interpretation: observed scale in this scraper sample only.
- Risk/limitation: scraper coverage can create apparent scale differences; this is not assortment or market share.
- Power BI: measure `Observed Stable-Category Products` from `shopee_product_snapshots`; respect date/category filters.
- Validation: nonnegative integer no greater than the distinct stable product count under identical filters.

## KPI 2 — Eligible Favorite-Movement Product Count

- Business meaning: independent product-level evidence available for favorite movement.
- Formula: distinct products with at least one primary-cohort interval.
- Unit/grain: product; Broad Product Category × active date window.
- Numerator: distinct eligible products. Denominator: none; this becomes the movement denominator.
- Aggregation: materialize one product-category row, then count rows/distinct products.
- Eligibility/exclusion: exact valid favorite endpoints, positive elapsed days, both dates in context, stable Level-2 membership; exclude compact, missing/invalid, category-changing, and boundary-crossing intervals.
- Minimum sample: always display; fewer than 30 forces `INSUFFICIENT` evidence.
- Approximate handling: compact intervals excluded from primary and counted in sensitivity coverage only.
- Outliers: valid exact endpoints retained; endpoint-excluded count is a sensitivity.
- Missing values: ineligible, never zero.
- Interpretation: denominator supporting product-level movement comparisons.
- Risk/limitation: exact-display products may not be representative of compact-display products.
- Power BI: measure `Eligible Favorite-Movement Products`; use a Phase 7 product-category fact so one product contributes once.
- Validation: nonnegative integer; no greater than Observed Stable-Category Product Count; reconciles to distinct eligible IDs.

## KPI 3 — Positive Favorite-Movement Breadth

- Business meaning: how broadly positive movement is distributed across eligible products.
- Formula: `100 × products with product_median_daily_favorite_change > 0 / all eligible products`.
- Unit/grain: product; Broad Product Category × active date window.
- Numerator: positive product medians.
- Denominator: all eligible product medians, including zero and negative values.
- Aggregation: product-level median first, then a share across products.
- Eligibility/exclusion: common primary cohort; no interval weighting.
- Minimum sample: publish only for `HIGH` or `MODERATE` evidence.
- Approximate handling: exact-only primary; compact-inclusive product-level breadth is directional sensitivity.
- Outliers: retained in primary; outlier-endpoint-excluded product breadth is mandatory sensitivity.
- Category changes: exclude every Level-2-changing product.
- Missing/zero denominator: missing intervals excluded; denominator zero returns blank.
- Interpretation: breadth, not magnitude. A high value may coexist with small typical changes.
- Risk/limitation: favorite movement is not purchasing; exact-only filtering reduces coverage.
- Power BI: measure `Positive Favorite-Movement Breadth %`; `DIVIDE` positive product rows by eligible product rows and suppress when evidence is insufficient.
- Validation: 100 positive of 200 eligible products equals 50%; allowed range 0%-100%; positive + zero + negative = denominator.

## KPI 4 — Median Daily Favorite Movement per Product

- Business meaning: typical magnitude and direction of exact displayed-favorite movement for an eligible product.
- Formula: category median of each product's median `(favorite change / elapsed days)`.
- Unit/grain: interval → product → Broad Product Category × active date window.
- Numerator/denominator: interval favorite change divided by positive elapsed days; final median has no ratio denominator.
- Aggregation: two-stage median. Mean is rejected because favorite changes are skewed and outlier-sensitive; a trimmed mean remains diagnostic only.
- Eligibility/exclusion: common primary cohort; intervals crossing the active date boundary are excluded.
- Minimum sample: publish only for `HIGH` or `MODERATE` evidence.
- Approximate handling: exact-only primary; compact-inclusive median is directional sensitivity.
- Outliers: retain primary exact observations and rely on the two-stage median; also calculate outlier-endpoint-excluded sensitivity.
- Category changes: exclude every Level-2-changing product.
- Missing/zero denominator: invalid intervals excluded; elapsed days must exceed zero; no eligible products returns blank.
- Interpretation: zero means the typical product showed no displayed movement per day. It does not mean no product moved.
- Risk/limitation: per-day normalization does not reveal when change occurred inside an irregular interval.
- Power BI: measure `Median Daily Favorite Movement per Product`; materialize product medians upstream and aggregate with `MEDIAN`.
- Validation: product medians `[-1, 0, 3]` produce category median `0`; present values must be finite.

## KPI 5 — Evidence Sufficiency Tier

- Business meaning: whether a category/window supports precise comparison, coarse directional comparison, or no comparison.
- Formula:

```text
HIGH
  if observed_dates = 20
  and eligible_products >= 100
  and product-breadth Wilson 95% width <= 20 percentage points

MODERATE
  if not HIGH
  and observed_dates >= 15
  and eligible_products >= 30
  and Wilson width <= 35 percentage points

INSUFFICIENT
  otherwise
```

- Unit/grain: Broad Product Category × active date window.
- Numerator/denominator: positive eligible products / all eligible products for Wilson precision; observed category dates / dates in context for coverage.
- Aggregation: transparent gates; no weights and no compensating between dimensions.
- Eligibility: evaluated after exact-display and stable-category rules.
- Approximate handling: compact-inclusive sensitivity cannot upgrade the tier.
- Outliers: outlier sensitivity cannot upgrade the tier; material disagreement adds `SENSITIVITY_REVIEW_REQUIRED` beside the tier.
- Missing/zero denominator: `INSUFFICIENT` and blank Wilson bounds.
- Interpretation: evidence within this sample only, not representativeness or business importance.
- Risk/limitation: thresholds are governance rules, not proof of statistical independence or external validity.
- Power BI: measure `Evidence Sufficiency Tier`; recalculate under active filters and show dates, n, Wilson bounds, and sensitivity status.
- Validation: `20 dates, n=100, width=19pp` is `HIGH`; `15 dates, n=30, width=34pp` is `MODERATE`; any failed moderate gate is `INSUFFICIENT`.

### Threshold justification

At a 50% product breadth, a Wilson 95% interval with `n=100` is about 19.25 percentage points wide, making 100 an interpretable high-evidence floor. At `n=30`, worst-case width is about 33.7 points, suitable only for coarse directional work. Full 20-date presence is required for `HIGH` because the window is already short; `MODERATE` allows at most five missing dates (75% presence). These rules control within-sample precision; they do not correct uneven sampling.

## Favorite approximation governance

Four options were assessed:

| Option | Decision | Reason |
|---|---|---|
| A. Exact displays only | Approved for primary KPIs | Avoids treating rounded endpoints as exact and makes formulas reproducible. |
| B. Exact + approximate with flag | Approved only as mandatory sensitivity | Retains direction/coverage information without contaminating the primary value. |
| C. Approximate only for broad direction | Retained as part of the labeled sensitivity, not as a standalone KPI | Direction can still be quantized or hidden by rounding. |
| D. Interval-censored modeling | Deferred | The display precision metadata could support later modeling, but assumptions would exceed Phase 6 and Power BI needs. |

The trade-off is material: exact-only intervals retain 2,603 of 3,489 valid intervals (74.61%) and remove 886 (25.39%). At snapshot grain, 4,738 of 19,241 valid favorite displays (24.62%) are compact/rounded. Both primary and sensitivity denominators must be shown.

## Required sensitivity and conflict flag

Recompute product-level breadth and median movement using:

1. all valid exact + compact intervals;
2. exact intervals after excluding favorite-outlier endpoints;
3. interval weighting instead of one product summary.

Set `SENSITIVITY_REVIEW_REQUIRED` when a sensitivity changes the sign of median movement, moves breadth across 50%, or differs from primary breadth by more than 10 percentage points. Do not average conflicting values or resolve disagreement with weights.

## Candidate KPI decisions

| Candidate dimension | Decision | Rationale |
|---|---|---|
| Observed scale | Approve stable-category distinct product count as context | Understandable and reproducible, but explicitly sample-only. |
| Observation coverage | Use as evidence input, not performance KPI | Necessary for reliability; high coverage is not traction. |
| Repeated-product coverage | Approve eligible product count as context/denominator | Directly states the movement evidence base. |
| Engagement movement | Approve favorite movement with exact-only governance | Only available signal with useful movement; remains a proxy. |
| Positive-movement breadth | Approve as core | Robustly distinguishes widespread movement from a few large movers. |
| Median product-level movement | Approve as core | Complements breadth with typical magnitude and limits outlier/interval weighting. |
| Price/discount behavior | Reject from traction KPI set | Describes listing attributes; no revenue, conversion, or causal link to engagement. |
| Evidence reliability | Approve transparent tier | Prevents sparse categories receiving equal treatment. |
| Average-rating movement | Reject | 97.54% of valid intervals are unchanged; little short-window information. |
| Relative favorite growth | Reject | Zero/small baselines and rounded displays make percentages unstable and misleading. |
| Favorite Movement Rate | Reject as redundant/ambiguous | Overlaps breadth or median daily movement depending on definition. |
| Mean/trimmed-mean movement | Reject as headline | Skew and large product changes can dominate; retain only as diagnostics if needed. |
| Category listing share | Reject as KPI | Would invite a market-share interpretation from an unknown sampling process. |

## Composite score decision

No composite “momentum” score is justified. The data offers no defensible component weights, and sensitivity to weights would create a ranking driven by analyst preference. The dashboard should display the dimensions separately. KPI conflicts are informative:

- high breadth + low median movement means movement is widespread but small;
- low breadth + high median movement means movement may be concentrated or distributionally uneven;
- strong movement + insufficient evidence means the category is not comparable;
- large sampled scale + weak movement means broad sample representation, not business underperformance.

No metric dominates another, and no arbitrary weighted tie-break is allowed.

## Power BI behavior

- Default date context is the complete 20-day window.
- An interval enters a filtered view only when both endpoints are inside the selected dates.
- Category filtering uses Broad Product Category while the conservative stable-Level-2 exclusion remains enforced.
- Count measures may show zero; rate and median measures return blank for zero denominators or insufficient evidence.
- Movement KPIs are suppressed for `INSUFFICIENT`; counts, dates, tier, and the suppression reason remain visible.
- The recommended Phase 7 prepared fact has one row per product/category/window with product median, positive/zero/negative outcome, eligible interval count, and sensitivity variants. This preserves grain and keeps Phase 9 DAX simple and auditable.

## Decision logic versus recommendation

KPI definition ends with measurement and evidence qualification. A category may be labeled “further investigation candidate” only if it has `HIGH` evidence, a positive-breadth Wilson lower bound above 50%, positive median daily movement, and no sensitivity conflict. This is not a campaign recommendation. Campaign prioritization still requires conversion, margin, inventory, campaign fit, cost, and outcome/causal evidence absent here.
