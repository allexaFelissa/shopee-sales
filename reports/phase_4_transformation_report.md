# Phase 4 Data Transformation Report

## 1. Objective

Transform the validated 20,312-row product-listing snapshot dataset into clearly grained, reproducible analytical structures for later EDA and methodology review. Phase 4 creates structural, coverage, valid-price, and engagement interfaces only. It does not answer the Big Question, define momentum, rank categories, or create campaign recommendations.

## 2. Source dataset

| Attribute | Validated value |
|---|---|
| Source | `data/processed/shopee_sales_cleaned.csv` |
| Grain | One product-listing snapshot on one observation date |
| Key | (`id`, `w_date`) |
| Rows / columns | 20,312 / 111 |
| SHA-256 | `407c6f5e654283461c8eba20a3a1721f5105650212e92ae99206ea6dbadd199d` |
| Date range | 2023-04-24 through 2023-05-13 |
| Products / Level-2 categories | 16,614 / 24 |

The immutable raw source also retained SHA-256 `afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69` before and after transformation.

## 3. Analytical grains

| Analytical grain | Definition |
|---|---|
| Snapshot grain | One sampled product listing on one observation date |
| Matched-observation grain | One interval from a product's immediately preceding snapshot to its current snapshot |
| Product grain | One persistent `product_id` with history and valid-field coverage |
| Daily grain | One of the 20 observation dates |
| Category-day grain | One Level-2 category on one study date, including zero-observation combinations |
| Category-summary grain | One Level-2 category across the full sampled window |

## 4. Tables created

| Table | Grain | Primary key | Rows | Columns |
|---|---|---|---:|---:|
| `shopee_product_snapshots.csv` | Product snapshot | (`product_id`, `observation_date`) | 20,312 | 65 |
| `shopee_matched_observations.csv` | Consecutive product interval | (`product_id`, `current_observation_date`) | 3,698 | 62 |
| `shopee_product_coverage.csv` | Product | `product_id` | 16,614 | 35 |
| `shopee_daily_coverage.csv` | Observation date | `observation_date` | 20 | 15 |
| `shopee_category_daily_coverage.csv` | Level-2 category by date | (`category_level_2`, `observation_date`) | 480 | 17 |
| `shopee_category_level2_summary.csv` | Level-2 category | `category_level_2` | 24 | 39 |

All columns use direct snake_case names such as `product_id`, `actual_price`, `elapsed_days`, `sampled_snapshot_count`, and `valid_favorite_snapshot_rate_percent`. Exact ordered schemas and field groups are documented in `docs/data_dictionary.md` and the Phase 4 manifest.

## 5. Table schemas

### Product snapshots

- Identifiers/time: source row, product, date/week/month/weekday, title, seller, URL.
- Category: Levels 2–4, clean path, history and transition flags.
- Price: valid actual/original price, status, validity, outlier, price-pair, discount, and currency-status fields.
- Engagement: approximate favorites with precision/status plus valid average rating.
- Coverage/quality: product history, intervals, duplicate flags, category changes, sampling counts, movement gate, and counter trust statuses.

### Matched observations

- Previous/current source rows and dates, elapsed days, and sequence.
- Previous/current categories with path and Level-2 stability.
- Validity-gated actual-price and displayed-discount comparisons.
- Validity-gated approximate-favorite and average-rating comparisons.
- Product, daily, and category-day coverage context.
- Explicit sales-movement and counter-trust restrictions.

### Product coverage

- Observation count, date count/rate, first/last date, span, interval counts and gaps.
- First/latest category and category-stability evidence.
- Valid actual-price, discount, favorite, and rating observation counts/rates.
- Duplicate-review and counter-trust status.

### Daily and category coverage

- Sampled snapshot, product, seller, category, repeat, valid-field, and interval counts.
- Rates use sampled snapshots for the corresponding date/category-date denominator.
- The category-day table explicitly represents all 24 × 20 combinations.

### Level-2 category summary

- Sample structure and time coverage.
- Valid listing-price and displayed-discount summaries.
- Valid approximate-favorite and average-rating summaries.
- Category-change and duplicate-review evidence.
- Unassigned reliability-tier and unavailable-performance statuses.

## 6. Transformation logic

1. Verify the validated processed SHA-256 and raw SHA-256.
2. Select only downstream-useful columns and rename them to clear analytical names.
3. Create explicit validity flags from already validated Phase 2 statuses.
4. Sort each product chronologically and pair every non-first snapshot with its immediate predecessor.
5. Calculate price, discount, favorite, and average-rating changes only when both observations pass their respective validity requirements.
6. Aggregate observation and valid-field coverage to product and daily grains.
7. Construct a complete 24-category × 20-date grid and fill absent observed counts with zero while leaving zero-denominator percentages empty.
8. Aggregate descriptive structural, price, engagement, and quality evidence to Level 2.
9. Apply hard business-safety assertions and reconcile every table to the validated source.

## 7. Filtering logic

- Product snapshots: no filtering; all 20,312 validated rows are retained.
- Matched observations: the first snapshot of each product is intentionally excluded because it has no previous observation. This produces `20,312 - 16,614 = 3,698` intervals.
- Product coverage: all products retained.
- Daily coverage: all 20 study dates retained.
- Category daily coverage: all 480 possible Level-2/date combinations retained; 97 have zero sampled snapshots and 383 have observed data.
- Category summary: all 24 Level-2 categories retained.

No row was filtered because of price, engagement, duplicate, category-change, negative-change, or outlier status. Invalid values remain represented through counts and status fields rather than converted to zero.

## 8. Derived analytical fields

Phase 4 adds only structural or validity-aware fields:

- Clear identifiers and renamed analytical values.
- Product observed-date rate: observed dates divided by the 20-date study window.
- Previous/current category, price, discount, favorite, and average-rating values.
- Valid comparison status and corresponding change only when both observations qualify.
- Product, date, category-date, and category-window coverage counts and rates.
- Sampled-snapshot share by Level-2 category.
- Descriptive median/mean values for valid prices, displayed discounts, approximate favorites, and average ratings.
- Explicit unassigned reliability and unavailable-performance status fields.

None is a final KPI.

## 9. Coverage handling

Coverage remains observable evidence rather than a correction or weight:

- 16,614 products; 3,070 repeat and 13,544 appear once.
- 3,698 matched intervals.
- Product observation counts reconcile to 20,312 source rows.
- Daily sampled-snapshot counts reconcile to 20,312 rows.
- Category-day sampled-snapshot counts reconcile to 20,312 rows.
- Category-summary sampled-snapshot counts reconcile to 20,312 rows.
- Level-2 sampled-snapshot shares sum to 100% within floating-point serialization tolerance.

No observation was weighted, duplicated, or treated as representative of the whole platform.

## 10. Reliability handling

Phase 4 exposes evidence needed for a later reliability framework: observation count, date rate, span, interval count/gaps, repeated-product availability, category-date coverage, category stability, duplicate review, and valid-field coverage.

No HIGH/MEDIUM/LOW/INSUFFICIENT tier was assigned because no threshold methodology has been approved. Every applicable table uses `coverage_reliability_tier_status = NOT_ASSIGNED_REQUIRES_APPROVED_THRESHOLDS`.

## 11. Price handling

- Snapshot prices use only Phase 2 cleaned values with `VALID` status.
- Sentinel, missing, zero, suspicious-high, and invalid values remain empty in analytical price fields.
- Discounts require a `VALID_COMPARABLE` original/actual pair.
- Matched actual-price change is available for 3,690 intervals; 8 are not comparable.
- Matched discount change is available for 3,609 intervals; 89 are not comparable.
- Price and discount values describe displayed listing data, not realized revenue or transaction value.

## 12. Engagement handling

- Favorites are preserved as approximate displayed counts with compact-rounding status.
- Favorite comparisons: 2,603 exact-display intervals, 886 valid intervals containing at least one compact display, and 209 non-comparable intervals.
- Average-rating comparisons: 3,500 valid and 198 missing/unrated non-comparable intervals.
- Missing or invalid engagement is never converted to zero.
- No causal or performance meaning is assigned to favorite or rating changes.

## 13. Data lineage

```text
data/processed/shopee_sales_cleaned.csv
    -> select/rename valid analytical fields
    -> shopee_product_snapshots.csv
        -> chronological product lag -> shopee_matched_observations.csv
        -> group by product -> shopee_product_coverage.csv
        -> group by date -> shopee_daily_coverage.csv
        -> group/reindex Level-2 x date -> shopee_category_daily_coverage.csv
        -> group by Level 2 + coverage joins -> shopee_category_level2_summary.csv
```

`source_row_number` links snapshots to the validated source. Previous/current source row numbers link every matched interval to two validated observations. Aggregate tables reconcile through sampled-snapshot and observation counts.

## 14. Reconciliation results

| Table | Key duplicates | Primary reconciliation | Result |
|---|---:|---|---|
| Product snapshots | 0 | 20,312 rows map one-to-one to source | PASS |
| Matched observations | 0 | 3,698 = source rows minus unique products | PASS |
| Product coverage | 0 | Observation counts sum to 20,312 | PASS |
| Daily coverage | 0 | Daily snapshot counts sum to 20,312 | PASS |
| Category daily coverage | 0 | 480 grid rows; sampled counts sum to 20,312 | PASS |
| Category Level-2 summary | 0 | 24 categories; sampled counts sum to 20,312 | PASS |

The independent Phase 4 validator passed 35 of 35 checks with zero failures. It verifies hashes, inventory, schemas, keys, row-level lineage, interval logic, price changes, product/daily/category reconciliation, reliability status, and business safeguards.

## 15. Reproducibility results

The transformation script was run twice from the validated Phase 2 CSV. All six analytical datasets, both inspection summaries, and the manifest reproduced byte-for-byte: 9 of 9 deterministic transformation artifacts.

Commands:

```powershell
python src\data\transform_data.py
python tests\data_validation\validate_transformed_data.py
```

No analytical CSV was manually edited, and no temporary file remains.

## 16. Remaining limitations

- This is a short, unevenly sampled listing-snapshot dataset, not a platform census.
- Only 18.48% of products have repeated observations.
- Level-2 category membership changes for eight products.
- Potential duplicate groups and two negative ambiguous-counter intervals remain flagged.
- Displayed prices are not realized transaction prices, and currency remains contextually inferred rather than independently verified.
- Favorite counts may be rounded and are incomplete; average ratings include unrated/missing listings.
- No campaign, inventory, margin, impression, click, conversion, order, customer, refund, or cancellation data exists.
- The original sales-momentum question remains unsupported as stated.

## 17. Fields intentionally excluded

The analytical interfaces intentionally omit fields that are redundant, raw-only, high-volume text, unsupported, or unsafe for casual analysis:

- Raw `total_sold` and `total_rating` values and their parsed/delta values.
- Raw price strings; valid analytical prices and statuses replace them.
- Raw favorite and item-rating displays; parsed values remain paired with statuses.
- Constant/redundant identifiers and fields: `sitename`, `idElastic`, `idHash`, `timestamp`, category Level 1.
- Long text/presentation fields: `specification`, `desc`, `pict_link`.
- Sparse `delivery` geography field.
- Cleaning-only missingness and lower-level audit fields not needed in the analytical interface.

All excluded values remain available in `shopee_sales_cleaned.csv` for auditability.

## 18. Fields that remain unverified

- `total_sold`: `UNVERIFIED_UNUSABLE_AS_SALES_METRIC`.
- `total_rating`: `UNVERIFIED_DUPLICATES_TOTAL_SOLD`.
- Currency: `UNVERIFIED_CONTEXT_SUGGESTS_MYR`.
- Favorite count: approximate secondary engagement display where compact.
- Coverage reliability tier: not assigned.
- Category performance metric: `NO_VERIFIED_SALES_OR_REVENUE_METRIC`.
- Matched sales movement: `NO_VERIFIED_SALES_MOVEMENT_METRIC`.

## Phase 4 decision

**Transformation checks passed — REVIEW REQUIRED.** The six tables are ready for review as the input foundation for Phase 5. Phase 4 did not perform EDA, finalize KPIs, rank categories, create a momentum score, produce visualizations, or make recommendations. Phase 5 has not started.
