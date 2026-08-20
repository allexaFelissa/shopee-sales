# Project Status

Allowed states: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `REVIEW REQUIRED`, `COMPLETED`.

A phase may be marked `COMPLETED` only after its deliverables and validation criteria have been checked. Phases 0 through 8 have been reviewed or explicitly authorized for progression; Phase 9 deliverables are ready for review.

| Phase | Name | Status | Entry gate | Completion evidence |
|---:|---|---|---|---|
| 0 | Project Setup & Understanding | COMPLETED | User approval to begin | Reconciled source inventory, objective, grain hypothesis, initial data dictionary, and analysis plan reviewed |
| 1 | Data Profiling | COMPLETED | Phase 0 completed | Reproducible profile and reviewed data-quality report; raw data unchanged |
| 2 | Data Cleaning | COMPLETED | Phase 1 completed; cleaning rules approved | Cleaned dataset and transformation log verified |
| 3 | Data Validation | COMPLETED | Phase 2 completed | Cleaned-data tests pass or unresolved issues are explicitly accepted |
| 4 | Data Transformation | COMPLETED | Phase 3 completed | Controlled broad-category enrichment approved; mapping and integrity gates passed |
| 5 | Exploratory Data Analysis | COMPLETED | Phase 4 completed | Reproducible facts tables and EDA findings reviewed |
| 6 | Business Questions & KPI Design | COMPLETED | Phases 0–5 completed | Broad-grain KPI contract passed 44 independent checks |
| 7 | Business Analysis | REVIEW REQUIRED | Phase 6 completed | Recalculated broad-grain evidence passes independent validation pending final review |
| 8 | Visualization | NOT STARTED | Phase 7 evidence stable | Charts pass chart-selection, semantic, and visual critique checks |
| 9 | Power BI Dashboard | REVIEW REQUIRED | Phase 8 completed; KPI logic stable | Dashboard values reconcile to validated facts tables |
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

- Controlled revision added a versioned 24-to-12 Level-2-to-Broad mapping without changing `category_level_2`, protected sources, row grain, or quality flags.
- All 20,312 snapshot rows map exactly once; separate broad stability fields were added while the Level-2 stability exclusion remains authoritative.
- The original Phase 4 gate remains 35/35 PASS and the new independent mapping gate is 14/14 PASS.
- Phase 4 is returned to `REVIEW REQUIRED` for this revision. Existing Phase 6-9 artifacts still represent the former Level-2 publication grain and must not be interpreted as recalculated broad-group results.

- Created six analytical tables at explicit snapshot, matched-interval, product, daily, Level-2 category-day, and Level-2 category grains.
- All six primary keys are unique; all source, product, date, category, interval, valid-price, and coverage totals reconcile.
- The independent transformation gate passed 35 of 35 checks with zero failures.
- Nine generated transformation artifacts reproduced byte-for-byte on rerun.
- No verified sales/revenue metric, category rank, momentum score, reliability tier, EDA conclusion, or recommendation was created.
- Phase 4 was reviewed and approved before Phase 5 began; its current status is `COMPLETED`.
- Phase 5 remained exploratory and was reviewed before the user authorized Phase 6.

## Phase 5 review note

- Created ten exploratory fact/diagnostic tables, twelve inspected figures, a Phase 5 analysis contract, reusable EDA code, an EDA report, and an independent validation gate.
- The gate passed 44 of 44 checks with zero failures; 23 generated artifacts reproduced byte-for-byte with zero SHA-256 differences.
- Daily sample volume varies 18.54×, only 18.48% of products repeat, and favorite movement is approximate and typically zero. These constraints prevent platform-growth inference.
- The original Big Question is not defensibly answerable. The sampled-listing observed-traction reframing is only conditionally supportable and still requires explicit approval.
- No sales/revenue/order KPI, final KPI, category rank, momentum score, campaign recommendation, or reliability tier was created. `total_sold` remains blocked.
- The raw CSV remained externally locked for a standard read, but a shared read-only handle verified its expected SHA-256. Phase 5 used only unchanged Phase 4 inputs; their hashes and the cleaned-source hash also match their approved manifests.
- Phase 5 reached `REVIEW REQUIRED`; the user then explicitly authorized progression to Phase 6.

The user explicitly authorized progression to Phase 6; Phase 5 is therefore recorded as `COMPLETED` for the sequential gate.

## Phase 6 review note

- Controlled taxonomy revision updated the comparison grain and source dependencies to the governed 12-value Broad Product Category while keeping all five KPI definitions, thresholds, exact-display primary rule, sensitivities, and Level-2-change exclusion unchanged.
- The revised Phase 6 gate passed 44 of 44 checks. Phase 6 is `COMPLETED` for this approved sequential recalculation.

- The original platform momentum and campaign-priority question remains unsupported; the governed question is limited to favorite-engagement movement among eligible repeatedly tracked sampled listings.
- Approved a five-item non-composite scorecard: two context measures, two movement measures, and one transparent evidence tier.
- Primary movement uses exact favorite displays, stable Level-2 products, positive elapsed intervals, and product-level aggregation. Compact values remain in a mandatory sensitivity only.
- `HIGH`, `MODERATE`, and `INSUFFICIENT` evidence rules use date presence, eligible product count, and product-level Wilson precision; insufficient categories have blank movement KPIs.
- No category result, ranking, composite momentum score, campaign recommendation, sales/revenue/order/AOV/customer/conversion KPI, or Phase 4 data change was created.
- The independent Phase 6 gate passed 44 of 44 checks, and all four generated specification tables plus the manifest reproduced byte-for-byte.
- Phase 6 reached `REVIEW REQUIRED`; the user then explicitly authorized Phase 7.

The user explicitly authorized downstream analysis; Phase 6 is therefore recorded as `COMPLETED` for the sequential gate.

## Phase 7 review note

- Analysis version 2.0.0 recomputed results from underlying eligible observations for all 12 broad groups; no old Level-2 KPI was summed, averaged, or relabeled.
- The unchanged primary cohort contains 2,590 intervals and 2,169 product summaries. Evidence tiers are 4 `HIGH`, 4 `MODERATE`, and 4 `INSUFFICIENT`; insufficient movement values are blank.
- All compact-inclusive, outlier-excluded, and interval-weighted sensitivities were recomputed. No broad group passes the complete further-investigation gate.
- The independent Phase 7 gate passed 43 of 43 checks. Phase 7 remains `REVIEW REQUIRED`; Phase 8 is `NOT STARTED` for this revision.

- Applied the five frozen Phase 6 KPIs to all 24 Broad Product Categories without changing definitions or upstream data.
- The primary exact-display cohort contains 2,590 intervals after excluding every category-changing product and produces 2,169 product-category summaries.
- Evidence tiers are 4 `HIGH`, 10 `MODERATE`, and 10 `INSUFFICIENT`; insufficient movement KPIs are blank.
- Completed compact-inclusive, outlier-excluded, and interval-weighted sensitivities. No category passes the complete formal further-investigation gate.
- Created governed category, comparison, sensitivity, findings, validation, and figure-review tables plus six inspected analytical figures.
- The independent Phase 7 gate passed 43 of 43 checks with zero failures.
- Thirteen generated analysis, figure, manifest, and validation artifacts reproduced byte-for-byte with zero SHA-256 differences.
- No sales/revenue/order/customer/conversion/campaign-effectiveness metric, composite score, final category ranking, causal claim, or campaign recommendation was created.
- Phase 7 reached `REVIEW REQUIRED`; the user then explicitly authorized Phase 8.

The user explicitly authorized visualization work; Phase 7 is therefore recorded as `COMPLETED` for the sequential gate. Phase 8 remains limited to reviewed analytical figures and a Power BI handoff specification; no dashboard implementation is authorized.

## Phase 8 review note

- Created six analytical visuals covering breadth versus magnitude, evidence sufficiency, eligible-product evidence, breadth, median movement, and all three mandatory sensitivities.
- All 24 Broad Product Categories remain visible where appropriate; ten insufficient categories show N/A/blank movement values and remain unranked.
- Exact-display product-level results remain primary. Compact-inclusive, outlier-excluded, and interval-weighted values are visually and semantically separate.
- Defined a three-page Power BI handoff: Category Engagement Overview, Category Evidence Deep Dive, and Evidence & Limitations. No `.pbix` or dashboard implementation was created.
- Six of six exact PNG exports passed manual visual QA after title, legend, label, and marker-layer revisions.
- The independent Phase 8 gate passed 57 of 57 checks with zero failures.
- Ten generated visual/specification/manifest artifacts reproduced byte-for-byte with zero SHA-256 differences; Phase 4, Phase 6, and Phase 7 inputs remained hash-identical.
- No KPI definition, composite score, sales/revenue/order/customer/conversion metric, campaign-effectiveness metric, causal claim, or campaign recommendation was created.
- Phase 8 reached `REVIEW REQUIRED`; the user then explicitly authorized Phase 9, so Phase 8 is recorded as `COMPLETED` for the sequential gate.

## Phase 9 review note

- Created a native source-controlled Power BI Project at `dashboard/Shopee_Category_Engagement.pbip`, with a local semantic model and the three approved report pages.
- Loaded only governed Phase 7 category-comparison and sensitivity facts; Phase 7 input hashes remained identical to the Phase 8 manifest.
- Implemented the five approved KPIs, exact-display primary logic, separate sensitivity results, and explicit `N/A — insufficient evidence` display behavior.
- Exposed only Broad Product Category, Evidence Sufficiency Tier, and Sensitivity Status as slicer fields; no date slicer exists.
- Independent dashboard validation passed 21 of 21 checks, including the report/3.3.0 root contract. Offline PBIR validation passed with zero errors; warnings were limited to remote schemas being unreachable.
- Three deterministic page-layout previews passed manual semantic/readability QA.
- Repaired an internally inconsistent `definition/report.json`: report schema 3.3.0 requires `themeCollection` and rejects the legacy `layoutOptimization` property. The generator and generated PBIR now emit the required empty theme collection and no legacy property.
- Repaired two DAX calculated columns in `model.bim`: `Sensitivity[Scenario Display]` and `Sensitivity[Scenario Type]` now explicitly declare TMSL `type: calculated`, rather than presenting `expression` on an implicitly imported source column. Their DAX and report references are unchanged.
- Removed five table-local column/measure namespace collisions by renaming only the imported backing columns with a `Value` suffix and updating their dependent DAX. The approved measure names and all report bindings remain unchanged.
- Repaired the deep-dive category domain: removed a visual-level categorical filter that unintentionally restricted the Broad Product Category slicer to `Health & Beauty`. The slicer remains single-select and now exposes all 24 governed categories, including insufficient-evidence categories that correctly display N/A after selection. The supporting table shows eligible units, positive breadth, difference from primary, and median movement by specification.
- Validation now confirms the complete 24-category slicer source and scans any report-, page-, or visual-level filter identifiers for uniqueness and the Desktop 1–50 character contract.
- Installed Power BI Desktop 2.150.2455.0 accepted the repaired report and semantic model, created a semantic-model workspace, and registered both calculated columns without the prior project-load error. Visible render, refresh, cross-filter, and screenshot QA remain review actions before Phase 9 can be marked `COMPLETED`.
- No composite score, sales/revenue/order/customer/conversion metric, platform-growth claim, campaign-effectiveness metric, final recommendation, or Phase 10 work was created.
- Phase 9 is `REVIEW REQUIRED`; Phase 10 remains `NOT STARTED`.
