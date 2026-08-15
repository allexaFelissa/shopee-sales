# Phase 0 Report — Project Setup & Understanding

## 1. Dataset overview

The source contains 20,312 rows and 20 columns representing sampled Shopee Malaysia product listing snapshots. It covers 16,614 distinct product IDs and 20 consecutive observation dates from 2023-04-24 through 2023-05-13. No cleaned dataset, order table, or transaction table exists.

The raw CSV is still locked by another process. A safe relocation attempt failed, so it remains at `dataset/shopee_sales_data.csv`. It is the only copy and retains the expected SHA-256 hash.

## 2. Dataset grain

One row is best interpreted as one product listing observed on one crawl date. `(id, w_date)` is unique; `idElastic` is unique per snapshot. This is not order-line grain.

## 3. Available dimensions

- Product: persistent ID, URL, title, description, image, specification
- Category: complete pipe-delimited path with 24 broad level-2 categories
- Time: one snapshot date per day across a 20-day window
- Seller: 9,226 seller names
- Price: displayed actual and original listing prices
- Listing engagement: average rating, labeled cumulative rating/sold counts, favorites
- Geography: extremely limited; `delivery` is 67.71% missing and otherwise one value

No customer, order, transaction, verified campaign, or reliable geography dimension exists.

## 4. Available metrics

Displayed prices, observed listing counts, matched-product coverage, and changes in cumulative-looking listing counters are potentially measurable. True revenue, orders, AOV, customers, conversion, and verified period units are not directly measurable.

## 5. Time coverage

All 20 calendar dates are present, but daily rows vary from 201 to 3,727. Only six broad categories appear on all 20 days. The changing sample makes raw daily category totals incomparable without coverage controls.

## 6. Ability to measure category momentum

**Assessment: partially capable only under a narrowed, proxy-based interpretation; not currently capable of a reliable platform-wide sales momentum claim.**

Strengths:

- Stable broad category hierarchy is available.
- Snapshot dates allow temporal ordering.
- 3,070 products have repeated observations and cumulative-looking counts are mostly non-decreasing.
- All 24 broad categories can be observed; 23 have at least one repeated product.

Constraints:

- Only 18.48% of products repeat; the median repeated product has two dates spanning five days.
- The maximum product history is five observations.
- Phase 3 clarification: `total_sold` exactly equals populated `total_rating` on 20,301 rows. The remaining 11 are jointly missing-equivalent but use blank versus `N/A`; there are zero substantive inequalities. This still strongly suggests duplicate or mislabeled source data.
- There are no transaction or realized-revenue measures.
- Coverage differs greatly by date and category.

The most defensible future target is category-level **sampled listing traction**, conditional on resolving the sold-field defect and using matched-product cohorts.

## 7. Candidate momentum definitions

- Matched absolute sold-count velocity
- Relative matched growth with minimum-baseline safeguards
- Positive-movement breadth across eligible products
- Recent versus prior velocity/acceleration where history permits
- Transparent scale-growth-reliability scorecard

No definition is approved. A scorecard is preferable to an opaque composite at this stage.

## 8. Candidate KPIs

Candidate measures include tracked and matched product counts, coverage, net cumulative-count change, change velocity, positive-movement breadth, median product velocity, recent-versus-prior velocity, observed listing share, discount prevalence, a price-weighted traction proxy, and a momentum reliability tier. Complete definitions and limitations are in `docs/business_questions.md`.

## 9. Analytical risks

1. Populated `total_sold` and `total_rating` are exact duplicates; 11 additional rows are jointly missing-equivalent with different raw tokens.
2. Short 20-day history is inadequate for month-over-month, quarter, seasonality, or robust acceleration claims.
3. Uneven scraper coverage can create false category growth.
4. Most products occur once; matched evidence is selective.
5. Compact `k` values are rounded and can hide small interval changes.
6. Small starting counts can create extreme percentage growth.
7. Two cumulative counters decrease across repeated observations, requiring investigation.
8. Nineteen products change category paths over time.
9. Price fields contain zeros, missing values, and `999999999` placeholders.
10. Listing price times sold count is not realized revenue.
11. No campaign, margin, inventory, conversion, customer, refund, or cost data exists.
12. Recommendations may reflect the scraped sample rather than the platform.

## 10. Recommended analytical framework

```text
Source validity
    -> category and time support
    -> matched listing cohort
    -> interval-normalized movement
    -> growth breadth and robustness
    -> observed scale
    -> reliability assessment
    -> category evidence tier
    -> campaign test / priority logic
```

Any final recommendation must show performance, scale, breadth, and evidence reliability separately.

## 11. Limitations and Phase 1 priorities

Phase 1 should prioritize the `total_sold`/`total_rating` duplication, raw category-path inconsistencies, compact-number parsing, price placeholders, missingness, key stability, and changing daily/category coverage. Until those tests are complete, no category momentum ranking or campaign recommendation is justified.

## Phase boundary confirmation

No source values were changed; no rows were removed; no categories were standardized; no analytical dataset, chart, dashboard, ranking, or recommendation was created.
