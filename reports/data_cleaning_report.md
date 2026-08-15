# Phase 2 Data Cleaning Report

## 1. Raw Dataset Information

| Attribute | Value |
|---|---|
| Source | `dataset/shopee_sales_data.csv` |
| File size | 37,654,822 bytes |
| Rows | 20,312 |
| Columns | 20 |
| SHA-256 before cleaning | `afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69` |
| SHA-256 after cleaning | `afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69` |

The source remains the only raw copy and was read without modification. It is still held open by another application, so its relocation to `data/raw/` remains pending.

## 2. Processed Dataset Information

| Attribute | Value |
|---|---|
| Output | `data/processed/shopee_sales_cleaned.csv` |
| Grain | One product listing snapshot per `id` and `w_date` |
| Rows | 20,312 |
| Columns | 111 |
| Raw columns preserved | 20/20 |
| Derived/audit columns | 91 |
| Rows removed | 0 |
| Verified sales metrics created | 0 |
| Initial processed SHA-256 | `407c6f5e654283461c8eba20a3a1721f5105650212e92ae99206ea6dbadd199d` |

The processed CSV retains raw cell representations as source text and adds separate parsed fields, statuses, quality flags, cohort metadata, and coverage counts.

## 3. Before/After Summary

| Measure | Raw | Processed | Change |
|---|---:|---:|---:|
| Rows | 20,312 | 20,312 | 0 |
| Columns | 20 | 111 | +91 |
| Raw columns preserved | 20 | 20 | 0 |
| Exact duplicate rows | 0 | 0 | 0 |
| Duplicate snapshot keys | 0 | 0 | 0 |
| Rows removed | 0 | 0 | 0 |
| Valid observation dates | 20,312 | 20,312 | 0 |
| Valid comparable price pairs | Not derived | 20,086 | +20,086 |
| Matched products | Not derived | 3,070 | +3,070 |
| Verified sales metric fields | 0 | 0 | 0 |

Machine-readable summary: `outputs/tables/phase_2_cleaning_summary.csv`.

## 4. Transformation Audit

| Step | Area | Transformation | Affected rows | Integrity treatment |
|---:|---|---|---:|---|
| 1 | Source protection | Verified SHA-256 before reading | 20,312 | No raw write |
| 2 | Raw preservation | Retained all raw columns as source text | 20,312 | No raw value changed |
| 3 | Missingness | Added nine business-relevant missing flags | 13,866 | No imputation; rows retained |
| 4 | Date | Parsed date and derived week/month/day-of-week | 20,312 | Raw date and timestamp retained |
| 5 | Category | Split and trimmed up to four hierarchy levels | 20,312 | No reassignment |
| 6 | Compact counts | Parsed sold/rating/favorite displays with suffix, precision, and status | 20,301 sold/rating rows | Compact values remain explicitly approximate |
| 7 | Sales safeguard | Marked sold unusable and rating count unverified | 20,312 | No sales metric created |
| 8 | Average rating | Parsed numeric ratings and preserved unrated/missing states | 19,384 numeric rows | No imputation |
| 9 | Price | Added cleaned values and status/quality fields | 226 rows with at least one non-valid price state | Raw price retained |
| 10 | Discount | Calculated only for valid, comparable pairs | 20,086 | Not labeled revenue or campaign data |
| 11 | Duplicates | Added duplicate and review-group flags | 62 potential-review rows | No deletion |
| 12 | Matched cohorts | Added history, sequence, span, and interval fields | 6,768 rows belonging to repeated products | Performance use remains blocked |
| 13 | Negative changes | Flagged decreases in the ambiguous counter | 2 | No clamping or interpolation |
| 14 | Category changes | Added history and change flags | 45 rows across 19 products | No reassignment |
| 15 | Coverage | Added observed daily/category/product counts | 20,312 | No weighting or duplication |
| 16 | Outliers | Added descriptive statistical flags | 7,266 rows with at least one tested flag | No removal |

Machine-readable logs:

- `outputs/tables/phase_2_transformation_summary.csv`
- `reports/data_cleaning_audit_log.csv`

## 5. New Fields

All 91 fields are individually defined in `docs/data_dictionary.md`. They fall into these controlled groups:

- Source-row audit identity
- Missingness flags
- Date fields and date-validation status
- Category hierarchy and path-validation fields
- Compact-count parses, suffixes, display precision, and validity states
- Explicit sold/rating trust statuses
- Average-rating parse and status
- Price cleaning, validity, statistical outlier, and discount fields
- Duplicate-review flags and deterministic group IDs
- Product observation, matched-cohort, interval, and movement-block fields
- Category-change histories and flags
- Daily/category coverage counts
- Non-destructive statistical outlier flags

## 6. Missing-Value Treatment

No missing value was filled. Source missing markers, including blank cells and textual `N/A`, remain unchanged in raw columns. Derived values remain empty when their prerequisites are missing, and important missing states receive flags.

| Field | Missing | Treatment |
|---|---:|---|
| `delivery` | 13,754 | Preserved; missing flag; excluded from reliable geography |
| `favorite` | 1,070 | Preserved; parsed field remains missing; status `MISSING` |
| `price_ori` | 200 | Preserved; clean value missing; status `MISSING` |
| `price_actual` | 15 | Preserved; clean value missing; status `MISSING` |
| `specification` | 11 | Preserved with missing flag |
| `item_rating` | 11 | Preserved; numeric value missing; status `MISSING` |
| `seller_name` | 11 | Preserved with missing flag |
| `total_rating` | 11 | Preserved; parsed value missing; unverified status retained |
| `total_sold` | 11 | Preserved; parsed value missing; unusable-sales status retained |

Complete table: `outputs/tables/phase_2_missingness_summary.csv`.

## 7. Price Treatment

Raw prices were preserved. Derived cleaned prices accept only status `VALID`; other statuses become empty in the cleaned numeric field while the source value remains visible.

| Status | Original price rows | Actual price rows | Treatment |
|---|---:|---:|---|
| `VALID` | 20,097 | 20,282 | Numeric cleaned value retained |
| `MISSING` | 200 | 15 | Clean value empty |
| `ZERO` | 12 | 12 | Clean value empty; not assumed free |
| `SENTINEL_999999999` | 2 | 2 | Clean value empty; explicit sentinel flag |
| `SUSPICIOUS_HIGH_GE_1000000` | 1 | 1 | Clean value empty pending review |

High prices below 1,000,000 were not invalidated because vehicle and other high-ticket listings may be legitimate. Separate IQR flags identify 2,423 original-price and 2,353 actual-price statistical outliers without excluding them.

Discount amount and percentage exist only for 20,086 pairs where both prices are valid and actual price does not exceed original price. Currency remains `UNVERIFIED_CONTEXT_SUGGESTS_MYR`.

## 8. Category Treatment

The raw `item_category_detail` remains unchanged. Separate category levels are trimmed around delimiters:

- 19,913 rows: `VALID_4_LEVEL`
- 399 rows: `VALID_3_LEVEL`
- Malformed or missing paths: 0
- Primary analytical grain marker: `LEVEL_2`

No spelling correction, case normalization, mapping, or reassignment was applied.

## 9. Duplicate Treatment

- Exact duplicates: 0
- Duplicate `(id, w_date)` snapshot keys: 0
- Potential duplicate review groups: 30
- Rows in potential groups: 62
- Removed rows: 0

Potential groups use deterministic `DUP-<hash>` identifiers based on seller, title, and date. Distinct IDs and links are retained because they may represent legitimate variants or relistings. Summary: `outputs/tables/phase_2_duplicate_review_summary.csv`.

## 10. Compact-Count Treatment

Each sold, rating, and favorite display is represented by:

- Original raw text
- Parsed approximate numeric value
- Suffix
- Display precision unit
- Compact-rounded flag
- Parse status

For example, `23.1k` becomes numeric `23100`, suffix `k`, precision unit `100`, rounded flag `TRUE`, and status `PARSED_COMPACT_ROUNDED`. This does not assert that the underlying exact count is 23,100.

| Field | Exact display | Compact rounded | Missing | Invalid |
|---|---:|---:|---:|---:|
| `total_sold` | 15,202 | 5,099 | 11 | 0 |
| `total_rating` | 15,202 | 5,099 | 11 | 0 |
| `favorite` | 14,503 | 4,738 | 1,070 | 1 |

`total_sold` has status `UNVERIFIED_UNUSABLE_AS_SALES_METRIC` on every row. `total_rating` has status `UNVERIFIED_DUPLICATES_TOTAL_SOLD` on every row.

## 11. Negative-Change Treatment

Matched snapshots expose an explicitly named `unverified_counter_change`, not a sales change. Of 3,698 matched intervals:

- 1,707 increase
- 1,987 show no displayed change
- 2 decrease
- 2 have a missing counter prerequisite

The two decreases are flagged. Nothing was set to zero, interpolated, reordered, or removed. All 3,696 intervals with parsed values remain `BLOCKED_COUNTER_UNVERIFIED` for movement analysis.

## 12. Category-Change Treatment

- Products changing full path: 19
- Affected snapshot rows: 45
- Products changing level 2: 8
- Affected snapshot rows for level-2-changing products: 21
- Consecutive path changes: 20
- Consecutive level-2 changes: 9

The processed data includes product-level and consecutive-observation flags, prior path/category values, and distinct path/category counts. No observation was deleted or reassigned. Summary: `outputs/tables/phase_2_category_change_summary.csv`.

## 13. Matched-Product Fields

| Measure | Result |
|---|---:|
| Unique products | 16,614 |
| Products observed once | 13,544 |
| Matched products | 3,070 |
| Rows belonging to matched products | 6,768 |
| Products with >=3 observations | 535 |
| Products with >=4 observations | 86 |
| Matched intervals | 3,698 |
| Intervals eligible with a verified sales metric | 0 |

The dataset now contains observation count, first/last date, span, sequence, prior date, interval length, structural acceleration flag, and explicit movement-eligibility status. No momentum score or category ranking was created.

## 14. Sampling and Coverage Fields

Each row now carries observed counts for its date and category:

- Daily observations and unique products
- Daily level-2 categories and sellers
- Category-date observations and unique products
- Total category observations and unique products
- Category repeated-product count

These fields reveal coverage; they do not weight, normalize, duplicate, or “correct” the sample.

## 15. Rows Excluded

**Zero rows were removed from the processed dataset.**

Derived calculations exclude invalid prerequisites at the field level only:

- Invalid/zero/sentinel/suspicious prices are empty in cleaned price fields.
- Discounts are empty unless both cleaned prices are valid and comparable.
- Missing or invalid compact displays have empty parsed values.
- `No ratings yet` remains a separate state and is not converted to zero.
- All movement intervals remain blocked from verified sales analysis.

## 16. Remaining Anomalies

Remaining and intentionally preserved:

- Exact populated `total_sold`/`total_rating` duplication in 20,301 rows, plus 11 jointly missing-equivalent rows encoded as blank versus `N/A`
- 3,698 matched intervals blocked by field validity or missing prerequisites
- Two negative ambiguous-counter changes
- 45 rows from category-changing products
- 62 potential duplicate-review rows
- 226 rows with at least one non-valid price state
- 2,423 original-price and 2,353 actual-price statistical outliers
- 2,699 ambiguous-counter, 2,546 favorite, and 1,510 average-rating IQR flags
- Uneven scraper coverage and short history
- Missing/non-informative geography
- Unverified currency assumption

Full counts: `outputs/tables/phase_2_anomaly_summary.csv`.

## 17. Limitations

- Cleaning improves structure and auditability but cannot repair absent business facts.
- `total_sold` remains unusable as sales evidence.
- `total_rating` remains unverified.
- No orders, realized revenue, customers, conversion, campaigns, margins, refunds, or cancellations were created.
- Compact counters remain approximate.
- Coverage fields quantify the sample but do not make it representative.
- The original platform-level category-momentum question remains unsupported in full.

## 18. Reproducibility

From the project root:

```powershell
python src\data\clean_data.py
```

The script:

1. Locates exactly one approved raw source.
2. Verifies its expected SHA-256.
3. Reads every raw cell as source text.
4. Applies deterministic derived transformations.
5. Asserts row count, raw-cell preservation, key uniqueness, and sales safeguards.
6. Writes the processed CSV, seven required summary tables, an audit log, and a manifest.
7. Rechecks the raw SHA-256 after writing.

Phase 3 must independently validate these assertions before downstream use.

## 19. Business-Question Safeguard

The original Big Question has not been silently changed and no category was ranked. A potential reframing is documented for approval:

> Which product categories show the strongest observed traction among repeatedly tracked Shopee listings in this sampled dataset?

Even that framing needs a defensible performance signal. Coverage, price, favorites, and the ambiguous counter must not be mislabeled as sales.
