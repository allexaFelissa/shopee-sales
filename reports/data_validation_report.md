# Phase 3 Data Validation Report

## 1. Executive validation summary

Phase 3 independently validated the immutable raw source, the Phase 2 processed dataset, every one of the 91 derived fields, and the cleaning pipeline's reproducibility. The final executable gate produced **47 checks: 41 PASS, 6 WARNING, and 0 FAIL**. All critical checks passed.

**Validation decision: PASS WITH DOCUMENTED WARNINGS.** The processed dataset is structurally correct and safe to enter Phase 4 after user approval, but only under the existing metric restrictions. This decision does not validate `total_sold`, `total_rating`, or any sales-momentum claim.

Evidence:

- `tests/data_validation/validate_processed_data.py`
- `outputs/tables/phase_3_validation_results.csv`
- `outputs/tables/phase_3_derived_field_validation.csv`
- `outputs/tables/phase_3_manual_sample_checks.csv`

## 2. Raw integrity result

| Check | Expected | Observed | Result |
|---|---:|---:|---|
| Raw file exists | One protected source | `dataset/shopee_sales_data.csv` | PASS |
| SHA-256 | `afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69` | Exact match | PASS |
| Rows | 20,312 | 20,312 | PASS |
| Columns | 20 | 20 | PASS |
| Unauthorized byte-identical raw copies | 0 | 0 | PASS |
| Raw hash after reproducibility run | Unchanged | Unchanged | PASS |

The only warning is organizational: the file remains in the protected legacy `dataset/` location rather than `data/raw/`. Validation did not move or modify it.

## 3. Processed structure validation

`data/processed/shopee_sales_cleaned.csv` exists with 20,312 rows and 111 columns: 20 original columns and 91 documented derived fields.

- All expected columns are present in the documented order.
- No unexpected column, duplicate column name, serialized index column, or completely empty column exists.
- The key `(id, w_date)` is complete and unique: zero missing keys and zero duplicate keys.
- The one-row-per-product-snapshot grain is preserved.
- CSV has no physical schema metadata, so validation applied the documented logical contracts. The 91 derived fields comprise 16 integer fields, 13 numeric fields, and 62 text/category/boolean/date fields; all passed parseability and value-definition checks.

## 4. Raw-to-processed reconciliation

The validator read both files as literal strings with automatic null conversion disabled, aligned rows using `source_row_number`, and compared all original fields independently.

- Original columns compared: 20
- Original cells compared: 406,240
- Cell discrepancies: 0
- Missing-token discrepancies: 0
- Row-order discrepancies: 0
- Identifier, date string, category path, numeric display, and text discrepancies: 0

No raw value was overwritten, normalized in place, or imputed.

## 5. Derived-field validation

All 91 derived fields were independently recomputed from the raw source without importing the cleaning module. Each field was checked for presence, documentation, logical type, expected missingness, impossible values, source relationship, and row-level equality.

| Logical contract | Fields | Passed | Failed |
|---|---:|---:|---:|
| Integer | 16 | 16 | 0 |
| Number | 13 | 13 | 0 |
| Text/category/boolean/date | 62 | 62 | 0 |
| **Total** | **91** | **91** | **0** |

The field-level evidence table records non-empty counts, expected empty counts, unexpected empty counts, type violations, and definition mismatches for every field. All type-violation, unexpected-empty, and definition-mismatch counts are zero.

## 6. Date validation

- All 20,312 `w_date` values parse using strict `YYYY-MM-DD` rules.
- Range is exactly 2023-04-24 through 2023-05-13.
- All 20 consecutive expected calendar dates are present.
- All epoch-millisecond timestamps resolve to the same calendar date as `w_date`; no timezone date shift was detected.
- Week starts, year-month values, and weekday names independently match their dates on every row.
- Manual records at source rows 1, 10,157, and 20,312 matched their raw dates and derived fields.

## 7. Category validation

- Level 1: one value (`Shopee`).
- Level 2: 24 raw-derived broad categories.
- Level 3: 222 categories.
- Level 4: 898 non-empty categories.
- Path structure: 19,913 valid four-level paths and 399 valid three-level paths.
- No new broad category was created, and raw `item_category_detail` values remain unchanged.
- All level fields and `category_path_clean` exactly match independently split and trimmed raw paths.
- Product path-change flags: 45 rows across 19 products, confirmed.
- Product Level-2-change flags: 21 rows across 8 products, confirmed.
- Previous-category fields and consecutive transition flags are internally consistent.

No category was reassigned during validation.

## 8. Price validation

| Field | Valid | Missing | Zero | Sentinel | Suspicious high |
|---|---:|---:|---:|---:|---:|
| Original price | 20,097 | 200 | 12 | 2 | 1 |
| Actual price | 20,282 | 15 | 12 | 2 | 1 |

All four raw `999999999` occurrences—two in each price column—have `SENTINEL_999999999` status and empty cleaned price values. They do not enter valid price pairs or discount calculations.

There are 20,086 valid comparable price pairs and 226 invalid-component pairs. Independent recomputation matched every `discount_amount` and `discount_pct` within numeric serialization tolerance. Discount fields are empty for all invalid pairs. Prices remain displayed listing prices, not realized revenue.

## 9. Compact-count validation

For `total_sold`, `total_rating`, and `favorite`, validation independently checked the numeric multiplier, suffix, display precision, compact-rounding flag, and parse status.

- `total_sold` and `total_rating`: 15,202 exact displays, 5,099 compact/rounded displays, and 11 missing-equivalent values each.
- `favorite`: 14,503 exact displays, 4,738 compact/rounded displays, 1,070 missing values, and one invalid label.
- Manual examples included `8.1k -> 8,100`, `6.5k -> 6,500`, and `2.9k -> 2,900`, each retaining suffix and rounding precision metadata.

Parsed compact values are explicitly approximate display values, not exact measurements.

## 10. `total_sold` / `total_rating` validation

Independent raw-string validation refined the earlier wording:

- 20,301 populated rows contain exactly identical `total_sold` and `total_rating` strings.
- In the remaining 11 rows, `total_sold` is blank and `total_rating` is `N/A`; both correctly normalize to missing.
- Substantive non-missing inequalities: 0.
- The processed `sold_rating_exact_match_flag` correctly records 20,301 `TRUE` and 11 `FALSE`, preserving the raw-token distinction.

All 20,312 rows retain `total_sold_metric_status = UNVERIFIED_UNUSABLE_AS_SALES_METRIC` and `total_rating_metric_status = UNVERIFIED_DUPLICATES_TOTAL_SOLD`.

No revenue, AOV, order, sales-growth, sales-velocity, category-rank, or momentum-score field exists. The `unverified_counter_*` fields remain audit fields, and all possible change intervals remain explicitly blocked from verified movement analysis.

## 11. Duplicate validation

- Exact duplicate rows: 0.
- Duplicate `(id, w_date)` keys: 0.
- Potential duplicate-review records: 62 rows in 30 deterministic groups.
- Every potential group ID independently matches the documented seller-title-date hash rule.
- All potential duplicates were retained.

Potential duplicate status is a review warning, not evidence that the rows are erroneous duplicates.

## 12. Cohort validation

| Measure | Independently verified |
|---|---:|
| Unique products | 16,614 |
| Repeated products | 3,070 |
| Rows belonging to repeated products | 6,768 |
| Matched intervals | 3,698 |
| Products with at least 3 observations | 535 |
| Products with at least 4 observations | 86 |
| Verified movement-eligible intervals | 0 |

Observation counts, first and last dates, spans, sequences, prior dates, and positive elapsed-day intervals independently match on every row. Daily, category-date, category-total, unique-product, seller, and repeated-product coverage fields also match their source groupings.

## 13. Category-change validation

The validator rebuilt each product's chronological category history. It confirmed:

- 45 product-history rows flagged for full-path instability across 19 products.
- 21 product-history rows flagged for Level-2 instability across 8 products.
- Previous-path and previous-Level-2 values match the actual preceding snapshot.
- Consecutive change flags occur only when both previous and current categories exist and differ.

Original observations remain unchanged, and no category assignment was corrected or removed.

## 14. Missingness validation

All nine Phase 2 missingness flags exactly match the documented missing-token rules. Source fields remain unchanged, including the blank-versus-`N/A` distinction in the duplicated counters. There is no evidence of imputation or of a missing business value being converted into a valid derived value.

## 15. Outlier validation

Independent 1.5×IQR calculations reproduced the manifest thresholds and all five statistical flags:

| Field | Lower fence | Upper fence | Flagged rows |
|---|---:|---:|---:|
| Original cleaned price | -129.125 | 221.315 | 2,423 |
| Actual cleaned price | -101.0 | 171.0 | 2,353 |
| Unverified counter | -1,407.5 | 2,444.5 | 2,699 |
| Favorite display | -1,365.0 | 2,379.0 | 2,546 |
| Average rating | 4.75 | 5.15 | 1,510 |

All extremes were retained. Statistical outlier flags are descriptive and do not classify a value as invalid. Explicit price validity statuses remain separate from statistical outlier status.

## 16. Reproducibility validation

The exact Phase 2 cleaning script and exact raw bytes were copied into an isolated temporary project. The script completed successfully and generated a fresh processed CSV without reading the canonical processed dataset.

- Cleaning exit code: 0.
- Regenerated rows/schema/order: exact match.
- Normalized dataframe differences: 0.
- Canonical and regenerated SHA-256: `407c6f5e654283461c8eba20a3a1721f5105650212e92ae99206ea6dbadd199d`.
- Result: byte-for-byte reproducible.
- Temporary validation environment: automatically removed.

## 17. Business-question safety assessment

The processed dataset does **not** validate or support claims about platform-wide sales growth, category revenue growth, order growth, AOV, customer growth, conversion rate, or campaign effectiveness.

The original Big Question remains in `docs/business_questions.md`. The alternative question—“Which product categories show the strongest observed traction among repeatedly tracked Shopee listings in this sampled dataset?”—remains labeled **POTENTIAL REFRAMING — REQUIRES APPROVAL**. Phase 3 did not approve, operationalize, calculate, or rank that concept.

## 18. Failed checks

Final failed checks: **none**.

During development of the independent gate, a preliminary test incorrectly treated the 11 differently encoded missing counter pairs as exact strings and contained a boolean-precedence error in an eligibility count. The tests were corrected against raw evidence. This did not require or cause a processed-data change. Prior documentation that described all 20,312 raw strings as exactly identical was corrected; the hard analytical restriction is unchanged.

## 19. Required remediation

No Phase 2 dataset or cleaning-code remediation is required.

Warnings that downstream phases must retain:

1. The raw source remains at its protected legacy path.
2. `total_sold` is unusable as a sales field and `total_rating` is unverified.
3. Sales, revenue, orders, AOV, customers, conversion, and campaign effectiveness remain unavailable.
4. Only 3,070 of 16,614 products repeat; daily sampling remains uneven.
5. Potential duplicates, category changes, negative ambiguous changes, price anomalies, and statistical outliers must remain governed by their flags.
6. Valid price fields support listing-price description only, not realized revenue.

## 20. Final validation decision

**PASS WITH DOCUMENTED WARNINGS — REVIEW REQUIRED.**

The processed dataset is safe for Phase 4 structural transformation after user approval, provided Phase 4 preserves row lineage, retains all quality/reliability flags, uses only valid-status price fields, and does not create a sales or momentum metric from `total_sold` or `total_rating`.

Phase 2 does not need to be revisited. Phase 4 has not started.
