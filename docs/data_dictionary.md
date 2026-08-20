# Initial Data Dictionary

## Source identity

| Attribute | Observed value |
|---|---|
| Current path | `dataset/shopee_sales_data.csv` |
| Intended immutable path | `data/raw/shopee_sales_data.csv` |
| File size | 37,654,822 bytes |
| SHA-256 | `afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69` |
| Rows | 20,312 |
| Columns | 20 |
| Observed dates | 2023-04-24 through 2023-05-13, 20 consecutive calendar dates |

The intended source name `20240121_shopee_sample_data (1).csv` is not present. The only available CSV is the file above. It remains in the legacy location because another process has it open; relocation was attempted and safely skipped. No duplicate was created.

## Dataset grain

The best-supported row grain is **one scraped Shopee Malaysia product-listing snapshot on one observation date**.

Evidence:

- `(id, w_date)` is unique across all 20,312 rows.
- `idElastic` is unique per row and appears to identify a snapshot record.
- `id`, `idHash`, and `link_ori` identify 16,614 products; `id` equals `idHash` on every row.
- 3,070 products occur on multiple dates; 13,544 occur once.
- A row is not an order, order line, transaction, customer event, or verified daily sale.

This grain is provisional until source documentation is obtained, but it is much better supported than a transaction interpretation.

## Columns

All meanings are inferred from names and observed values; none should be treated as source-system documentation.

| Column | Raw pandas type | Missing | Unique non-null | Inferred meaning | Analytical relevance and risks |
|---|---:|---:|---:|---|---|
| `price_ori` | `float64` | 200 (0.98%) | 2,964 | Listed original/reference price | Candidate discount baseline. Contains zero and `999999999` placeholders/outliers. Currency is not explicitly encoded; Shopee Malaysia context suggests MYR but this must remain an assumption. |
| `delivery` | text | 13,754 (67.71%) | 1 | Delivery/location label | Only non-null value is `KL City, Kuala Lumpur`; unusable as broad geography without source clarification. |
| `item_category_detail` | text | 0 | 1,152 | Pipe-delimited category hierarchy | Main category source. Structure has 3-4 levels: `Shopee` plus 24 level-2, 222 level-3, and 898 level-4 values. Nineteen product IDs change full paths across snapshots. |
| `specification` | text | 11 (0.05%) | 19,264 | Scraped product specification text | May contain stock, origin, brand, and other attributes, but extracting them would be a later transformation with validation. |
| `title` | text | 0 | 16,430 | Product listing title | Useful for product identification and qualitative checking; not a stable unique key. |
| `w_date` | text | 0 | 20 | Snapshot observation date | Parses to consecutive dates from 2023-04-24 to 2023-05-13. It is observation/crawl time, not proven order date. |
| `link_ori` | text | 0 | 16,614 | Original product URL | One-to-one with `id` in this dataset; contains Shopee listing identifiers. |
| `item_rating` | text | 11 (0.05%) | 23 | Average displayed product rating | Mostly numeric text but includes `No ratings yet`; requires later parsing. |
| `seller_name` | text | 11 (0.05%) | 9,226 | Seller/shop username | Seller-level dimension; not a customer field. |
| `idElastic` | text | 0 | 20,312 | Snapshot/index record identifier | Unique row identifier, not the persistent product identifier. |
| `price_actual` | `float64` | 15 (0.07%) | 3,371 | Current displayed listing price | Candidate price measure. Contains zero and two `999999999` values. A listing price is not realized order revenue. |
| `sitename` | text | 0 | 1 | Platform name | Constant `shopee`; provides no within-file comparison. |
| `idHash` | text | 0 | 16,614 | Persistent hashed product identifier | Identical to `id` in every row; redundant unless source meaning differs. |
| `total_rating` | text | 11 (0.05%) | 1,329 | Labeled cumulative rating count | Compact text such as `1.1k`. It exactly equals populated `total_sold` on 20,301 rows; the other 11 rows are jointly missing but use different raw tokens (`N/A` versus blank). This still indicates duplication or a scrape-label error. |
| `id` | text | 0 | 16,614 | Persistent hashed product identifier | Best current product key together with snapshot date. Identical to `idHash`. |
| `total_sold` | text | 11 (0.05%) | 1,329 | Labeled cumulative sold count | Fully parseable with `k/m/b` notation. It exactly equals populated `total_rating` on 20,301 rows; the other 11 rows are jointly missing-equivalent. It must not be treated as verified sold units. |
| `pict_link` | text | 0 | 16,584 | Product image URL | Presentation/reference field; not a performance measure. |
| `favorite` | text | 1,070 (5.27%) | 1,267 | Displayed favorite count embedded in text | Potential popularity proxy after parsing; incomplete and likely cumulative. |
| `timestamp` | `int64` | 0 | 20 | Epoch-millisecond snapshot timestamp | Converts exactly to the same calendar dates as `w_date`; redundant time representation. |
| `desc` | text | 0 | 16,577 | Product description text | Qualitative product content; not a transaction measure. |

## Category hierarchy

The category path can support multiple levels after a later documented split:

- Level 1: `Shopee` (constant)
- Level 2: 24 broad marketplace categories; primary candidate for robust category analysis
- Level 3: 222 subcategories
- Level 4: 898 detailed categories, with many `Others` values and greater sparsity

Level 2 is the safest initial candidate because deeper levels fragment the short, uneven sample. No category standardization has been performed.

## Available and unavailable business fields

Available or potentially usable:

- Product ID and URL
- Snapshot date
- Category hierarchy
- Seller name
- Current and original listing price
- Labeled cumulative sold/rating counts, subject to a serious semantic defect
- Average rating and favorite count
- Partial listing-location/specification text

Not available:

- Order or transaction identifier
- Order date/time
- Customer identifier
- Order value or realized revenue
- Verified period units sold
- Refunds, cancellations, fees, or cost
- Campaign, promotion, impression, click, or conversion identifiers
- Reliable customer geography

## Phase boundary

This dictionary records raw observations only. No column was renamed, parsed in the source, standardized, imputed, removed, or corrected.

## Phase 1 verified profiling notes

- Deep in-memory DataFrame size is 105,940,382 bytes.
- `id` and `idHash` are identical in all 20,312 rows. `idElastic` is unique per snapshot, and `(id, w_date)` is a unique product-snapshot key.
- `w_date` parses without failure, covers 20 consecutive dates, and agrees with the epoch-millisecond `timestamp` date in every row.
- `total_sold` and `total_rating` contain identical populated strings on 20,301 rows. On the remaining 11, `total_sold` is blank while `total_rating` is `N/A`; both normalize to missing. There are zero substantive non-missing inequalities. Phase 3 corrected the earlier wording that called all 20,312 raw strings identical.
- Trust status: `total_sold` is **UNUSABLE as a sales/momentum metric**; `total_rating` is **UNVERIFIED as a rating-count metric**.
- `item_rating` contains 19,384 numeric values, 917 `No ratings yet` labels, and 11 missing values.
- `favorite` has 1,070 missing values and one nonnumeric non-null label (`label_favorite`).
- Price fields contain 12 zero pairs, two `999999999` pairs, missing values, legitimate-looking high-ticket vehicle listings, and other context-dependent extremes.
- Category stability is not perfect: 19 products change full path, including eight broad level-2 changes.
- Exact rows and `(id, w_date)` keys have no duplicates. Thirty seller-title-date groups covering 62 rows have multiple distinct product IDs/links and require review rather than automatic deletion.

Detailed evidence is in `reports/data_profiling_report.md`, `reports/data_quality_issue_register.md`, and the Phase 1 audit tables under `outputs/tables/`.

## Processed dataset

`data/processed/shopee_sales_cleaned.csv` preserves the 20 raw fields as source text and adds the following Phase 2 fields. CSV logical booleans are stored as `TRUE`/`FALSE`; empty derived cells mean the prerequisite was missing or invalid, never imputed.

### Audit and missingness

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `source_row_number` | integer | One-based source row position | Raw file order | 1-20,312 | Trace a processed row to its raw observation |
| `price_ori_missing_flag` | boolean text | Original price is blank or source `N/A` | `price_ori` missing-token check | TRUE/FALSE | Audit missing original price |
| `delivery_missing_flag` | boolean text | Delivery value is missing | `delivery` | TRUE/FALSE | Expose unusable geography coverage |
| `specification_missing_flag` | boolean text | Specification is missing | `specification` | TRUE/FALSE | Audit missing product detail |
| `item_rating_missing_flag` | boolean text | Average-rating display is missing | `item_rating` | TRUE/FALSE | Separate missing from unrated |
| `seller_name_missing_flag` | boolean text | Seller name is missing | `seller_name` | TRUE/FALSE | Audit seller completeness |
| `price_actual_missing_flag` | boolean text | Actual price is missing | `price_actual` | TRUE/FALSE | Audit price completeness |
| `total_rating_missing_flag` | boolean text | Labeled rating counter is missing | `total_rating` | TRUE/FALSE | Audit unverified counter completeness |
| `total_sold_missing_flag` | boolean text | Labeled sold counter is missing | `total_sold` | TRUE/FALSE | Audit unusable sales field completeness |
| `favorite_missing_flag` | boolean text | Favorite display is missing | `favorite` | TRUE/FALSE | Audit favorite coverage |

### Date fields

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `observation_date` | date text | Parsed listing snapshot date | Strict `%Y-%m-%d` parse of `w_date` | ISO date or empty | Governed analytical date |
| `observation_week_start` | date text | Monday of observation week | `observation_date - weekday` | ISO date or empty | Later weekly grouping without changing grain |
| `observation_month` | text | Observation year-month | `observation_date` | `YYYY-MM` or empty | Coverage labeling; not month-over-month evidence |
| `observation_day_of_week` | text | Calendar weekday name | `observation_date` | Monday-Sunday or empty | Coverage diagnostics |
| `date_parse_status` | category | Raw-date parse result | `w_date` | VALID/MISSING/INVALID | Date quality gate |
| `timestamp_date_match_flag` | boolean text | Epoch date equals parsed `w_date` | `timestamp`, `w_date` | TRUE/FALSE | Cross-check redundant dates |

### Category fields

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `category_level_1` | text | First trimmed path component | `item_category_detail` split on `|` | Raw-derived text/empty | Preserve hierarchy |
| `category_level_2` | text | Second trimmed path component | Same | 24 observed detailed categories/empty | Preserved source-derived detail category; not overwritten by the analytical grouping |
| `broad_product_category` | text | Deterministic mapping from `category_level_2` | `src/data/broad_product_category.py` | 12 governed analytical groups | Project-defined dashboard grouping, not an asserted official Shopee taxonomy |
| `category_level_3` | text | Third trimmed path component | Same | Raw-derived text/empty | Retain subcategory detail |
| `category_level_4` | text | Fourth trimmed path component | Same | Raw-derived text/empty | Retain detailed category where present |
| `category_path_clean` | text | Path with trimmed components and controlled delimiter spacing | Rejoin split raw path | Derived path/empty | Consistent comparison without overwriting raw path |
| `category_path_parse_status` | category | Hierarchy-level result | Component count | VALID_3_LEVEL/VALID_4_LEVEL/MISSING/MALFORMED_LEVEL_COUNT | Category structure validation |
| `primary_category_grain` | category | Governed main category level | Project rule | LEVEL_2 | Prevent accidental use of fragmented levels |

### Compact counters and trust controls

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `total_sold_parsed` | number | Approximate numeric display value | Parse raw `total_sold`; `k/m/b` multiplier | Nonnegative/empty | Audit only; not a sales metric |
| `total_sold_suffix` | text | Compact suffix | `total_sold` | empty/k/m/b | Record display encoding |
| `total_sold_precision_unit` | number | Smallest displayed increment implied by suffix/decimals | Example `23.1k` -> 100 | Positive/empty | Preserve rounding precision |
| `total_sold_compact_rounded_flag` | boolean text | Display used compact notation | `total_sold` suffix | TRUE/FALSE | Prevent false exactness |
| `total_sold_parse_status` | category | Parse result | `total_sold` | PARSED_EXACT_DISPLAY/PARSED_COMPACT_ROUNDED/MISSING/INVALID_FORMAT | Parse audit |
| `total_rating_parsed` | number | Approximate numeric display value | Parse raw `total_rating` | Nonnegative/empty | Unverified counter analysis only |
| `total_rating_suffix` | text | Compact suffix | `total_rating` | empty/k/m/b | Record display encoding |
| `total_rating_precision_unit` | number | Smallest displayed increment | `total_rating` suffix/decimals | Positive/empty | Preserve rounding precision |
| `total_rating_compact_rounded_flag` | boolean text | Display used compact notation | `total_rating` | TRUE/FALSE | Prevent false exactness |
| `total_rating_parse_status` | category | Parse result | `total_rating` | PARSED_EXACT_DISPLAY/PARSED_COMPACT_ROUNDED/MISSING/INVALID_FORMAT | Parse audit |
| `favorite_parsed` | number | Approximate favorite count extracted from label | `favorite` numeric token and compact parser | Nonnegative/empty | Secondary unverified engagement signal |
| `favorite_suffix` | text | Compact suffix | `favorite` | empty/k/m/b | Record display encoding |
| `favorite_precision_unit` | number | Smallest displayed increment | `favorite` suffix/decimals | Positive/empty | Preserve rounding precision |
| `favorite_compact_rounded_flag` | boolean text | Favorite display is compact/rounded | `favorite` | TRUE/FALSE | Prevent false exactness |
| `favorite_parse_status` | category | Favorite parse result | `favorite` | PARSED_EXACT_DISPLAY/PARSED_COMPACT_ROUNDED/MISSING/INVALID_LABEL/INVALID_FORMAT | Parse audit |
| `sold_rating_exact_match_flag` | boolean text | Raw sold and rating strings are identical | `total_sold == total_rating` | TRUE/FALSE | Expose critical duplication |
| `total_sold_metric_status` | category | Trust classification | Phase 1 evidence | UNVERIFIED_UNUSABLE_AS_SALES_METRIC | Block unsupported sales use |
| `total_rating_metric_status` | category | Trust classification | Phase 1 evidence | UNVERIFIED_DUPLICATES_TOTAL_SOLD | Block unsupported interpretation |

### Average rating

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `item_rating_numeric` | number | Parsed average rating | Numeric parse when valid | 1-5 or empty | Valid average-rating analysis |
| `item_rating_status` | category | Rating-display state | `item_rating` | VALID/NO_RATINGS_YET/MISSING/INVALID_LABEL/OUT_OF_RANGE | Separate unrated, missing, and invalid |

### Price and discount fields

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `price_ori_clean` | number | Usable original displayed price | Numeric raw value only when status VALID | Positive number/empty | Safe price-derived analysis |
| `price_ori_status` | category | Original-price quality class | Missing, zero, sentinel, >=1M rule | VALID/MISSING/INVALID_FORMAT/ZERO/SENTINEL_999999999/SUSPICIOUS_HIGH_GE_1000000 | Explicit treatment |
| `price_actual_clean` | number | Usable current displayed price | Numeric raw value only when status VALID | Positive number/empty | Safe price-derived analysis |
| `price_actual_status` | category | Actual-price quality class | Same rule | Same values as original-price status | Explicit treatment |
| `price_ori_statistical_outlier_flag` | boolean text | Clean original price falls outside global 1.5-IQR fences | `price_ori_clean` | TRUE/FALSE | Review flag; never automatic removal |
| `price_actual_statistical_outlier_flag` | boolean text | Clean actual price falls outside global 1.5-IQR fences | `price_actual_clean` | TRUE/FALSE | Review flag; never automatic removal |
| `price_pair_status` | category | Pair eligibility for discount | Both statuses and price ordering | VALID_COMPARABLE/INVALID_COMPONENT/ACTUAL_ABOVE_ORIGINAL/UNCLASSIFIED | Guard discount calculations |
| `discount_amount` | number | Original minus actual displayed price | Valid comparable pair | Nonnegative/empty | Displayed markdown proxy, not revenue |
| `discount_pct` | number | Discount amount / original price x 100 | Valid comparable pair | 0-100/empty | Comparable displayed markdown proxy |
| `price_currency_status` | category | Currency evidence status | Marketplace context only | UNVERIFIED_CONTEXT_SUGGESTS_MYR | Prevent unsupported currency certainty |

### Duplicate-review fields

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `exact_duplicate_flag` | boolean text | Row duplicates all 20 raw columns | Full-row duplicate test | TRUE/FALSE | Preserve and identify exact duplicates |
| `snapshot_key_duplicate_flag` | boolean text | Duplicate `(id,w_date)` | Key duplicate test | TRUE/FALSE | Grain validation |
| `duplicate_review_group_id` | text | Deterministic group for same seller/title/date with multiple IDs | SHA-256 prefix of group fields | `DUP-<12 hex>`/empty | Manual review without deletion |
| `duplicate_review_flag` | boolean text | Row belongs to potential duplicate group | Group membership | TRUE/FALSE | Prevent silent deduplication |

### Product history, intervals, and category changes

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `product_observation_count` | integer | Snapshots for product | Group by `id` | 1-5 | Matched-cohort support |
| `product_first_observation_date` | date text | First observed date | Min date by `id` | ISO date | Cohort history |
| `product_last_observation_date` | date text | Last observed date | Max date by `id` | ISO date | Cohort history |
| `product_observation_span_days` | integer | Days from first to last snapshot | Date difference by `id` | 0-19 | Exposure context |
| `matched_product_flag` | boolean text | Product has more than one snapshot | Observation count >1 | TRUE/FALSE | Identify matched products |
| `observation_sequence` | integer | Chronological snapshot position within product | Sort by product/date/source row | 1-5 | Deterministic interval construction |
| `previous_observation_date` | date text | Prior snapshot date for product | Group lag | ISO date/empty | Interval audit |
| `observation_interval_days` | integer | Days since prior snapshot | Date difference | 1-19/empty | Normalize future interval methods |
| `unverified_counter_previous` | number | Prior parsed `total_sold` display | Lag of `total_sold_parsed` | Nonnegative/empty | Audit ambiguous counter only |
| `unverified_counter_change` | number | Current minus prior ambiguous counter | `total_sold_parsed` difference | Number/empty | Detect direction/anomalies; not sales |
| `negative_change_flag` | boolean text | Ambiguous counter decreased | Change <0 | TRUE/FALSE | Preserve cumulative anomaly |
| `cumulative_change_status` | category | Displayed counter interval state | Prior/current/change | FIRST_OBSERVATION/MISSING_UNVERIFIED_COUNTER/DECREASE/NO_CHANGE/INCREASE/UNCLASSIFIED | Safe interval description |
| `movement_analysis_eligibility_status` | category | Current downstream movement gate | Prior date and field validity | NO_PRIOR_OBSERVATION/MISSING_UNVERIFIED_COUNTER/BLOCKED_COUNTER_UNVERIFIED | Prevent momentum use |
| `acceleration_structure_flag` | boolean text | Product has >=3 snapshots | Observation count | TRUE/FALSE | Structural availability only, not metric approval |
| `product_category_change_flag` | boolean text | Product has >1 full path | Distinct clean paths by `id` | TRUE/FALSE | Category stability |
| `product_category_level2_change_flag` | boolean text | Product crosses broad categories | Distinct level-2 values by `id` | TRUE/FALSE | Main-grain stability |
| `product_category_path_count` | integer | Distinct full paths for product | Group by `id` | 1-3 | Quantify instability |
| `product_category_level2_count` | integer | Distinct level-2 categories for product | Group by `id` | 1-3 | Quantify broad changes |
| `previous_category_path` | text | Prior cleaned category path | Product lag | Path/empty | Audit path transition |
| `previous_category_level_2` | text | Prior broad category | Product lag | Category/empty | Audit broad transition |
| `category_changed_from_previous_flag` | boolean text | Full path differs from prior snapshot | Path comparison | TRUE/FALSE | Locate exact transition rows |
| `category_level2_changed_from_previous_flag` | boolean text | Broad category differs from prior snapshot | Level-2 comparison | TRUE/FALSE | Locate main-grain transitions |

### Coverage fields

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `daily_observation_count` | integer | Snapshot rows on observation date | Group by date | Positive integer | Expose daily scraper coverage |
| `daily_unique_product_count` | integer | Distinct products on date | Date + `id` | Positive integer | Coverage denominator |
| `daily_category_level2_count` | integer | Broad categories present on date | Date + level 2 | 1-24 | Composition diagnostic |
| `daily_seller_count` | integer | Distinct sellers on date | Date + seller | Positive integer | Coverage diagnostic |
| `category_date_observation_count` | integer | Snapshots in row's category/date | Level 2 + date | Positive integer | Category-time denominator |
| `category_date_unique_product_count` | integer | Distinct products in category/date | Level 2 + date + `id` | Positive integer | Category-time coverage |
| `category_total_observation_count` | integer | All snapshots in row's category | Level 2 | Positive integer | Observed category scale |
| `category_unique_product_count` | integer | Distinct products in row's category | Level 2 + `id` | Positive integer | Sample scale |
| `category_repeated_product_count` | integer | Distinct repeated products observed in row's category | Level 2 + matched IDs | 0 or positive integer | Matched evidence base |

### Statistical review flags

| Field | Type | Definition | Source/transformation | Allowed values | Purpose |
|---|---|---|---|---|---|
| `unverified_counter_statistical_outlier_flag` | boolean text | Parsed ambiguous counter outside 1.5-IQR fences | `total_sold_parsed` | TRUE/FALSE | Sensitivity/review only |
| `favorite_statistical_outlier_flag` | boolean text | Parsed favorite count outside 1.5-IQR fences | `favorite_parsed` | TRUE/FALSE | Sensitivity/review only |
| `item_rating_statistical_outlier_flag` | boolean text | Numeric average rating outside 1.5-IQR fences | `item_rating_numeric` | TRUE/FALSE | Distribution review only |

No derived field represents verified units sold, orders, revenue, AOV, conversion, customers, or campaign performance.

## Phase 4 analytical tables

Phase 4 keeps `shopee_sales_cleaned.csv` as the complete validated audit dataset and creates narrower analytical interfaces with plain snake_case names. Counts refer to **sampled/observed listings**, never the full Shopee platform.

### Table registry and grains

| Table | Grain | Primary key | Rows | Purpose |
|---|---|---|---:|---|
| `shopee_product_snapshots.csv` | One sampled product-listing snapshot on one observation date | (`product_id`, `observation_date`) | 20,312 | Main row-level analytical interface |
| `shopee_matched_observations.csv` | One consecutive observation interval for a repeated product | (`product_id`, `current_observation_date`) | 3,698 | Validity-aware price and engagement comparisons; no sales movement |
| `shopee_product_coverage.csv` | One sampled product | `product_id` | 16,614 | Product history and analytical coverage evidence |
| `shopee_daily_coverage.csv` | One observation date | `observation_date` | 20 | Daily sampling and field-validity coverage |
| `shopee_category_daily_coverage.csv` | One Level-2 category on one study date | (`category_level_2`, `observation_date`) | 480 | Complete 24 × 20 coverage grid, including explicit zero-observation cells |
| `shopee_category_level2_summary.csv` | One Level-2 category | `category_level_2` | 24 | Descriptive structure, coverage, valid price, and engagement summaries; no ranking |

### Naming and value conventions

- `sampled_*` and `observed_*` describe this dataset only, not platform totals.
- `*_count` is a row or distinct-entity count at the table's declared grain.
- `*_rate_percent` is a 0–100 percentage with its denominator stated by the name and table documentation.
- `*_valid_flag` is `TRUE` only when the Phase 2 status permits the corresponding value.
- `*_approx` preserves compact-display uncertainty and must not be presented as exact.
- Empty analytical values mean the comparison or source value was invalid, missing, or not applicable; they are never silently converted to zero.
- `coverage_reliability_tier_status` is always `NOT_ASSIGNED_REQUIRES_APPROVED_THRESHOLDS`; Phase 4 assigns no HIGH/MEDIUM/LOW tier.

### `shopee_product_snapshots.csv`

Identifiers and time:
`source_row_number`, `product_id`, `observation_date`, `observation_week_start`, `observation_month`, `observation_day_of_week`, `product_title`, `seller_name`, `product_url`.

Category:
`category_level_2`, `broad_product_category`, `category_level_3`, `category_level_4`, `category_path`, `category_path_status`, `category_changed_over_time_flag`, `level2_category_changed_over_time_flag`, `category_changed_from_previous_observation_flag`, `level2_category_changed_from_previous_observation_flag`.

Price:
`actual_price`, `actual_price_status`, `actual_price_valid_flag`, `actual_price_outlier_flag`, `original_price`, `original_price_status`, `original_price_valid_flag`, `original_price_outlier_flag`, `price_pair_status`, `discount_valid_flag`, `discount_amount`, `discount_percent`, `currency_status`. Clean price fields are populated only for Phase 2 `VALID` statuses; discount fields require a `VALID_COMPARABLE` pair.

Engagement:
`favorite_count_approx`, `favorite_status`, `favorite_valid_flag`, `favorite_is_rounded_flag`, `favorite_precision_unit`, `favorite_outlier_flag`, `average_rating`, `average_rating_status`, `average_rating_valid_flag`, `average_rating_outlier_flag`.

Coverage, quality, and safeguards:
`product_observation_count`, `product_first_observation_date`, `product_last_observation_date`, `product_observation_span_days`, `product_observed_date_rate_percent`, `repeated_product_flag`, `observation_sequence`, `previous_observation_date`, `days_since_previous_observation`, `has_three_or_more_observations_flag`, `duplicate_review_flag`, `duplicate_review_group_id`, `negative_unverified_counter_change_flag`, `unverified_counter_change_status`, `movement_analysis_eligibility_status`, `total_sold_metric_status`, `total_rating_metric_status`, `daily_sampled_snapshot_count`, `daily_sampled_unique_product_count`, `daily_sampled_category_count`, `daily_sampled_seller_count`, `category_day_sampled_snapshot_count`, `category_day_sampled_unique_product_count`, `coverage_reliability_tier_status`.

### `shopee_matched_observations.csv`

Lineage and grain:
`product_id`, `previous_observation_date`, `current_observation_date`, `previous_source_row_number`, `current_source_row_number`, `elapsed_days`, `current_observation_sequence`, `product_title`, `seller_name`, `product_url`.

Category comparison:
`previous_category_level_2`, `current_category_level_2`, `previous_broad_product_category`, `current_broad_product_category`, `previous_category_level_3`, `current_category_level_3`, `previous_category_level_4`, `current_category_level_4`, `previous_category_path`, `current_category_path`, `category_path_stable_flag`, `level2_category_stable_flag`, `broad_product_category_stable_flag`, `category_changed_over_time_flag`, `level2_category_changed_over_time_flag`.

Price comparison:
`previous_actual_price`, `current_actual_price`, `previous_actual_price_status`, `current_actual_price_status`, `actual_price_comparison_status`, `actual_price_change`, `actual_price_change_percent`, `previous_discount_amount`, `current_discount_amount`, `previous_discount_percent`, `current_discount_percent`, `discount_comparison_status`, `discount_amount_change`, `discount_percentage_point_change`. Changes exist only when both observations pass the relevant validity rule.

Engagement comparison:
`previous_favorite_count_approx`, `current_favorite_count_approx`, `previous_favorite_status`, `current_favorite_status`, `favorite_comparison_status`, `favorite_count_change_approx`, `previous_average_rating`, `current_average_rating`, `previous_average_rating_status`, `current_average_rating_status`, `average_rating_comparison_status`, `average_rating_change`.

Coverage, quality, and safeguards:
`product_observation_count`, `product_observation_span_days`, `product_observed_date_rate_percent`, `current_daily_sampled_snapshot_count`, `current_category_day_sampled_snapshot_count`, `previous_duplicate_review_flag`, `current_duplicate_review_flag`, `negative_unverified_counter_change_flag`, `unverified_counter_change_status`, `movement_analysis_eligibility_status`, `sales_movement_metric_status`, `total_sold_metric_status`, `total_rating_metric_status`, `coverage_reliability_tier_status`.

### `shopee_product_coverage.csv`

Identity/history:
`product_id`, `product_url`, `latest_product_title`, `latest_seller_name`, `first_observation_date`, `last_observation_date`, `observation_count`, `observed_date_count`, `observation_span_days`, `observed_date_rate_percent`, `matched_interval_count`, `minimum_interval_days`, `median_interval_days`, `maximum_interval_days`, `repeated_product_flag`, `has_three_or_more_observations_flag`, `has_four_or_more_observations_flag`.

Category and valid-field coverage:
`first_category_level_2`, `latest_category_level_2`, `first_broad_product_category`, `latest_broad_product_category`, `distinct_category_path_count`, `distinct_level2_category_count`, `distinct_broad_product_category_count`, `category_path_stable_flag`, `level2_category_stable_flag`, `broad_product_category_stable_flag`, `valid_actual_price_observation_count`, `valid_actual_price_observation_rate_percent`, `valid_discount_observation_count`, `valid_discount_observation_rate_percent`, `valid_favorite_observation_count`, `valid_favorite_observation_rate_percent`, `valid_average_rating_observation_count`, `valid_average_rating_observation_rate_percent`, `any_duplicate_review_flag`, `total_sold_metric_status`, `total_rating_metric_status`, `coverage_reliability_tier_status`.

### `shopee_daily_coverage.csv`

Columns:
`observation_date`, `sampled_snapshot_count`, `sampled_unique_product_count`, `sampled_category_level2_count`, `sampled_seller_count`, `repeated_product_snapshot_count`, `repeated_product_snapshot_rate_percent`, `valid_actual_price_snapshot_count`, `valid_actual_price_snapshot_rate_percent`, `valid_favorite_snapshot_count`, `valid_favorite_snapshot_rate_percent`, `valid_average_rating_snapshot_count`, `valid_average_rating_snapshot_rate_percent`, `matched_interval_count_ending_on_date`, `study_date_count`.

### `shopee_category_daily_coverage.csv`

Columns:
`category_level_2`, `observation_date`, `sampled_snapshot_count`, `sampled_unique_product_count`, `sampled_seller_count`, `repeated_product_snapshot_count`, `valid_actual_price_snapshot_count`, `valid_discount_snapshot_count`, `displayed_discount_snapshot_count`, `valid_favorite_snapshot_count`, `valid_average_rating_snapshot_count`, `matched_interval_count_ending_on_date`, `category_observed_on_date_flag`, `repeated_product_snapshot_rate_percent`, `valid_actual_price_snapshot_rate_percent`, `valid_favorite_snapshot_rate_percent`, `valid_average_rating_snapshot_rate_percent`.

Zero counts in this table represent a category/date combination with no sampled observation. Percentage fields remain empty when the sampled-snapshot denominator is zero.

### `shopee_category_level2_summary.csv`

Sample structure and coverage:
`category_level_2`, `sampled_snapshot_count`, `sampled_unique_product_count`, `sampled_seller_count`, `sampled_snapshot_share_percent`, `repeated_product_count`, `repeated_product_rate_percent`, `matched_interval_count`, `dates_observed_count`, `date_coverage_rate_percent`, `minimum_daily_sampled_snapshot_count`, `median_daily_sampled_snapshot_count`, `average_daily_sampled_snapshot_count`, `maximum_daily_sampled_snapshot_count`.

Valid price and discount summaries:
`valid_actual_price_snapshot_count`, `valid_actual_price_snapshot_rate_percent`, `median_actual_price`, `average_actual_price`, `valid_original_price_snapshot_count`, `median_original_price`, `average_original_price`, `valid_discount_snapshot_count`, `displayed_discount_snapshot_count`, `displayed_discount_prevalence_percent`, `median_discount_percent`.

Valid engagement and quality summaries:
`valid_favorite_snapshot_count`, `valid_favorite_snapshot_rate_percent`, `median_favorite_count_approx`, `average_favorite_count_approx`, `rounded_favorite_snapshot_count`, `valid_average_rating_snapshot_count`, `valid_average_rating_snapshot_rate_percent`, `median_average_rating`, `average_average_rating`, `category_changed_product_count`, `level2_category_changed_product_count`, `duplicate_review_snapshot_count`, `coverage_reliability_tier_status`, `performance_metric_status`.

`performance_metric_status` is always `NO_VERIFIED_SALES_OR_REVENUE_METRIC`. The table is alphabetical by category and contains no rank, recommendation, momentum score, or platform-wide estimate.

## Phase 5 exploratory output dictionary

Phase 5 does not add reusable datasets under `data/processed/`. It creates facts and diagnostics under `outputs/tables/`; these can be regenerated from the six Phase 4 tables.

| File | Grain / key | Purpose |
|---|---|---|
| `phase_5_descriptive_statistics.csv` | Source table + field | Count, missingness, robust and conventional descriptive statistics. |
| `phase_5_product_observation_distribution.csv` | Product observation count | Product-history depth and interval contribution. |
| `phase_5_interval_distribution.csv` | Elapsed days | Matched-interval frequency and cumulative share. |
| `phase_5_daily_coverage_diagnostics.csv` | Observation date | Daily sample volume and change diagnostics; not performance growth. |
| `phase_5_category_evidence.csv` | Level-2 category | Joined coverage, price, engagement, uncertainty, concentration, and matched evidence. |
| `phase_5_price_sensitivity_by_category.csv` | Level-2 category | Mean/median/trimmed/outlier-aware displayed-price and discount summaries. |
| `phase_5_engagement_sensitivity_by_category.csv` | Level-2 category + sensitivity scenario | Favorite movement under interval, exact-display, category-stable, outlier-endpoint, and product-level views. |
| `phase_5_category_change_impact.csv` | Stability dimension + stable/changed group | Matched comparison evidence for Level-2 and full-path changes. |
| `phase_5_big_question_feasibility.csv` | Feasibility component | Support status for each part of the original and proposed questions. |
| `phase_5_figure_review.csv` | Figure file | Chart question, encodings, denominator, semantic control, and inspection status. |
| `phase_5_validation_results.csv` | Validation check | Independent Phase 5 pass/fail evidence. |

Key Phase 5 analytical fields:

- `favorite_change_per_day_approx`: displayed favorite-count change divided by positive elapsed days; approximate when compact display values are present.
- `positive_movement_breadth_percent`: positive valid units divided by all valid units within the stated scenario. The unit is either matched interval or one product-level median, as identified by `unit_of_analysis`.
- `positive_breadth_wilson_95_lower_percent` / `upper_percent`: Wilson interval for the positive-breadth proportion; descriptive uncertainty, not a causal confidence claim.
- `top_product_share_of_absolute_favorite_change_percent`: largest product's absolute favorite-change contribution divided by total absolute change in that category/scenario.
- `sensitivity_scenario`: `ALL_VALID_INTERVALS`, `EXACT_DISPLAY_INTERVALS_ONLY`, `LEVEL2_STABLE_INTERVALS_ONLY`, `EXCLUDE_FAVORITE_OUTLIER_ENDPOINTS`, or `PRODUCT_LEVEL_MEDIAN_DAILY_CHANGE`.

All `favorite_*_approx` fields remain engagement-display proxies. They are not sales, revenue, demand, or final traction KPIs. Phase 5 assigns no reliability tier, rank, momentum score, or recommendation.
