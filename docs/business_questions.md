# Business Questions and Initial Evidence Contract

> **Historical Phase 0 contract.** This document preserves the original question and early candidate metrics for decision traceability. It is not the current analytical specification. The authoritative governed question and approved KPI framework are in [business_question_governance.md](business_question_governance.md) and [kpi_definitions.md](kpi_definitions.md).

## Central Big Question

> Which product categories are gaining momentum fastest on the platform, and which of those should a marketplace's category team prioritize featuring in upcoming campaigns and collections?

This is the organizing question for the project. Phase 0 does not answer it; it establishes what the current dataset can measure and where the claim must be narrowed.

## Measurable version to test later

Subject to validation of `total_sold`, a defensible dataset-specific version is:

> Among broad categories represented by repeatedly observed Shopee Malaysia product listings from 2023-04-24 through 2023-05-13, which show the strongest combination of positive change in the labeled cumulative sold field, breadth across tracked products, observed category scale, and consistency across available intervals?

Do not call this platform-wide sales momentum. The dataset is a short, uneven listing sample rather than a transaction census.

## Operational definitions still requiring approval

| Term | Candidate definition | Alternative/sensitivity | Why unresolved |
|---|---|---|---|
| Category | Level-2 value in `item_category_detail` | Level 3 for categories with sufficient support | Level 4 is sparse; 19 products change full paths. |
| Performance | Change in validated cumulative sold count for matched listings | Listing count, favorite change, or price-weighted change as separate proxies | No orders or realized revenue exist; sold/rating fields may be duplicated. |
| Recent | A fixed trailing segment within the 20-day window | Equal-duration early vs late matched intervals | Window is short and observations per product are irregular. |
| Growth | Absolute or per-day change in a cumulative field | Relative change with minimum baseline rules | Percent growth exaggerates small starting values. |
| Consistency | Share of matched product intervals with positive change | Median product velocity or positive-day breadth | Most repeated products have only two observations. |
| Scale | Number of tracked products and/or validated cumulative/incremental units | Price-weighted proxy, explicitly not revenue | Daily category sample size varies strongly. |
| Momentum | Multi-signal assessment of recent velocity, breadth, consistency, scale, and reliability | Separate scorecard instead of a composite score | Weighting can hide assumptions and must be approved in Phase 6. |
| Priority | Evidence tier for featuring/testing/maintaining/deprioritizing | No recommendation when reliability threshold fails | Campaign economics, margins, inventory, and conversion are absent. |

## Supporting questions

### Measurement validity

1. Does `total_sold` represent cumulative units sold, or is it a duplicated rating count?
2. Which product IDs have enough repeated observations for defensible change measurement?
3. How uneven is listing coverage by date and category, and can matched cohorts reduce that bias?
4. At which category level is support sufficient and category identity stable?

Phase 1 result: question 1 is unresolved and release-blocking. `total_sold` is unusable as sales evidence without independent validation. All supporting questions that require sales, units, revenue, velocity, growth, or acceleration remain **blocked**, not answered.

## POTENTIAL REFRAMING — REQUIRES APPROVAL

> Which product categories show the strongest observed traction among repeatedly tracked Shopee listings in this sampled dataset?

This has **not** replaced the original Big Question. Phase 2 prepared coverage, matched-product, price, favorite, category-stability, and ambiguous-counter audit fields, but it did not establish a verified performance metric. Even the proposed reframing must define “traction” without implying sales and must be explicitly approved before final analysis or dashboard use.

### Category growth

1. Which supported categories have the highest matched-listing sold-count change per observed day?
2. Which categories have the broadest positive movement across products rather than dependence on a few listings?
3. Which categories show stronger recent velocity than earlier velocity, where observation history permits?
4. How sensitive are category results to compact-count rounding and inclusion thresholds?

### Scale and reliability

1. Do fast-moving categories have meaningful tracked-product coverage?
2. Which categories combine movement with a sufficiently large and stable matched cohort?
3. How much of a category result is driven by its largest product outliers?
4. Does the category ranking change when using medians, winsorized aggregates, or minimum-baseline rules?

### Price and promotion proxies

1. Is change in the sold-count field associated with displayed discount depth or price changes?
2. Are any apparent relationships robust after accounting for category and listing coverage?

These questions support association only. The dataset contains no campaign exposure or causal design.

### Recommendation

1. Which categories have high measured traction, meaningful scale, broad participation, and acceptable evidence reliability?
2. Which appear emerging but need a controlled campaign test rather than full prioritization?
3. Which are established but show weak recent movement?
4. Which must remain unranked because coverage or field validity is inadequate?

## Candidate analytical dimensions

- Snapshot date and later-defined early/recent windows
- Level-2 category; level 3 only after support checks
- Product ID and matched-product cohort
- Seller
- Displayed price and original price
- Discount proxy derived later from valid price pairs
- Labeled cumulative sold/rating count
- Average rating and favorites as secondary listing signals
- Observation coverage and reliability tier

Customer, transaction, true revenue, order, campaign, and reliable geographic dimensions are unavailable.

## Candidate KPIs for Phase 6 review

| Candidate KPI | Potential formula | Required columns | Business meaning | Main limitation |
|---|---|---|---|---|
| Tracked Product Count | Distinct `id` by category/window | `id`, category, `w_date` | Observed category sample scale | Measures dataset coverage, not platform assortment. |
| Matched Product Count | Distinct products with at least two usable snapshots | `id`, `w_date`, candidate cumulative field | Evidence base for change analysis | Only 3,070 of 16,614 products currently qualify. |
| Observation Coverage | Product snapshots or matched products by category/date | `id`, category, `w_date` | Reliability and changing-sample diagnostic | High coverage is not business performance. |
| Net Labeled-Sold Change | Sum of last minus first validated cumulative count within a governed window | `id`, `w_date`, `total_sold` | Aggregate observed movement in matched listings | Field validity is unresolved; interval lengths differ. |
| Sold-Change Velocity | Cumulative-count delta divided by elapsed days | `id`, `w_date`, `total_sold` | Normalizes irregular observation gaps | Compact `k` rounding and cumulative semantics distort small changes. |
| Positive-Movement Breadth | Products or intervals with positive delta / eligible products or intervals | Same as above | Distinguishes broad movement from a few winners | Denominator and repeated-observation requirements must be fixed. |
| Median Product Velocity | Median per-product sold-change-per-day | Same as above | Robust typical listing movement | Can understate scale and remains invalid if `total_sold` is wrong. |
| Recent-vs-Prior Velocity | Recent matched velocity minus or divided by prior matched velocity | Same fields plus approved windows | Candidate acceleration signal | Twenty days and mostly two observations make this weak or unavailable for many categories. |
| Category Listing Share | Category distinct products / all distinct tracked products in comparable cohort | `id`, category, `w_date` | Relative representation in the observed sample | Can reflect scraper sampling rather than marketplace scale. |
| Discount Prevalence | Valid listings with `price_actual < price_ori` / valid price pairs | `price_actual`, `price_ori`, category | Exposure to displayed markdowns | No explicit promotion/campaign field; extreme prices require later rules. |
| Price-Weighted Sold-Change Proxy | Sum of valid price times validated sold-count delta | price, product, date, sold field | Rough value-weighted traction proxy | Not revenue; price timing, variants, refunds, and realized prices are unknown. |
| Momentum Reliability Tier | Rule-based grade from coverage, matched count, field validity, and sensitivity stability | All evidence-quality measures | Prevents weak categories from receiving confident ranks | Thresholds require Phase 6 approval. |

No candidate KPI is final. `Revenue`, `Orders`, `AOV`, `Customers`, and `Conversion Rate` are not currently computable as genuine business KPIs.

After Phase 1, all candidates derived from `total_sold` are suspended pending field validation or replacement. Coverage, matched-product count, category representation, price-quality, and reliability measures remain computable, but they cannot by themselves answer the central sales-momentum question.

## Candidate momentum definitions

1. **Matched absolute velocity:** aggregate validated cumulative-count changes divided by exposure days. Simple and scale-aware, but favors large categories and depends on field validity.
2. **Relative matched growth:** cumulative change divided by starting cumulative count. Comparable across size, but unstable for zero or tiny baselines and distorted by compact rounding.
3. **Breadth-adjusted momentum:** velocity plus the share of eligible products with positive movement. Reduces dependence on isolated winners, but needs minimum cohort sizes.
4. **Recent acceleration:** recent velocity relative to prior velocity for the same products. Closest to “gaining” momentum, but the 20-day window and sparse repeats make it the least broadly feasible.
5. **Scale-growth scorecard:** keep velocity, breadth, observed scale, and reliability as separate dimensions. Most transparent and currently preferred for later evaluation; avoids arbitrary composite weights.

Phase 1 feasibility decision: the scorecard remains the preferred architecture, but its growth and breadth components cannot use `total_sold` in the current state. Recent acceleration is additionally underpowered: only 535 products have at least three observations and 86 have at least four.

Phase 2 safeguard: every matched interval is labeled `BLOCKED_COUNTER_UNVERIFIED` or lacks a usable prerequisite. No row is currently eligible for a verified sales-movement calculation.

## Conceptual future decision logic

Only after metric validation and approved thresholds:

```text
High momentum + high scale + adequate reliability -> strong campaign candidate
High momentum + low scale + adequate reliability  -> emerging/test opportunity
Low momentum  + high scale                         -> established/maintain presence
Low momentum  + low scale                          -> lower evidence-based priority
Any signal     + low reliability                   -> do not rank; improve evidence
```

This is not yet a recommendation framework. Margin, inventory, campaign fit, and operational constraints are absent and must be acknowledged before a business decision.

## Phase 5 feasibility decision

The original Big Question remains unchanged but is **not defensibly answerable** from the current dataset:

> Which product categories are gaining momentum fastest on the platform, and which of those should a marketplace's category team prioritize featuring in upcoming campaigns and collections?

The data cannot measure verified sales momentum, category business growth, platform-wide growth, or campaign priority. Earlier candidate questions and metrics that rely on `total_sold`, including sold-count change, sales velocity, relative sales growth, acceleration, price-weighted sold change, and sales-based category ranking, remain suspended and must not be implemented.

The following remains a **potential reframing — requires approval**:

> Which product categories show the strongest observed traction among repeatedly tracked Shopee listings in this sampled dataset?

Phase 5 found this narrower question conditionally supportable only if “traction” is governed as separate sampled dimensions rather than silently equated with sales:

- observed sample scale;
- repeated-product and interval evidence;
- approximate favorite movement and positive breadth;
- average-rating stability;
- calendar and category coverage;
- uncertainty, compact-rounding sensitivity, category stability, and product concentration.

Candidate Phase 6 questions are:

1. Is favorite movement an acceptable, clearly labeled engagement proxy for this portfolio analysis?
2. Should breadth use intervals or one product-level summary per category, and what is the valid denominator?
3. What minimum date coverage, distinct-product evidence, and uncertainty precision are required before comparison?
4. Must approximate compact-display intervals be excluded, reported separately, or retained only in sensitivity analysis?
5. How should category changes, outlier endpoints, and irregular elapsed days be governed?
6. Should the final output remain a multidimensional scorecard rather than a composite score or rank?

These questions do not authorize campaign recommendations. Campaign prioritization requires business outcomes and decision inputs absent from the dataset.

## Phase 6 governed decision

Controlled taxonomy revision note: the original approved question and five KPI definitions are unchanged, but the future publication grain will be the project-defined `broad_product_category`. `category_level_2` remains available for detail. All denominators, Wilson intervals, evidence tiers, breadth, and median movement must be recomputed from underlying eligible observations; existing Level-2 results cannot be aggregated into broad results.

Phase 6 formally rejects the original Big Question as unsupported and approves a narrower, sample-bound analytical question:

> Which Level-2 product categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

“Observed traction” is now governed as a non-composite scorecard, not sales momentum. Primary movement uses exact favorite displays, stable Level-2 products, positive elapsed intervals, and one product-level median before category aggregation. Compact/rounded displays are retained only in a separately labeled sensitivity. Categories failing the transparent evidence gates are not comparable and receive blank movement KPIs rather than zeroes.

The approved definitions are in `docs/kpi_definitions.md`; the component-by-component decision and allowed claims are in `docs/business_question_governance.md`. No category result, rank, composite score, or campaign recommendation is made in Phase 6.

## Phase 7 business-analysis result

Phase 7 applied the governed scorecard to every Broad Product Category. Four categories have `HIGH` evidence, ten have `MODERATE` evidence, and ten have `INSUFFICIENT` evidence. Insufficient-category movement KPIs remain blank.

No category meets the complete formal gate for a “candidate for further business investigation.” `Groceries & Pets` has the strongest high-evidence primary combination, but compact-inclusive breadth differs from primary by more than the governed 10-point limit. `Health & Beauty` has the strongest robust positive pattern but only `MODERATE` evidence because it appears on 19 of 20 dates. `Men Clothes`, `Mobile & Accessories`, and `Women Clothes` have `HIGH` evidence but sensitivity-unstable movement.

These results answer only the sampled favorite-engagement question. They do not answer the original sales/platform-growth or campaign-priority question. See `reports/phase_7_business_analysis_report.md` and the Phase 7 category tables.
