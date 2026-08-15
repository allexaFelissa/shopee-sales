# Project Status

Allowed states: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `REVIEW REQUIRED`, `COMPLETED`.

A phase may be marked `COMPLETED` only after its deliverables and validation criteria have been checked. Phases 0 through 4 have been reviewed and approved; Phase 5 deliverables are ready for review.

| Phase | Name | Status | Entry gate | Completion evidence |
|---:|---|---|---|---|
| 0 | Project Setup & Understanding | COMPLETED | User approval to begin | Reconciled source inventory, objective, grain hypothesis, initial data dictionary, and analysis plan reviewed |
| 1 | Data Profiling | COMPLETED | Phase 0 completed | Reproducible profile and reviewed data-quality report; raw data unchanged |
| 2 | Data Cleaning | COMPLETED | Phase 1 completed; cleaning rules approved | Cleaned dataset and transformation log verified |
| 3 | Data Validation | COMPLETED | Phase 2 completed | Cleaned-data tests pass or unresolved issues are explicitly accepted |
| 4 | Data Transformation | COMPLETED | Phase 3 completed | Analytical tables and derived-field checks verified |
| 5 | Exploratory Data Analysis | REVIEW REQUIRED | Phase 4 completed | Reproducible facts tables and EDA findings reviewed |
| 6 | Business Questions & KPI Design | NOT STARTED | Phases 0–5 completed | Questions and KPI contracts reviewed for support and denominator correctness |
| 7 | Business Analysis | NOT STARTED | Phase 6 completed | Every answer traces to computed evidence and limitations |
| 8 | Visualization | NOT STARTED | Phase 7 evidence stable | Charts pass chart-selection, semantic, and visual critique checks |
| 9 | Power BI Dashboard | NOT STARTED | Phase 8 completed; KPI logic stable | Dashboard values reconcile to validated facts tables |
| 10 | Business Insights & Recommendations | NOT STARTED | Phase 9 completed | Recommendations trace directly to evidence and stated limitations |
| 11 | Final Documentation | NOT STARTED | Phases 0–10 completed | Portfolio narrative is reproducible, concise, and complete |
| 12 | Final Quality Assurance | NOT STARTED | Phase 11 completed | Data, analysis, visuals, dashboard, and documentation pass final review |

## Phase 0 review note

- Verified deliverables: folder architecture, source inventory and hash, initial README, `docs/data_dictionary.md`, `docs/business_questions.md`, `docs/analysis_plan.md`, updated master pipeline, and `reports/phase_0_report.md`.
- Phase 0 was reviewed and approved before Phase 1 began; its current status is `COMPLETED`.
- Raw relocation remains pending: another process still holds `dataset/shopee_sales_data.csv`. The file remains the only copy and its expected SHA-256 is unchanged.
- Phase 0 performed read-only structural assessment only. No cleaning, transformation, category ranking, or campaign recommendation was performed.

## Phase 1 review note

- Verified deliverables: read-only profiling script, full profile evidence, four audit tables, `reports/data_profiling_report.md`, `reports/data_quality_issue_register.md`, and evidence-based documentation updates.
- Phase 1 was reviewed and approved before Phase 2 began; its current status is `COMPLETED`.
- Critical decision: `total_sold` is unusable as a sales/momentum field unless independently validated; `total_rating` is unverified.
- Raw SHA-256 remained `afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69` throughout profiling.

## Phase 2 review note

- Verified deliverables: deterministic cleaning script, 20,312-row processed snapshot dataset, transformation audit log, seven required summary tables, cleaning manifest, cleaning report, and exhaustive processed-field dictionary.
- Phase 2 was reviewed and approved before Phase 3 began; its current status is `COMPLETED`.
- All 20 raw columns and all rows were preserved. Zero records were deleted or imputed.
- `total_sold` remains `UNVERIFIED_UNUSABLE_AS_SALES_METRIC`; `total_rating` remains unverified. Zero verified sales metrics were created.
- Potential reframing is documented but has not replaced the original Big Question.
- Phase 3 began only after Phase 2 approval and remains the hard gate before transformation.

## Phase 3 review note

- The independent hard gate produced 47 checks: 41 passed, six documented warnings, and zero failures.
- All 91 derived fields passed independent definition, datatype, missingness, and source-relationship validation.
- All 406,240 preserved raw cells matched exactly, and isolated regeneration reproduced the processed CSV byte-for-byte.
- Phase 3 was reviewed and approved before Phase 4 began; its current status is `COMPLETED`.
- `total_sold` remains unusable as sales, `total_rating` remains unverified, and zero movement intervals are eligible for a verified sales analysis.
- Phase 4 began only after Phase 3 approval and remained limited to reproducible analytical structures and reconciliation.

## Phase 4 review note

- Created six analytical tables at explicit snapshot, matched-interval, product, daily, Level-2 category-day, and Level-2 category grains.
- All six primary keys are unique; all source, product, date, category, interval, valid-price, and coverage totals reconcile.
- The independent transformation gate passed 35 of 35 checks with zero failures.
- Nine generated transformation artifacts reproduced byte-for-byte on rerun.
- No verified sales/revenue metric, category rank, momentum score, reliability tier, EDA conclusion, or recommendation was created.
- Phase 4 was reviewed and approved before Phase 5 began; its current status is `COMPLETED`.
- Phase 5 remained exploratory and is now `REVIEW REQUIRED`; Phase 6 governance has not started.

## Phase 5 review note

- Created ten exploratory fact/diagnostic tables, twelve inspected figures, a Phase 5 analysis contract, reusable EDA code, an EDA report, and an independent validation gate.
- The gate passed 44 of 44 checks with zero failures; 23 generated artifacts reproduced byte-for-byte with zero SHA-256 differences.
- Daily sample volume varies 18.54×, only 18.48% of products repeat, and favorite movement is approximate and typically zero. These constraints prevent platform-growth inference.
- The original Big Question is not defensibly answerable. The sampled-listing observed-traction reframing is only conditionally supportable and still requires explicit approval.
- No sales/revenue/order KPI, final KPI, category rank, momentum score, campaign recommendation, or reliability tier was created. `total_sold` remains blocked.
- The raw CSV remained externally locked for a standard read, but a shared read-only handle verified its expected SHA-256. Phase 5 used only unchanged Phase 4 inputs; their hashes and the cleaned-source hash also match their approved manifests.
- Phase 5 is `REVIEW REQUIRED`; Phase 6 remains `NOT STARTED` pending explicit approval.
