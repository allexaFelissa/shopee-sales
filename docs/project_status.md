# Project Status

Allowed states: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `REVIEW REQUIRED`, `COMPLETED`.

Canonical publication grain: 12 Broad Product Categories. The 24 original Level-2 values remain preserved as detail and lineage fields, not as the publication grain.

| Phase | Name | Status | Current evidence |
|---:|---|---|---|
| 0 | Project Setup & Understanding | COMPLETED | Source identity, hash baseline, grain hypothesis, data dictionary, and analysis plan reviewed |
| 1 | Data Profiling | COMPLETED | Raw profile and data-quality issue register verified |
| 2 | Data Cleaning | COMPLETED | 20,312 rows preserved; cleaned data and audit log verified |
| 3 | Data Validation | COMPLETED | Hard gate passed with documented warnings and no failures |
| 4 | Data Transformation | COMPLETED | Six analytical tables reconcile; 24-to-12 mapping gate passed 14/14 |
| 5 | Exploratory Data Analysis | COMPLETED | Sampling, repeat coverage, engagement, and limitations reviewed |
| 6 | Business Questions & KPI Design | COMPLETED | Five frozen broad-category KPIs; revised gate passed 44/44 |
| 7 | Business Analysis | COMPLETED | Current 12-group facts passed 43/43 and deterministic regeneration |
| 8 | Visualization | COMPLETED | Six canonical figures passed 58/58 plus rendered QA |
| 9 | Power BI Dashboard | REVIEW REQUIRED | Portable 12-group PBIP/PBIR regenerated; automated gates passed; native Desktop review recorded separately |
| 10 | Business Insights & Recommendations | REVIEW REQUIRED | Recruiter-facing story and evidence-bound implications documented; no commercial recommendation introduced |
| 11 | Final Documentation | NOT STARTED | Depends on Phase 10 |
| 12 | Final Quality Assurance | NOT STARTED | Depends on Phase 11 |

## Protected data and analytical boundary

- Raw SHA-256: `afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69`.
- Raw and Phase 2 validated sources remain unchanged.
- `total_sold` remains unusable as sales; `total_rating` remains unverified.
- The analysis describes observed favorite-display engagement among eligible repeatedly tracked sampled listings.
- It does not support sales, revenue, orders, conversion, demand, platform growth, campaign effectiveness, future performance, or campaign priority.

## Current governed facts

- Categories: 12 Broad Product Categories.
- Evidence: 4 `HIGH`, 4 `MODERATE`, 4 `INSUFFICIENT`.
- Primary cohort: exact favorite displays, positive elapsed intervals, product-level aggregation, and the conservative Level-2-change exclusion.
- Sensitivities: compact-inclusive, outlier-excluded, and interval-weighted.
- Insufficient groups: Entertainment & Hobbies, Others, Tickets & Vouchers, and Travel; counts remain visible and movement KPIs remain blank/N/A.
- No category passes the complete formal further-investigation gate.

## Phase 8 completion note

Phase 8 regenerated six canonical figures from the current Phase 7 facts. All 12 groups appear in evidence/count views; insufficient groups are N/A rather than zero in movement views. The exact exports passed semantic/readability review and 58/58 independent checks. The user authorized Phase 9 after this gate, so Phase 8 is `COMPLETED`.

## Phase 9 review note

The existing PBIP/PBIR project was regenerated in place at the broad-category grain:

- `Category Scorecard`: 12 rows.
- `Sensitivity`: 48 rows across four scenarios.
- Pages: Category Engagement Overview; Category Evidence Deep Dive; Evidence & Limitations.
- Filters: Broad Product Category; Evidence Sufficiency Tier; Sensitivity Status.
- Evidence distribution: 4/4/4.
- Machine-specific Power Query paths were removed. The deterministic generator embeds the small governed publication facts as Base64 CSV for portable refresh.
- No Level-2 slicer, date slicer, stale Level-2 publication result, composite score, or prohibited commercial metric exists.
- The navy-and-orange redesign passes 33/33 automated Phase 9 checks and PBIR structural validation with 0 errors; native Desktop page rendering and interactions still need user review.

Phase 9 stops at `REVIEW REQUIRED`. Phase 10 documentation is also `REVIEW REQUIRED`: the portfolio narrative is drafted, but no unsupported commercial recommendation has been introduced and the native dashboard interaction walkthrough remains outstanding.
