# Phase 7 — Broad Product Category Business Analysis

Status: `REVIEW REQUIRED`  
Analysis version: `2.0.0`  
Window: 2023-04-24 through 2023-05-13

## Result

The analysis was recalculated from the 3,698 matched observation intervals at the new 12-group grain. Exact-display filtering retains 2,603 of 3,489 valid intervals; the unchanged Level-2 stability rule leaves 2,590 primary intervals and 2,169 product-category summaries.

Evidence distribution changed from the former 24 Level-2 results (`HIGH` 4, `MODERATE` 10, `INSUFFICIENT` 10) to the 12 broad results (`HIGH` 4, `MODERATE` 4, `INSUFFICIENT` 4). This is a grain change, not a direct category performance comparison.

| Broad Product Category | Stable products | Eligible products | Positive breadth | Median favorites/day | Evidence | Sensitivity |
|---|---:|---:|---:|---:|---|---|
| Fashion | 6,259 | 881 | 52.55% | 0.091 | HIGH | UNSTABLE |
| Groceries & Pets | 965 | 112 | 64.29% | 0.211 | HIGH | DIRECTIONALLY_STABLE |
| Home | 1,872 | 194 | 57.22% | 0.172 | HIGH | UNSTABLE |
| Mobile & Technology | 2,346 | 304 | 52.30% | 0.083 | HIGH | UNSTABLE |
| Automotive | 656 | 96 | 46.88% | 0.000 | MODERATE | ROBUST |
| Baby & Kids | 1,277 | 148 | 52.03% | 0.143 | MODERATE | UNSTABLE |
| Health & Beauty | 1,926 | 337 | 62.91% | 0.167 | MODERATE | ROBUST |
| Sports & Outdoor | 694 | 67 | 46.27% | 0.000 | MODERATE | ROBUST |
| Entertainment & Hobbies | 322 | 19 | N/A | N/A | INSUFFICIENT | NOT ASSESSABLE |
| Others | 45 | 0 | N/A | N/A | INSUFFICIENT | NOT ASSESSABLE |
| Tickets & Vouchers | 101 | 3 | N/A | N/A | INSUFFICIENT | NOT ASSESSABLE |
| Travel | 143 | 8 | N/A | N/A | INSUFFICIENT | NOT ASSESSABLE |

## Reassessed findings

- No broad group passes the complete further-investigation gate. The formal candidate count remains zero.
- Groceries & Pets retains the widest publishable primary breadth, but compact-inclusive breadth is materially lower; it remains directionally stable rather than robust.
- Health & Beauty remains a robust positive sampled pattern but retains `MODERATE` evidence.
- Grouping materially changes interpretation for Fashion, Home, and Mobile & Technology: their larger combined cohorts reach `HIGH` evidence, but each remains sensitivity-unstable.
- Four broad groups are insufficient and remain selectable/unranked with blank movement KPIs.
- The former individual Level-2 statements do not automatically transfer to their broad parent because breadth and medians were recomputed from product observations.

## Sensitivities

All 12 groups have four scenario records: primary exact product, compact-inclusive product, outlier-excluded exact product, and interval-weighted exact. Insufficient groups have scenario counts but blank published breadth and movement. Outlier exclusion does not change the displayed broad results; compact inclusion and interval weighting drive the material conflicts in Fashion, Home, Mobile & Technology, and Baby & Kids.

## Integrity

Protected raw and validated-source hashes remain unchanged. Phase 6 validation passed 44/44 checks; Phase 7 validation passed 43/43 checks. Generated tables and figures are recorded in the Phase 7 manifest. No Phase 8 or Phase 9 artifact was updated.
