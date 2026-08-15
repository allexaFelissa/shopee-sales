# Phase 5 EDA Analysis Contract

## 1. Question as measurable claim

- **Plain question:** What patterns, evidence strengths, and limitations exist in the sampled Shopee listing snapshots, and can they support a later observed-traction framework?
- **Measurable Phase 5 version:** Describe sampling coverage, repeated-product availability, valid displayed-price behavior, and favorite/rating movement among matched listing intervals at product, date, and Level-2 category grains.
- **Do not claim yet:** Platform growth, sales growth, revenue, campaign impact, category priority, a final traction definition, a final KPI, or a momentum ranking.

## 2. Operational definitions

| Term | Phase 5 definition | Sensitivity / alternative | Why it matters |
|---|---|---|---|
| Observed scale | Sampled snapshot and unique-product counts | Repeated-product counts and category-date coverage | Sample size is not platform assortment or demand |
| Repeated product | `product_id` with at least two dates | Products with at least three or four dates | Only repeated products support interval comparisons |
| Matched interval | Consecutive snapshots for the same product | Product-level aggregation across all intervals | Prevents comparing unrelated listings |
| Favorite movement | Current minus previous valid approximate favorite display | Per-day change; exact-display-only subset; product-level median | Compact displays are rounded and missingness is non-random |
| Positive favorite breadth | Valid favorite intervals with change > 0 divided by valid favorite intervals | Distinct products with any/median positive movement | Interval-heavy products can receive more weight |
| Price movement | Current minus previous valid displayed actual price | Percentage change and stable-category-only subset | Displayed prices are not realized revenue |
| Rating movement | Current minus previous valid average rating | Share unchanged and stable-category-only subset | Ratings are bounded and often unchanged |
| Category coverage | Dates observed, sampled snapshots, products, repeated products, and valid intervals | Daily coefficient of variation and zero-date count | Raw listing-count changes can reflect scraping coverage |
| Evidence sufficiency | Continuous evidence fields: dates, products, valid intervals, Wilson interval width, compact share, and dominance | A later governed threshold screen | Phase 5 must not invent a final reliability tier |
| Observed traction | A future multidimensional concept that may combine scale, engagement movement, breadth, coverage, and reliability | Keep dimensions separate | Combining them now would silently create a KPI or score |

## 3. Unit, denominator, numerator

- **Snapshot unit:** one product listing on one observation date.
- **Matched unit:** one consecutive product interval.
- **Product unit:** one persistent product, used as a sensitivity denominator so products with more intervals do not dominate.
- **Category unit:** one Level-2 category; current-interval category is used for interval summaries, with stable-category-only sensitivity.
- **Main breadth denominator:** matched intervals with valid favorite values at both endpoints.
- **Sensitivity breadth denominator:** distinct products with at least one valid favorite interval, summarized to one product-level median daily change.
- **Positive breadth numerator:** denominator units whose valid favorite change is greater than zero.
- **Exclusions:** invalid/missing price or engagement comparisons from the corresponding metric only; no row deletion from source tables.

## 4. Metrics

- Counts, shares, missingness, mean, median, standard deviation, quartiles, P05/P95/P99, minimum, and maximum.
- Daily/category coverage counts and coefficient of variation, with zero-observation category dates visible.
- Valid price and discount distributions using medians and robust sensitivity summaries.
- Favorite/rating change, per-day favorite change, positive/zero/negative breadth, and Wilson 95% intervals for positive breadth.
- Exact-display-only, stable-category-only, outlier-excluded, and product-level sensitivity summaries.
- Required sample-size columns accompany every category movement result.

## 5. Comparisons

- Daily volume versus the 20-day median and full observed range.
- Categories versus each other on separate evidence dimensions—not a combined score.
- All valid versus exact-display-only favorite intervals.
- Interval-weighted versus product-level favorite movement.
- All products versus stable-category products.
- Full valid prices versus explicit outlier-excluded prices.
- Absolute movement versus elapsed-day-normalized movement.

## 6. Data requirements and profile checks

- Inputs: the six Phase 4 analytical CSVs only, except source audit when necessary.
- Grain checks: all Phase 4 keys must remain unique.
- Coverage checks: 20,312 snapshots, 16,614 products, 3,698 intervals, 20 dates, 24 categories, and a 480-row category-date grid.
- Validity rules: use only `VALID_COMPARISON` or documented valid statuses for a metric.
- Compact favorites: keep approximate status visible and run exact-display-only sensitivity.
- Category changes: retain history; compare all intervals with Level-2-stable intervals.
- Source caveat: observational scraped listing sample with uneven coverage and no transactions or campaign exposure.

## 7. Sanity checks

- Category snapshot totals must reconcile to 20,312.
- Positive, zero, and negative favorite intervals must sum to valid favorite intervals.
- Per-day changes require strictly positive elapsed days.
- Category breadth denominators must equal their displayed sample sizes.
- Exact-display-only results must exclude every compact interval.
- No output may contain revenue, orders, AOV, sales velocity, sales growth, category rank, or momentum score.
- Stop or narrow if category patterns reverse materially across exact-only, product-level, stable-category, or outlier sensitivity views.

## 8. Falsification and weakening conditions

- A category engagement pattern is strengthened when the median direction, breadth, and product-level sensitivity agree and the evidence base is broad.
- It is weakened when confidence intervals are wide, compact-display share is high, category/date coverage is sparse, or a few products dominate absolute change.
- It is not supportable when valid matched engagement intervals are absent or when sign/direction reverses under reasonable sensitivity definitions.
- The original platform-momentum claim is falsified for this dataset unless an independently verified sales/performance measure and representative coverage become available.

## 9. Caveats that must survive

- Sampled listing behavior is not platform-wide behavior.
- Favorites and ratings are engagement proxies, not purchases or demand.
- Compact favorite displays are approximate and interval-censored.
- Price is a displayed listing attribute, not realized revenue.
- The 20-day window cannot establish seasonality or durable growth.
- Association and co-movement do not establish causation.

## 10. Execution plan

1. Revalidate Phase 4 inputs and grains.
2. Produce facts tables before prose or charts.
3. Profile structure, coverage, prices, discounts, favorites, ratings, and intervals.
4. Build Level-2 evidence tables with explicit denominators.
5. Run exact-only, product-level, outlier, interval, and category-stability sensitivities.
6. Render exploratory figures with source/timeframe/denominator notes.
7. Inspect and critique every exported figure.
8. Assess the original and proposed questions without approving KPIs or recommendations.
