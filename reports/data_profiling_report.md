# Phase 1 Data Profiling Report

## 1. Executive Summary

The complete 37,654,822-byte raw CSV was profiled read-only. It has 20,312 rows, 20 columns, and an in-memory deep footprint of 105,940,382 bytes. The best-supported grain is one Shopee Malaysia product listing snapshot per product and observation date.

The central category-momentum question remains **blocked as a sales question**. Phase 3 independently confirmed that `total_sold` and `total_rating` have identical populated strings on 20,301 rows; the other 11 rows are jointly missing-equivalent but encoded as blank versus `N/A`. Parsed values therefore match wherever present, with zero substantive inequalities. `total_sold` is classified **UNUSABLE for sales or momentum**, and `total_rating` is **UNVERIFIED** as a rating count. There is no independent order, transaction, revenue, or unit field.

Even if a cumulative metric is later validated, daily sampling varies from 201 to 3,727 products, only 18.48% of products repeat, and the history spans 20 days. Any later momentum analysis must use matched listings, normalize observation intervals, disclose coverage denominators, and enforce reliability gates.

## 2. Dataset Structure

| Measure | Result |
|---|---:|
| Rows | 20,312 |
| Columns | 20 |
| File size | 37,654,822 bytes |
| DataFrame memory, deep | 105,940,382 bytes |
| Distinct product IDs | 16,614 |
| Distinct snapshot IDs (`idElastic`) | 20,312 |
| Distinct dates | 20 |
| Exact duplicate rows | 0 |
| Duplicate `(id, w_date)` rows | 0 |
| Duplicate `idElastic` rows | 0 |

Keys and grain:

- Product key: `id` (identical to `idHash` in every row)
- Snapshot key: `(id, w_date)`; unique in all rows
- Snapshot record identifier: `idElastic`; unique in all rows
- Grain: product listing observed on a scrape date, not an order line

The complete column-level audit is reproducible in `outputs/tables/phase_1_field_profile.csv`.

## 3. Data Types and Cardinality

| Column | Raw type | Non-null | Missing | Unique | Cardinality |
|---|---:|---:|---:|---:|---:|
| `price_ori` | float64 | 20,112 | 200 | 2,964 | 14.59% |
| `delivery` | text | 6,558 | 13,754 | 1 | <0.01% |
| `item_category_detail` | text | 20,312 | 0 | 1,152 | 5.67% |
| `specification` | text | 20,301 | 11 | 19,264 | 94.84% |
| `title` | text | 20,312 | 0 | 16,430 | 80.89% |
| `w_date` | text | 20,312 | 0 | 20 | 0.10% |
| `link_ori` | text | 20,312 | 0 | 16,614 | 81.79% |
| `item_rating` | text | 20,301 | 11 | 23 | 0.11% |
| `seller_name` | text | 20,301 | 11 | 9,226 | 45.42% |
| `idElastic` | text | 20,312 | 0 | 20,312 | 100.00% |
| `price_actual` | float64 | 20,297 | 15 | 3,371 | 16.60% |
| `sitename` | text | 20,312 | 0 | 1 | <0.01% |
| `idHash` | text | 20,312 | 0 | 16,614 | 81.79% |
| `total_rating` | text | 20,301 | 11 | 1,329 | 6.54% |
| `id` | text | 20,312 | 0 | 16,614 | 81.79% |
| `total_sold` | text | 20,301 | 11 | 1,329 | 6.54% |
| `pict_link` | text | 20,312 | 0 | 16,584 | 81.65% |
| `favorite` | text | 19,242 | 1,070 | 1,267 | 6.24% |
| `timestamp` | int64 | 20,312 | 0 | 20 | 0.10% |
| `desc` | text | 20,312 | 0 | 16,577 | 81.61% |

`w_date`, rating/count fields, and favorites require typed analytical representations later, but no raw type was changed in Phase 1.

## 4. Missing Values

| Column | Missing | Missing % | Non-null | Pattern assessment |
|---|---:|---:|---:|---|
| `delivery` | 13,754 | 67.71% | 6,558 | Structural/nonrandom; only one non-null value and category/date rates vary strongly |
| `favorite` | 1,070 | 5.27% | 19,242 | Concentrated: 9.26% missing on 2023-05-07; 34.91% in Tickets & Vouchers |
| `price_ori` | 200 | 0.98% | 20,112 | Mild concentration: 2.79% on 2023-05-02; 2.66% in Home & Living |
| `price_actual` | 15 | 0.07% | 20,297 | Sparse; highest daily rate 0.74%, highest category rate 0.60% |
| `specification` | 11 | 0.05% | 20,301 | Sparse and often paired with missing seller |
| `item_rating` | 11 | 0.05% | 20,301 | Same missing-row family as sold/rating counters |
| `seller_name` | 11 | 0.05% | 20,301 | Sparse and often paired with missing specification |
| `total_rating` | 11 | 0.05% | 20,301 | Missing exactly where `total_sold` is missing |
| `total_sold` | 11 | 0.05% | 20,301 | Missing exactly where `total_rating` is missing |

There are 6,289 fully complete rows. The most common incomplete pattern is `delivery` alone (12,740 rows), followed by `delivery + favorite` (897 rows). A total of 11,555 distinct products have at least one row with a missing value, driven mostly by `delivery`.

Missingness is not safely assumed random. Geography and favorite coverage depend on category/date composition; sold/rating missingness is jointly structured.

## 5. Numeric Profiles

Numeric-like text was parsed in memory only for profiling. Compact suffixes use approximate multipliers (`k=1,000`).

| Field | Numeric count | Min | Q1 | Median | Q3 | Mean | Std. dev. | Max | Zero | IQR outliers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `price_ori` | 20,112 | 0.00 | 2.27 | 19.90 | 89.90 | 99,897.02 | 9,971,868.30 | 999,999,999 | 12 | 2,426 |
| `price_actual` | 20,297 | 0.00 | 1.00 | 10.00 | 69.00 | 98,930.85 | 9,926,321.93 | 999,999,999 | 12 | 2,356 |
| `item_rating` | 19,384 | 1.0 | 4.9 | 4.9 | 5.0 | 4.890 | 0.154 | 5.0 | 0 | 1,510 |
| `total_rating` | 20,301 | 0 | 37 | 205 | 1,000 | 1,561.21 | 6,191.35 | 407,400 | 658 | 2,699 |
| `total_sold` | 20,301 | 0 | 37 | 205 | 1,000 | 1,561.21 | 6,191.35 | 407,400 | 658 | 2,699 |
| `favorite` | 19,241 | 1 | 39 | 207 | 975 | 1,296.72 | 3,655.81 | 96,600 | 0 | 2,546 |

`item_rating` has another 917 rows labeled `No ratings yet` plus 11 true missing values. One non-null favorite value is `label_favorite` and is not numeric.

IQR outliers are flags, not errors. High sold/rating/favorite counts may be legitimate popular listings. Price outliers require context: many high prices are identifiable vehicle listings, while `999999999` and a `Free Gift (Not for Sale)` priced at 1,000,000 are strongly suspicious.

## 6. Categorical Profiles

Important categorical findings:

- `item_category_detail`: 1,152 paths; 447 occur <=5 times. No raw leading/trailing whitespace or case-only path collisions were detected.
- Parsed level 2: 24 values, all with more than five observations; no whitespace or case-only collisions.
- Parsed level 3: 222 values; seven occur <=5 times.
- Parsed level 4: 898 values; 344 occur <=5 times and 399 rows have no fourth level.
- `seller_name`: 9,226 values; 8,664 occur <=5 times. No whitespace or case-only collisions were detected.
- `title`: 16,430 values; five rows contain leading/trailing whitespace and nine case-only collision groups exist. Titles are not keys.
- `delivery`: one non-null value only (`KL City, Kuala Lumpur`).
- `sitename`: constant `shopee`.
- `item_rating`: 23 raw labels including numeric strings and `No ratings yet`.

Broad category frequency:

| Level-2 category | Snapshots | Days present | Repeated products |
|---|---:|---:|---:|
| Health & Beauty | 2,464 | 19 | 443 |
| Men Clothes | 2,458 | 20 | 527 |
| Women Clothes | 2,232 | 20 | 414 |
| Mobile & Accessories | 1,887 | 20 | 389 |
| Baby & Toys | 1,496 | 19 | 197 |
| Home & Living | 1,316 | 19 | 231 |
| Groceries & Pets | 1,130 | 20 | 148 |
| Home Appliances | 948 | 20 | 108 |
| Automotive | 822 | 18 | 135 |
| Sports & Outdoor | 788 | 18 | 89 |
| Women's Bags | 623 | 17 | 66 |
| Watches | 533 | 20 | 98 |
| Men's Bags & Wallets | 492 | 16 | 44 |
| Cameras & Drones | 452 | 13 | 13 |
| Women Shoes | 444 | 17 | 40 |
| Muslim Fashion | 419 | 14 | 18 |
| Fashion Accessories | 410 | 16 | 38 |
| Computer & Accessories | 391 | 17 | 19 |
| Games, Books & Hobbies | 345 | 13 | 22 |
| Men Shoes | 209 | 14 | 16 |
| Travel & Luggage | 154 | 10 | 11 |
| Gaming & Consoles | 148 | 9 | 7 |
| Tickets & Vouchers | 106 | 12 | 5 |
| Others | 45 | 2 | 0 |

The exact coverage table is `outputs/tables/phase_1_category_coverage.csv`.

## 7. Duplicate Analysis

- Exact duplicate rows: **0**
- Duplicate `(id, w_date)` rows: **0**
- Duplicate `idElastic` values: **0**
- Same seller + title + date with multiple product IDs: **30 groups / 62 rows**

The 30 potential groups have distinct product IDs and links. They may be separate listings, variants, relistings, or seller duplicates. They must not be removed automatically. Product URL, price, specification, and description should be reviewed during cleaning-rule design.

## 8. Outlier Analysis

Potential data errors:

- Two snapshots for product `0a069d...` have both prices equal to `999999999` and zero sold/rating count.
- A `Free Gift x 1 - Not for Sale` listing is priced at 1,000,000.
- Twelve rows have zero actual and original prices; most are ordinary listings and therefore are unlikely to be valid paid prices.
- One favorite string is nonnumeric.
- Two cumulative-counter intervals decrease.

Potential legitimate extremes:

- Vehicle listings between approximately 103,700 and 205,500 align with Automotive/Automobiles titles.
- A silver tea set is priced at 137,171.40 from an original 274,342.79; legitimacy cannot be proven from this file.
- Very large rating/sold/favorite counts may be plausible cumulative popularity, but compact rounding and field duplication prevent confident interpretation.

No outlier was removed or corrected.

## 9. Time Coverage

- First date: 2023-04-24
- Last date: 2023-05-13
- Distinct dates: 20
- Missing calendar dates: 0
- Invalid `w_date`: 0
- `timestamp` date equals `w_date`: 20,312/20,312

Feasibility by temporal method:

- Daily description: structurally possible but biased by changing coverage.
- Period-over-period: possible only for carefully matched cohorts and equal/exposure-normalized windows.
- Growth velocity: structurally possible for repeated products if a cumulative metric is validated.
- Acceleration: weak; only 535 products have >=3 observations and 86 have >=4.
- Sustained momentum: not supported convincingly by a 20-day window with sparse histories.
- Month-over-month, quarter-over-quarter, and seasonality: unsupported.

## 10. Daily Sampling Coverage

Raw means below are descriptive profile values, not comparable performance KPIs. Sold-count means are not trusted.

| Date | Observations/products | Categories | Sellers | Median price | Median sold/rating field |
|---|---:|---:|---:|---:|---:|
| 2023-04-24 | 276 | 20 | 262 | 7.50 | 637.0 |
| 2023-04-25 | 570 | 22 | 487 | 10.00 | 694.5 |
| 2023-04-26 | 581 | 21 | 506 | 7.95 | 447.0 |
| 2023-04-27 | 486 | 21 | 423 | 7.37 | 415.5 |
| 2023-04-28 | 629 | 21 | 542 | 5.99 | 713.5 |
| 2023-04-29 | 405 | 20 | 367 | 3.95 | 484.0 |
| 2023-04-30 | 511 | 21 | 458 | 5.99 | 468.5 |
| 2023-05-01 | 3,646 | 24 | 2,557 | 8.99 | 327.0 |
| 2023-05-02 | 466 | 19 | 422 | 4.95 | 511.5 |
| 2023-05-03 | 985 | 20 | 831 | 8.00 | 311.0 |
| 2023-05-04 | 201 | 11 | 144 | 87.00 | 55.0 |
| 2023-05-05 | 852 | 18 | 704 | 25.22 | 133.5 |
| 2023-05-06 | 747 | 19 | 641 | 5.49 | 140.0 |
| 2023-05-07 | 583 | 23 | 505 | 29.90 | 78.0 |
| 2023-05-08 | 774 | 18 | 670 | 39.90 | 167.5 |
| 2023-05-09 | 571 | 10 | 519 | 15.50 | 208.0 |
| 2023-05-10 | 904 | 12 | 781 | 23.90 | 168.0 |
| 2023-05-11 | 915 | 21 | 797 | 34.00 | 106.0 |
| 2023-05-12 | 2,483 | 20 | 1,823 | 29.00 | 124.0 |
| 2023-05-13 | 3,727 | 22 | 2,559 | 8.09 | 117.0 |

Coverage clearly changes in size and composition. For example, 2023-05-04 has only 201 products and 11 categories, while 2023-05-01 has 3,646 products across all 24 categories. Falling raw means over time cannot be interpreted as marketplace movement because the observed product mix changes.

The complete table, including means/medians for price, favorites, and the ambiguous counter, is `outputs/tables/phase_1_daily_coverage.csv`.

## 11. Snapshot Behavior and Category Stability

Observation frequency:

| Snapshots per product | Products |
|---:|---:|
| 1 | 13,544 |
| 2 | 2,535 |
| 3 | 449 |
| 4 | 79 |
| 5 | 7 |

There are 3,697 consecutive matched intervals. The ambiguous cumulative field increases in 1,707, is unchanged in 1,987, and decreases in 2. Interval lengths range from 1 to 19 days; only 725 are one-day intervals.

Category stability:

- 19 products change full category path.
- 8 cross broad level-2 categories; these are major analytical changes.
- 14 change level 3; after accounting for level-2 changes, six are within-level-2 subcategory changes.
- Five change only the detailed level-4 path.
- Examples of major changes include Baby & Toys -> Automotive, Home & Living -> Health & Beauty, and Mobile & Accessories -> Fashion Accessories.

The complete dated history is `outputs/tables/phase_1_category_changes.csv`. No category was reassigned.

## 12. Price Data Quality

- Missing original price: 200
- Missing actual price: 15
- Zero original price: 12
- Zero actual price: 12
- `999999999` original price: 2
- `999999999` actual price: 2
- Rows with both prices present: 20,101
- Actual below original: 10,770
- Actual equal to original: 9,331
- Actual above original: 0
- Valid positive-original discount pairs: 20,089
- Raw currency symbols in price fields: not applicable because pandas read them as numeric

For valid positive-original pairs, the displayed discount proxy has median 8.85%, Q3 50.0%, and 99th percentile 95.18%. These extreme markdowns require validation. Currency is not encoded explicitly; MYR is contextual, not proven metadata.

## 13. `total_sold` vs `total_rating` Investigation

### A. Exact equality

| Test | Count | Percentage |
|---|---:|---:|
| Equal including both missing | 20,312 | 100.00% |
| Unequal | 0 | 0.00% |
| Exact non-null raw-string equality | 20,301 | 99.95% of all rows |
| Both missing | 11 | 0.05% |
| Parsed numeric equality when non-null | 20,301 | 100.00% of non-null pairs |

### B. Distribution comparison

Both fields have exactly 1,329 non-null raw values and identical distributions:

- Minimum: 0
- Q1: 37
- Median: 205
- Q3: 1,000
- Mean: 1,561.21
- Standard deviation: 6,191.35
- 99th percentile: 21,900
- Maximum: 407,400
- Zero count: 658
- IQR outlier count: 2,699

### C. Related-field comparison

- Correlation with parsed favorites is approximately 0.670 for both duplicate fields.
- Correlation with numeric average rating is approximately 0.013 for both.
- Product URL, title, description, seller, price, and average rating do not independently contain verified sold or rating totals.
- No order, transaction, or external source is present.

The related fields show that the duplicate counter behaves like a cumulative popularity signal, but they cannot establish whether it is sold count, rating count, or another scraped value.

### D. Representative records

Examples include `179/179`, `17/17`, `8.1k/8.1k`, `185/185`, and `89/89` for rating/sold. Repeated products also move in lockstep, such as `209 -> 210 -> 214` in both fields and `23.1k -> 23.1k -> 23.2k` in both fields.

### E. Plausible explanations

| Explanation | Evidence assessment |
|---|---|
| Scraper extraction bug | Highly plausible: perfect raw equality and identical missingness across a large heterogeneous sample |
| Duplicated source field | Highly plausible for the same reason |
| One field mislabeled | Plausible; the file provides no source metadata to identify which label is correct |
| Actual business relationship | Highly implausible that every product has exactly one sale per rating at every snapshot |
| Project transformation issue | Not supported: equality exists in the immutable raw CSV before project transformations |
| Parsing issue | Ruled out as the sole cause: raw strings are already identical before parsing |

No explanation can be proven without scraper/source documentation or an independent dataset.

### F. Trust classification

- **`total_sold`: UNUSABLE as a sales, unit-growth, velocity, or momentum metric.** It may be retained as an ambiguous raw engagement counter, but must not be labeled sales.
- **`total_rating`: UNVERIFIED as a rating-count metric.** Its label is plausible, but there is no independent confirmation and it is duplicated into `total_sold`.

Consequently, the current dataset cannot safely support sales-based category momentum. A better source or field-level validation is required.

## 14. Momentum Feasibility

| Approach | Required fields | Advantages | Limitations and risks | Current support |
|---|---|---|---|---|
| Absolute velocity | Stable product, date, validated cumulative metric | Handles unequal observation dates when divided by days; scale-aware | `total_sold` unusable; compact rounding; selective cohort; changing categories | Structurally possible, substantively blocked |
| Relative growth | Same plus nonzero starting value | Compares products/categories of different sizes | Tiny baselines explode; zeros; interval-censoring; unusable sold field | Structurally possible, substantively blocked |
| Positive-movement breadth | Eligible matched products and validated change | Limits dominance by a few winners; denominator visible | Only 18.48% repeat; field invalid; eligibility choice matters | Partially supported after validation, currently blocked |
| Recent acceleration | >=3 timed observations per product and validated metric | Closest to “gaining” momentum | Only 535 products have >=3 observations; 20-day window; uneven intervals | Weak and unsuitable as the primary method |
| Scale + growth + reliability | Valid growth measure, matched breadth, observed scale, coverage diagnostics | Most transparent; separates signal from evidence quality | No valid sales metric; scale is sample coverage, not platform scale | Reliability/coverage components supported; growth component blocked |

If no independent sales field becomes available, the central question must be narrowed to **sampled listing representation and ambiguous engagement-counter movement**, which is not sufficient for confident campaign prioritization.

## 15. Data Quality Risks

The complete prioritized register is `reports/data_quality_issue_register.md`. The critical risks are:

1. Exact sold/rating duplication invalidates the sales measure.
2. Extreme daily/category coverage variation invalidates unmatched trend totals.
3. Short temporal depth and sparse repeats prevent robust sustained momentum.
4. Category changes, compact rounding, and price anomalies require explicit flags and governed rules.

## 16. Proposed Cleaning Requirements

Subject to user approval in Phase 2:

1. Preserve all raw columns and raw text; create cleaned fields rather than overwriting evidence.
2. Parse `w_date` and `timestamp`; verify exact agreement and retain one governed analytical date.
3. Split category paths into explicit levels with completeness and category-change flags.
4. Designate `id` as product key and `(id, date)` as snapshot key; document redundant `idHash` and unique `idElastic`.
5. Parse compact counts and favorites with raw-value, parsed-value, suffix/precision, and validity fields.
6. Keep `total_sold` excluded from sales KPIs unless independent validation is supplied.
7. Parse numeric `item_rating` while preserving `No ratings yet` as a distinct state.
8. Add missing, zero, sentinel, and context-review flags to prices; calculate discount only for approved valid pairs.
9. Do not impute `delivery`; exclude it from geographic analysis.
10. Retain potential duplicate groups pending record-level review; do not deduplicate by title alone.
11. Add category-path-change and negative-cumulative-delta flags; approve temporal assignment rules.
12. Build coverage and matched-cohort eligibility fields before any temporal aggregation.

## 17. Recommended Next Steps and Review Decisions

Before Phase 2, review and approve:

- Whether to seek source/scraper documentation or a replacement transaction/sales dataset.
- Whether `total_sold` should remain excluded from all sales metrics unless validated.
- Whether the project should explicitly target sampled listing traction if validation is impossible.
- Level 2 as the default category grain.
- Rules for compact-count parsing, category changes, zero/sentinel prices, missing values, and potential duplicates.
- Matched-cohort/reliability fields as mandatory future outputs.
- Closing the application holding the raw CSV so it can be hash-preservingly moved to `data/raw/`.

Phase 2 has not started.
