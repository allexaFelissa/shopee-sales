# Phase 0 Analysis Plan

## Purpose

Establish whether the raw listing-snapshot dataset can support the central category-momentum question and define the evidence needed before any cleaning or final analysis.

## Proposed evidence flow

```text
Source and field validation
        -> category hierarchy and stability
        -> snapshot coverage and matched-product cohort
        -> cumulative-count validity
        -> interval-normalized movement
        -> breadth and outlier sensitivity
        -> observed category scale
        -> transparent momentum scorecard
        -> reliability tier
        -> campaign-priority evidence tier
```

## Future execution sequence

1. **Phase 1 profile:** fully characterize raw types, missingness, count formats, price anomalies, category consistency, duplicate/key behavior, snapshot coverage, and suspected sold/rating duplication.
2. **Phase 2 clean:** create a new processed dataset with documented category levels, parsed compact counts, valid dates, price-quality flags, and explicit handling rules; preserve raw bytes.
3. **Phase 3 validate:** reconcile raw/clean row counts, product/date keys, parsing coverage, category mappings, cumulative monotonicity, and all exclusions.
4. **Phase 4 transform:** build a product-snapshot table and matched-product interval table with elapsed days and changes. Keep coverage measures alongside performance measures.
5. **Phase 5 explore:** assess whether results are stable across category levels, periods, aggregation methods, minimum baselines, cohort definitions, and outlier treatments.
6. **Phase 6 govern KPIs:** approve exact windows, formulas, denominators, eligibility thresholds, reliability rules, and the use or rejection of `total_sold`.
7. **Phase 7 answer:** compute category facts using frozen definitions; do not rank categories failing reliability thresholds.
8. **Phases 8-10 communicate:** visualize growth, breadth, scale, and reliability; reconcile dashboard values; produce evidence-bound recommendation tiers.

## Required preconditions for a credible answer

- Establish whether `total_sold` has an independent and trustworthy meaning despite matching populated `total_rating` exactly and matching its missingness after normalization.
- Use matched products or another defensible coverage-control method; never compare raw daily category totals from changing samples as if they were sales totals.
- Normalize comparisons for unequal observation intervals.
- Set minimum category and product-history eligibility rules before ranking.
- Keep absolute movement, relative movement, breadth, scale, and reliability visible rather than hiding them in one unexplained score.
- Preserve sensitivity results for small baselines, outliers, compact-count rounding, category changes, and time-window choice.

## Phase 1 methodological update

- Treat `total_sold` as **unusable for sales, growth, velocity, breadth, and momentum** unless independent source or scraper evidence validates it.
- Treat `total_rating` as an **unverified** cumulative counter rather than a confirmed rating count.
- Do not proceed from coverage diagnostics to a campaign recommendation without a validated performance measure.
- Use level 2 as the default candidate category grain; deeper levels require explicit support thresholds.
- Make matched-cohort eligibility and coverage reliability mandatory fields in any later analytical table.
- Keep recent acceleration as a sensitivity analysis only because just 535 products have at least three snapshots.
- If no valid performance field can be recovered, narrow the project to sampled listing traction and state that the original platform momentum question cannot be answered reliably.

## Phase 2 implementation update

### Verified structural fields

- Observation date and its agreement with the raw timestamp
- Level-1 through level-4 category extraction; level 2 marked as primary
- Product/snapshot keys and chronological observation sequence
- Product observation counts, first/last dates, span, and interval lengths
- Exact/key duplicate absence and potential duplicate-review groups
- Category-path and broad-category change flags
- Daily, category-date, category-total, and matched-product coverage counts
- Price/favorite/rating parse and quality statuses

### Unverified or blocked fields

- `total_sold` remains unusable as a sales metric.
- `total_rating` remains an unverified counter.
- `favorite` is a secondary, incomplete, approximate engagement display.
- Currency is contextually likely MYR but unverified.
- All interval movement statuses remain blocked from sales analysis.

### Unavailable metrics

- Orders, realized revenue, units sold, AOV, customers, conversion, impressions, campaign exposure, margin, refunds, cancellations, and platform-wide category share.

### Future candidates after Phase 3

- Coverage and reliability assessment using verified structural fields
- Descriptive listing-price and discount analysis using valid price pairs
- Average-rating and favorite analysis with explicit missing/rounding caveats
- Ambiguous-counter sensitivity analysis only if its semantics receive independent validation

Momentum methodology remains unfinalized. Phase 3 must validate every derived field and confirm the raw-to-processed reconciliation before any analytical table is built.

## Phase 4 transformation update

Controlled taxonomy revision: Phase 4 now enriches the snapshot, matched-interval, product, and daily interfaces with the deterministic `broad_product_category` grouping while retaining every Level-2 field. The mapping covers all 24 observed Level-2 values with 12 broad groups and is independently validated. Level-2 and broad-category stability are separate diagnostics; the approved conservative Level-2-change exclusion remains unchanged. Downstream Phase 6-9 results must be recomputed from eligible observations at the new broad grain before they can be treated as current.

Phase 4 created six governed analytical structures from the validated Phase 2 snapshot table:

1. A product-snapshot interface retaining the source grain and quality/status fields.
2. A consecutive matched-observation table for valid price, discount, favorite, and average-rating comparisons.
3. A product-grain coverage table.
4. A daily sampling-coverage table.
5. A complete Level-2 category/date coverage grid.
6. A Level-2 descriptive structural summary.

The structures make the following future investigations technically possible without approving them as KPIs:

- Listing-price and displayed-discount patterns using validity-gated price fields.
- Favorite and average-rating patterns using explicit missingness and compact-rounding status.
- Sensitivity to repeated-product coverage, elapsed observation intervals, category changes, and daily/category sampling coverage.
- Comparison of category evidence availability using raw coverage measures.

Phase 4 did **not** create a verified business-performance measure, category rank, momentum score, campaign recommendation, or reliability tier. `total_sold` and `total_rating` values are intentionally absent from the analytical interfaces; only their trust statuses remain. Any future observed-traction interpretation still requires explicit approval and an evidence-bound operational definition.

## Phase 5 evidence update

Phase 5 tested the available analytical directions without approving a KPI or answering the business question.

- Daily sampling varies from 201 to 3,727 snapshots; category and time coverage must remain explicit in every comparison.
- Only 3,070 of 16,614 products repeat. The matched structure contains 3,698 irregular intervals, and just 535 products have at least three observations.
- Favorites permit exploratory matched engagement comparisons, but 24.62% of valid snapshot values are compact/rounded. The valid-interval denominator is 3,489: 1,518 positive, 1,891 zero, and 80 negative.
- Average rating is nearly static: 3,414 of 3,500 valid intervals are unchanged.
- The original Big Question is not defensibly answerable with this dataset. The sampled-listing observed-traction question is conditionally supportable for exploration and remains subject to explicit approval.

Phase 6 should govern, separately, candidate evidence measures, observed sample scale, positive favorite-movement breadth, median product-level favorite change per day, concentration, and sensitivity requirements. It must decide whether favorites are an acceptable engagement proxy. A transparent multidimensional scorecard is preferable to a weighted composite, but neither is approved.

The following sensitivity views are mandatory if favorite movement proceeds: all valid versus exact-only displays, interval versus product weighting, inclusion versus exclusion of outlier endpoints, Level-2-stable versus all intervals, Wilson uncertainty, date coverage, and top-product concentration. No category should be compared without its denominator and evidence base.

## Stop/narrow conditions

Narrow the claim to listing-sample traction—or conclude that momentum is not supportable—if any of these remains unresolved:

- `total_sold` cannot be distinguished from `total_rating`.
- Matched coverage is too sparse for stable category comparisons.
- Results are dominated by changes in scraper coverage or a few listings.
- Recent-versus-prior windows cannot be constructed with adequate observations.
- Category results reverse under reasonable cohort, baseline, or outlier sensitivity choices.

## Planned artifacts

- Phase 1: `reports/data_quality_report.md`
- Phase 2: `data/processed/shopee_sales_cleaned.csv` and `reports/data_cleaning_report.md`
- Phase 3: validation checks and `reports/data_validation_report.md`
- Phase 4: documented product-snapshot and matched-interval analytical tables
- Phase 5 onward: governed facts tables, KPI definitions, charts, dashboard, and final report

## Phase 7 execution update

Controlled taxonomy recalculation (analysis version 2.0.0): all Phase 7 KPIs were recomputed from eligible intervals at the governed 12-group Broad Product Category grain. The primary cohort remains 2,590 exact-display, Level-2-stable intervals and 2,169 product summaries. Evidence is now 4 `HIGH`, 4 `MODERATE`, and 4 `INSUFFICIENT`; no group passes the complete further-investigation gate. Former Level-2 results remain historical comparison evidence and were not aggregated into the new values.

Phase 7 executed the frozen Phase 6 definitions against unchanged Phase 4 tables.

- Exact favorite filtering retains 2,603 of 3,489 valid intervals; excluding all Broad Product Category-changing products leaves 2,590 primary intervals.
- Product-level aggregation produces 2,169 eligible product-category summaries across 24 categories.
- Evidence results are 4 `HIGH`, 10 `MODERATE`, and 10 `INSUFFICIENT`; insufficient movement values are blank.
- Compact-inclusive, outlier-excluded, and interval-weighted sensitivities are reported separately.
- No category passes the complete formal further-investigation gate; no campaign recommendation is made.
- No KPI definition, composite score, sales/revenue metric, or upstream analytical table was changed.

The user explicitly approved Phase 8 visualization work after reviewing the Phase 7 gate.

## Phase 8 visualization update

Phase 8 transformed the frozen Phase 7 facts into a governed six-visual analytical layer and a three-page Power BI plan.

- The executive scatter keeps breadth and median daily movement on separate axes; eligible product count controls size and evidence tier remains a separate grouping.
- Evidence, eligible-product scale, breadth, and typical magnitude each have a dedicated view. All 24 categories remain visible where relevant.
- The ten `INSUFFICIENT` categories appear as `N/A — insufficient evidence`, never as zero or ranked movement values.
- Compact-inclusive, outlier-excluded, and interval-weighted sensitivities are shown in separate aligned panels with exact/product results fixed as primary.
- Evidence tier uses neutral quality semantics and is explicitly separated from category performance.
- Phase 9 is specified as three pages: Category Engagement Overview, Category Evidence Deep Dive, and Evidence & Limitations.

All six exact PNG exports passed manual visual QA, and the independent Phase 8 gate passed 57 of 57 checks. Ten generated artifacts reproduced byte-for-byte with zero hash differences. No KPI, composite score, sales/revenue measure, dashboard, or campaign recommendation was created. Phase 9 requires explicit approval.

## Phase 9 dashboard implementation update

The user explicitly authorized Phase 9. A native source-controlled PBIP/PBIR project now implements the frozen three-page design using Phase 7 publication tables as the factual source.

- Page 1 separates breadth, typical movement, eligible tracked-product scale, and evidence context.
- Page 2 provides single-category exact-display primary KPIs with Wilson evidence and three separately labeled sensitivity specifications.
- Page 3 exposes evidence gates, sampled scale, insufficient categories, and unsupported claims.
- Only Broad Product Category, Evidence Sufficiency Tier, and Sensitivity Status are exposed as filters; the fixed 20-day window has no date slicer.
- Independent validation passed 20 of 20 checks; offline PBIR validation passed with zero errors; three deterministic layout previews passed manual semantic/readability QA.
- Native Desktop refresh/render/interaction QA remains required because Power BI Desktop is not installed in the execution environment.

No KPI, composite score, sales/revenue/order/conversion metric, campaign recommendation, or Phase 10 analysis was added. Phase 9 is `REVIEW REQUIRED`; Phase 10 remains `NOT STARTED`.
