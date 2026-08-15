# Data Quality Issue Register

Issues are observations, not cleaning decisions. Proposed actions require review before Phase 2.

| ID | Area | Issue | Severity | Evidence | Analytical Impact | Proposed Action |
|---|---|---|---|---|---|---|
| DQ-001 | Sales metric validity | `total_sold` duplicates populated `total_rating`; jointly missing rows use different raw tokens | CRITICAL | 20,301 populated raw strings and parsed values equal; the other 11 are blank `total_sold` versus `N/A` `total_rating`, both normalized missing; zero substantive inequalities | `total_sold` cannot safely measure units, growth, velocity, or momentum | Preserve both raw fields and their raw-token distinction; classify `total_sold` as unusable for sales analysis unless source/scraper evidence independently validates it; seek original extraction logic or a better source |
| DQ-002 | Sampling coverage | Daily listing coverage changes drastically | CRITICAL | 201-3,727 rows/day; 10-24 level-2 categories/day; daily medians also shift sharply | Raw category/day totals can show scraper composition changes rather than demand | Never use unmatched daily totals as growth; build coverage diagnostics and matched cohorts; require reliability thresholds |
| DQ-003 | Temporal depth | History is only 20 consecutive days | HIGH | 2023-04-24 to 2023-05-13 | Cannot support monthly, quarterly, seasonal, or robust sustained-momentum claims | Limit claims to short-window listing traction; do not infer seasonality; seek a longer dataset if platform momentum is required |
| DQ-004 | Repeat coverage | Most products have no second observation | HIGH | 13,544/16,614 products observed once; repeat share 18.48% | Change cannot be calculated for 81.52% of products; matched cohort may be selective | Flag eligibility; compare matched vs overall category coverage; publish matched denominators |
| DQ-005 | Acceleration support | Very few products have enough observations for acceleration | HIGH | 535 products have >=3 observations; 86 have >=4; maximum is 5 | Recent-vs-prior acceleration will be underpowered and category-limited | Treat acceleration as sensitivity only; require minimum product/category histories before use |
| DQ-006 | Price validity | Sentinel-like `999999999` values | HIGH | Two snapshots of one product have both price fields equal to `999999999` | Corrupts means, value-weighted metrics, and any revenue proxy | Add invalid-price flag and exclude from price-derived calculations after approval; retain raw values |
| DQ-007 | Price semantics | Some legitimate high-ticket listings coexist with obvious anomalies | MEDIUM | Vehicles at 103,700-205,500 appear plausible; a `Free Gift (Not for Sale)` is priced at 1,000,000 | Simple global outlier deletion would remove legitimate products and retain errors | Use rule/context flags rather than one global cutoff; review product/category context |
| DQ-008 | Zero prices | Both price fields are zero in 12 rows | MEDIUM | Titles include ordinary goods, a workshop/voucher, and listings with missing sold counts | Zero may mean missing/unavailable/free, not a realized price | Flag zero-price rows; do not impute or treat as normal paid price without evidence |
| DQ-009 | Missing original price | `price_ori` has 200 missing values | MEDIUM | 0.98% overall; highest daily rate 2.79%; highest category rate 2.66% in Home & Living | Discount depth cannot be computed for affected rows | Retain missing; create discount only for valid positive price pairs |
| DQ-010 | Geography | `delivery` is mostly missing and non-informative | HIGH | 13,754 missing (67.71%); only non-null value is `KL City, Kuala Lumpur`; missing rate reaches 97.56% for Watches | Geographic performance cannot be supported | Exclude `delivery` from geographic claims; retain as raw descriptive field |
| DQ-011 | Favorite parsing | Favorites are incomplete and one label is nonnumeric | MEDIUM | 1,070 missing; one non-null `label_favorite`; category missingness reaches 34.91% for Tickets & Vouchers | Favorite-based breadth or popularity can be biased | Parse with explicit validity flag; keep missing/nonparseable separate; use only as sensitivity signal |
| DQ-012 | Compact counts | `k` notation is rounded | HIGH | Values such as `23.1k` remain flat until the next 100-unit display increment | Small changes and velocity are interval-censored, especially for popular products | Preserve raw text and parsed approximation; record precision class; avoid false zero-growth claims |
| DQ-013 | Cumulative behavior | Two matched sold/rating intervals decrease | MEDIUM | 2 negative versus 1,707 positive and 1,987 zero intervals | Violates a cumulative-count assumption and may signal relisting, scrape errors, or rounding | Inspect and flag negative deltas; do not silently clamp or remove |
| DQ-014 | Category stability | Product category paths change over time | HIGH | 19 products change full path; 8 cross level 2, 14 change level 3, 5 change only level 4 | Category movement can be misattributed; cross-category changes affect matched analysis | Create category-change flag; approve a temporal category assignment rule before analysis |
| DQ-015 | Category sparsity | Detailed category levels are fragmented | MEDIUM | 898 level-4 values; 344 occur <=5 times; 399 rows have no level 4; `Others` is common | Detailed rankings will be unstable and misleading | Use level 2 initially; allow deeper levels only after explicit support thresholds |
| DQ-016 | Potential duplicates | Same seller/title/date can map to multiple product IDs | MEDIUM | 30 groups, 62 rows; all have distinct links/IDs | May be legitimate variants/relistings or duplicated listings; can inflate product counts | Review IDs, URLs, prices, and specifications; do not delete automatically |
| DQ-017 | Identifier redundancy | `id` and `idHash` are identical | LOW | 20,312/20,312 rows equal | Redundant columns can confuse key selection | Retain both raw; designate `id` as working product key and document redundancy |
| DQ-018 | Snapshot key | `idElastic` is snapshot-unique while `id` is product-stable | INFORMATIONAL | 20,312 unique `idElastic`; 16,614 `id` values; `(id,w_date)` is unique | Wrong key choice would prevent matched-product analysis | Use `(id,w_date)` as snapshot key and `id` as product key after validation |
| DQ-019 | Rating representation | `item_rating` mixes numbers and text | MEDIUM | 917 `No ratings yet`, 11 missing; 19,384 numeric values from 1.0-5.0 | Direct numeric operations fail or conflate absent ratings with missing data | Parse numeric rating with a separate unrated flag; never map `No ratings yet` to zero without approval |
| DQ-020 | Currency | Currency is not stored explicitly | MEDIUM | Numeric price fields have no symbol/code; Malaysia context is inferred from URLs/titles | Monetary labels and cross-market interpretation remain assumptions | Document presumed MYR as an assumption or obtain source documentation before labeling |
| DQ-021 | Raw location | Source is still locked in the legacy folder | LOW | Move attempt blocked; hash unchanged; exactly one copy remains | Does not affect read-only profiling but prevents final architecture conformance | Close holding application, move once, and recheck SHA-256; never create a second copy |

## Highest-priority review gates

1. Decide whether another source or extraction evidence can validate `total_sold`.
2. Approve a matched-cohort and reliability-first approach instead of raw daily totals.
3. Decide whether the project should be explicitly reframed as sampled listing traction if no valid sold field can be recovered.
4. Approve conservative handling proposals for category changes, compact counts, invalid prices, and potential duplicates before Phase 2.

## Phase 2 treatment status

No issue was silently declared resolved. Treatments preserve raw evidence and prepare Phase 3 validation.

| Issue | Phase 2 treatment | Current state |
|---|---|---|
| DQ-001 | Preserved both fields; added parse metadata, equality flag, and explicit trust statuses | OPEN — `total_sold` blocked from sales use |
| DQ-002 | Added daily/category coverage counts; applied no weighting | OPEN — methodology decision deferred |
| DQ-003 | Added governed date fields; made no long-period claims | OPEN — source limitation |
| DQ-004 | Added matched-product/history/interval fields | MITIGATED STRUCTURALLY — selectivity remains |
| DQ-005 | Added structural acceleration flag | OPEN — acceleration not approved |
| DQ-006 | Marked sentinel prices invalid in cleaned price fields; retained raw values | TREATED — validate in Phase 3 |
| DQ-007 | Added statistical/context review flags; retained high-ticket records | OPEN FOR REVIEW |
| DQ-008 | Marked zero prices and left cleaned values empty; retained rows | TREATED — meaning remains unknown |
| DQ-009 | Preserved missing prices; no imputation | TREATED |
| DQ-010 | Preserved delivery and missing flags; geography remains unsupported | OPEN — source limitation |
| DQ-011 | Parsed valid favorites with precision/status; preserved missing/invalid | TREATED — analytical caveat remains |
| DQ-012 | Preserved suffix, precision unit, rounded flag, and raw display | TREATED — approximation remains |
| DQ-013 | Added negative-change and cumulative-status flags; no correction | TREATED — exclusion decision deferred |
| DQ-014 | Added product-level and transition-level category-change fields | TREATED STRUCTURALLY — assignment decision deferred |
| DQ-015 | Preserved all levels; marked level 2 primary | TREATED STRUCTURALLY |
| DQ-016 | Retained all rows; added deterministic duplicate-review groups | OPEN FOR RECORD REVIEW |
| DQ-017 | Preserved both identifiers; documented `id` as working product key | TREATED |
| DQ-018 | Added source row, product history, and snapshot sequence fields | TREATED |
| DQ-019 | Parsed numeric rating and separated unrated/missing states | TREATED |
| DQ-020 | Added explicit unverified currency status | OPEN — source metadata needed |
| DQ-021 | Retried no forced action; one legacy source remains hash-verified | OPEN — file lock remains |
