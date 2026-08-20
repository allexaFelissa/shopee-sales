# Shopee Sales Analytics Master Pipeline

This document is the single source of truth for project phases, dependencies, artifacts, validation gates, and skill routing.

## Objective and evidence standard

Build a portfolio-quality Shopee Sales Analytics project that demonstrates accurate, reproducible, business-focused analytical work. Every important conclusion must trace through:

```text
Business question -> operational definition -> data grain
-> numerator / denominator / filters -> computed facts
-> visualization -> finding -> implication -> recommendation
```

No column, KPI, relationship, target, causal claim, or recommendation may be invented. Unsupported questions must be narrowed, deferred, or rejected.

### Project-specific central question

The project is organized around: **Which product categories are gaining momentum fastest on the platform, and which should a marketplace category team prioritize featuring in upcoming campaigns and collections?**

Phase 0 found listing-snapshot data rather than transaction data. Until the labeled sold field and sampling coverage are validated, downstream work must treat the feasible target as **momentum among repeatedly observed sampled listings**, not platform-wide revenue or order momentum. Coverage and reliability measures are mandatory companions to any later category ranking.

## Architecture

```text
NEW Shopee sales/
|-- data/
|   |-- raw/                  # immutable sources; target location for current legacy CSV
|   |-- interim/              # reproducible temporary stage outputs
|   `-- processed/            # validated and analytical-ready datasets
|-- notebooks/                # numbered exploration/communication notebooks as needed
|-- src/
|   |-- data/                 # loading, cleaning, validation, transformation logic
|   |-- analysis/             # EDA, KPI, and business-analysis logic
|   `-- visualization/        # reusable charts and dashboard preparation
|-- outputs/
|   |-- figures/              # reviewed exported visuals
|   |-- tables/               # reviewed facts and reconciliation tables
|   `-- analysis_results/     # reproducible generated results
|-- dashboard/                # Power BI files and dashboard assets
|-- docs/                     # definitions, methodology, questions, and governance
|-- reports/                  # data-quality, cleaning, validation, analysis, final reports
|-- tests/
|   `-- data_validation/      # executable integrity and business-rule checks
|-- config/                   # non-secret configuration
|-- .gitignore
|-- AGENTS.md
`-- README.md
```

Only create a notebook, script, report, or configuration file when a phase actually needs it. Controlled filenames replace `final_final`, `v2`, `new`, and similar duplicates. Git does not preserve empty directories; they will become tracked naturally as verified artifacts are added.

## Data flow and mutation policy

| Stage | Input | Output | Modification policy | Depends on |
|---|---|---|---|---|
| Raw intake | User-supplied CSV currently at `dataset/shopee_sales_data.csv` | Immutable file in `data/raw/` when the lock is released | Move only after byte-level verification; never edit or duplicate | None |
| Profiling | Raw CSV | Profile tables, `reports/data_profiling_report.md`, and issue register | Read raw; write only reports/results | Phase 0 |
| Cleaning | Raw CSV + approved rules | `data/processed/shopee_sales_cleaned.csv` plus cleaning report | Create new output; never update raw | Phase 1 |
| Validation | Raw profile + cleaned CSV | Validation results and report | Read datasets; update tests/report only | Phase 2 |
| Transformation | Validated cleaned CSV | Named analytical tables in `data/processed/` | Rebuild outputs reproducibly | Phase 3 |
| EDA | Analytical tables | Facts tables and EDA artifacts | Modify code/notebooks and generated outputs only | Phase 4 |
| KPI/business analysis | Validated facts | KPI tables, answers, limitations | Definitions require review; calculations reproducible | Phases 5–6 |
| Visualization | Validated facts | Reviewed figures/specifications | Never manually alter source facts | Phase 7 |
| Dashboard | Validated model + visuals | Native `.pbip`/PBIR project and reconciliation evidence | Dashboard calculations must match source definitions | Phase 8 |
| Insights/reporting | Reviewed evidence | Reports and README updates | Claims must retain caveats | Phases 9–10 |

## Phase workflow

```text
Phase 0  Setup & understanding
   -> Phase 1  Data profiling
   -> Phase 2  Data cleaning
   -> Phase 3  Data validation [hard gate]
   -> Phase 4  Data transformation
   -> Phase 5  Exploratory data analysis
   -> Phase 6  Business questions & KPI design
   -> Phase 7  Business analysis
   -> Phase 8  Visualization
   -> Phase 9  Power BI dashboard
   -> Phase 10 Business insights & recommendations
   -> Phase 11 Final documentation
   -> Phase 12 Final quality assurance [release gate]
```

## Phase contracts

### Phase 0 — Project Setup & Understanding

- **Goal:** establish source identity, business scope, actual schema context, and a defensible analysis plan.
- **Inputs:** project brief, repository inventory, immutable source candidate.
- **Work:** reconcile the source filename; verify source hash; inspect schema only after approval; establish row-grain hypothesis; create `docs/data_dictionary.md`; define objectives, measurable question candidates, exclusions, and limitations.
- **Outputs:** reviewed architecture, initial README, initial data dictionary, and analysis plan.
- **Skills:** `karthik-analysis-planner`; use no broader skill unless schema evidence requires it.
- **Validation:** source identity and immutability confirmed; every proposed question is mapped to required fields; unknowns remain explicitly unknown.
- **Complete when:** all outputs are reviewed and the user approves Phase 1.

Phase 0 evidence established a provisional product-listing snapshot grain, 20-day coverage, a usable broad category hierarchy, sparse repeated-product history, and critical duplication between populated `total_sold` and `total_rating` values. Phase 3 later clarified that 11 jointly missing-equivalent rows use different raw tokens. See `docs/data_dictionary.md`, `docs/business_questions.md`, `docs/analysis_plan.md`, and `reports/phase_0_report.md`.

### Phase 1 — Data Profiling

- **Goal:** understand raw structure and quality without changing it.
- **Inputs:** verified raw CSV and Phase 0 definitions.
- **Work:** row/column counts, types, missingness, exact and key-level duplicates, invalid values, date/numeric checks, categorical consistency, potential outliers, currency risks, coverage, and grain tests.
- **Outputs:** `src/data/profile_data.py`, reproducible profile artifacts, `reports/data_profiling_report.md`, and `reports/data_quality_issue_register.md`.
- **Skills:** `data-cleaner` for profiling criteria; `pandas-helper` for implementation.
- **Validation:** reconcile total rows across all profile sections; label potential anomalies rather than silently treating them as errors.
- **Complete when:** report reviewed, risks classified, and cleaning decisions approved.

Phase 1 evidence classifies `total_sold` as unusable for sales/momentum and `total_rating` as unverified. It also establishes critical daily sampling bias, sparse repeats, limited acceleration support, category-path changes, and price anomalies. Phase 2 must not convert `total_sold` into a sales KPI without independent validation.

### Phase 2 — Data Cleaning

- **Goal:** create a clean dataset while preserving the source.
- **Inputs:** raw CSV, approved data-quality findings, explicit cleaning rules.
- **Work:** controlled names, types, missing values, duplicates, categories, dates, numerics, currency, and invalid-record handling.
- **Outputs:** `src/data/clean_data.py`, `data/processed/shopee_sales_cleaned.csv`, seven cleaning summary tables, `reports/data_cleaning_audit_log.csv`, a deterministic manifest, and `reports/data_cleaning_report.md`.
- **Skills:** `data-cleaner`, `data-transformer`, and `pandas-helper` only as needed.
- **Validation:** transformation log includes before/after counts and reasons; no source writes; deterministic rerun produces the same output.
- **Complete when:** output exists, transformations are documented, and Phase 3 review begins.

Phase 2 preserves all 20 raw fields and all 20,312 snapshot rows, then adds separate parsed values, quality/status flags, category levels, product-history fields, and coverage counts. `total_sold` remains explicitly unusable as sales; no verified sales metric or final analytical aggregation is created.

### Phase 3 — Data Validation

- **Goal:** prove that cleaning preserved intended information and produced valid data.
- **Inputs:** raw profile, cleaned CSV, cleaning rules.
- **Work:** validate types, ranges, dates, allowed categories, duplicates, missingness, row-count reconciliation, accidental loss, calculated fields, and repeatability.
- **Outputs:** executable checks in `tests/data_validation/`, result tables, and `reports/data_validation_report.md`.
- **Skills:** `pandas-helper`; use `sql-analyst` only when SQL adds a useful independent reconciliation.
- **Validation:** serious unresolved failures block Phase 4; accepted exceptions require rationale and impact.
- **Complete when:** required tests pass and the user accepts remaining limitations.

### Phase 4 — Data Transformation

- **Goal:** create analysis-ready tables at declared grains.
- **Inputs:** validated cleaned CSV and approved metric prerequisites.
- **Work:** supported date dimensions, derived measures, and product/category/customer/geographic tables only when corresponding fields exist.
- **Outputs:** `src/data/transform_data.py`; six clearly named analytical datasets in `data/processed/`; `outputs/tables/phase_4_transformation_summary.csv`; `outputs/tables/phase_4_table_reconciliation.csv`; `outputs/tables/phase_4_validation_results.csv`; a deterministic manifest; and `reports/phase_4_transformation_report.md`.
- **Skills:** `data-transformer`, `pandas-helper`; `sql-analyst` where query-based models improve clarity.
- **Validation:** derived values reconcile to cleaned source totals; joins preserve expected cardinality and expose unmatched records.
- **Complete when:** each table has a documented grain, key, lineage, and passing reconciliation.

Phase 4 analytical tables are `shopee_product_snapshots.csv`, `shopee_matched_observations.csv`, `shopee_product_coverage.csv`, `shopee_daily_coverage.csv`, `shopee_category_daily_coverage.csv`, and `shopee_category_level2_summary.csv`. They expose sampled-listing structure, valid prices/engagement, matched intervals, and coverage evidence. They contain no verified sales metric, category ranking, momentum score, assigned reliability tier, or campaign recommendation.

### Phase 5 — Exploratory Data Analysis

- **Goal:** identify defensible sampled-listing patterns, quantify the evidence base, and test whether an observed-traction interpretation is feasible without implying sales or platform growth.
- **Inputs:** the six validated Phase 4 analytical tables.
- **Work:** evaluate sampling/category coverage, product repetition, valid displayed prices/discounts, favorite and average-rating behavior, matched intervals, category-change effects, uncertainty, concentration, and reasonable sensitivities. `total_sold` remains blocked.
- **Outputs:** `docs/phase_5_analysis_contract.md`; reusable scripts in `src/analysis/`; ten facts/diagnostic tables and an independent validation table in `outputs/tables/`; twelve inspected exploratory figures in `outputs/figures/`; a deterministic manifest; and `reports/phase_5_eda_report.md`.
- **Skills:** `karthik-analysis-planner`, `pandas-helper`, `dataviz-orchestrator`, `dataviz-selector`, `karthik-data-visualization`, and `dataviz-critique`.
- **Validation:** every reported number traces to a facts table; denominators, units, Wilson uncertainty, and sensitivity scenarios are explicit; six input hashes match Phase 4; 44 independent checks pass; 23 artifacts reproduce byte-for-byte; no unsupported sales or Phase 6 output exists.
- **Complete when:** the user reviews the evidence and approves or rejects the proposed analytical narrowing. Until then Phase 5 is `REVIEW REQUIRED` and Phase 6 is `NOT STARTED`.

### Phase 6 — Business Questions & KPI Design

- **Goal:** convert available evidence into measurable business questions and governed KPIs.
- **Inputs:** Phase 0 scope, validated schema, and Phase 5 facts.
- **Work:** define each question and KPI with business meaning, source fields, grain, formula, numerator, denominator, filters, time behavior, aggregation rules, comparison, caveats, and falsifiers.
- **Outputs:** governed question documentation in `docs/business_questions.md` and `docs/business_question_governance.md`; `docs/kpi_definitions.md`; KPI, validation, dependency, and eligibility specifications in `outputs/tables/`; reusable specification code; a deterministic manifest; an independent validation gate; and `reports/phase_6_kpi_design_report.md`.
- **Skills:** `karthik-analysis-planner`, then `kpi-tracker`.
- **Validation:** no KPI is accepted without computable source fields and test cases; approximate favorite values, category changes, missing values, outliers, date filters, zero denominators, and evidence suppression are explicit; no unsupported metric, composite score, rank, or recommendation exists.
- **Complete when:** definitions are reviewed and frozen for Phase 7.

### Phase 7 — Business Analysis

- **Goal:** answer approved questions with reproducible evidence and business meaning.
- **Inputs:** governed KPI definitions and validated analytical tables.
- **Work:** question -> metric -> analysis -> finding -> implication -> evidence-bound recommendation candidate.
- **Outputs:** reusable analysis code; governed category analysis, comparison, sensitivity, findings, validation, and figure-review tables; analytical figures; a deterministic manifest; an independent validation gate; and `reports/phase_7_business_analysis_report.md`.
- **Skills:** `sql-analyst` and/or `pandas-helper`; `data-storyteller` only after facts are stable.
- **Validation:** independent reconstruction of every governed KPI, evidence tier, blank, and sensitivity; Phase 4 and Phase 6 hashes unchanged; distinguish description, association, and causation; no composite score or campaign recommendation.
- **Complete when:** every answer traces to evidence, definitions, and limitations.

### Phase 8 — Visualization

- **Goal:** communicate approved findings accurately and clearly.
- **Inputs:** validated facts tables, question, audience, and intended takeaway.
- **Work:** define each chart's question; select, implement, inspect, critique, and revise the exact rendered artifact.
- **Outputs:** six reviewed charts in `outputs/figures/`; `docs/phase_8_visualization_specification.md`; `docs/phase_8_powerbi_handoff.md`; reproducible code in `src/visualization/`; visual, dashboard, QA, and validation tables; deterministic manifest; and `reports/phase_8_visualization_report.md`.
- **Skills:** coordinate with `dataviz-orchestrator`; route selection to `dataviz-selector`, execution to `karthik-data-visualization`, and review to `dataviz-critique`.
- **Validation:** correct encodings, labels, denominators, axes, comparisons, accessibility, and delivery-size legibility; N/A is never encoded as zero; exact/product results remain primary; input hashes remain unchanged; no decorative, purposeless, sales, composite-score, or recommendation visual.
- **Complete when:** each delivered chart passes critique and matches its source facts.

Phase 8 implements a six-visual story: breadth-versus-magnitude scatter, evidence sufficiency, eligible tracked products, breadth comparison, median-movement comparison, and a three-panel sensitivity summary. It defines a three-page Power BI handoff without building the dashboard. The final gate passed 57 of 57 independent checks; six of six exports passed manual visual QA; ten generated artifacts reproduced byte-for-byte; and Phase 4, Phase 6, and Phase 7 inputs remained hash-identical. Phase 8 remains `REVIEW REQUIRED` until user approval.

The user explicitly authorized Phase 9 after the Phase 8 gate, so Phase 8 is recorded as `COMPLETED` for sequential progression.

### Phase 9 — Power BI Dashboard

- **Goal:** build a concise interactive decision view from governed metrics.
- **Inputs:** validated model, KPIs, visual specifications, and facts-table benchmarks.
- **Work:** executive overview first; add product, customer/geography, or promotion pages only when supported and useful.
- **Outputs:** native source-controlled PBIP/PBIR project, dashboard notes, and reconciliation evidence; a `.pbix` export is optional when Desktop is available.
- **Skills:** `dashboard-builder`; use visualization skills for dashboard visuals as needed.
- **Validation:** displayed values, filters, relationships, totals, time context, and KPI definitions reconcile to benchmarks.
- **Complete when:** all pages serve a defined audience question and pass value reconciliation.

Phase 9 produced `dashboard/Shopee_Category_Engagement.pbip`, a native PBIP/PBIR project with a local semantic model and the approved overview, deep-dive, and evidence/limitations pages. The model imports frozen Phase 7 publication facts, exposes only the three approved slicer fields, and preserves N/A for insufficient movement. Desktop compatibility review repaired the invalid report/3.3.0 root, two semantic-model DAX columns that lacked the required TMSL `type: calculated` discriminator, and five imported-column/measure name collisions. The backing columns now use internal `Value` aliases while approved measure names, DAX meaning, source mappings, and report bindings remain unchanged. Independent validation passes 23 of 23 checks and offline PBIR validation reports zero errors. Installed Power BI Desktop 2.150.2455.0 reaches the named `Shopee_Category_Engagement` project window with no modal project-load error, while visible refresh/render/interaction screenshot QA remains a review action. Three deterministic page previews passed manual layout/semantic QA. Phase 9 is `REVIEW REQUIRED` and Phase 10 is `NOT STARTED`.

### Phase 10 — Business Insights & Recommendations

- **Goal:** connect evidence to decisions without overclaiming.
- **Inputs:** reviewed analysis and dashboard.
- **Work:** finding -> why it matters -> implication -> recommendation, including confidence and limitations.
- **Outputs:** prioritized insight and recommendation section for the final report.
- **Skills:** `data-storyteller`.
- **Validation:** each recommendation links to a finding; feasibility claims not contained in the data are labeled as hypotheses or omitted.
- **Complete when:** recommendations are evidence-linked, specific, and appropriately qualified.

### Phase 11 — Final Documentation

- **Goal:** make the work quickly understandable and reproducible for recruiters and analysts.
- **Inputs:** all verified phase artifacts.
- **Work:** document overview, problem, dataset, cleaning, validation, methodology, KPIs, EDA, findings, dashboard, recommendations, limitations, reproduction steps, and conclusion.
- **Outputs:** completed README, methodology/data documentation, and `reports/final_report.md`.
- **Skills:** `data-storyteller` where narrative synthesis helps.
- **Validation:** links and commands work; numbers match final outputs; limitations remain visible.
- **Complete when:** an unfamiliar reviewer can understand and reproduce the analytical path.

### Phase 12 — Final Quality Assurance

- **Goal:** conduct a senior-analyst release review.
- **Inputs:** complete repository and exact deliverable artifacts.
- **Work:** audit data accuracy/completeness/consistency/loss/types; formulas and aggregation; statistical and claim integrity; chart semantics; dashboard filters and values; documentation and reproducibility; repository cleanliness.
- **Outputs:** final QA checklist/report and resolved issue log.
- **Skills:** use the smallest relevant skills for each failed gate; `dataviz-critique` for visuals and `dashboard-builder` for dashboard checks.
- **Validation:** rerun critical checks and inspect exact final artifacts.
- **Complete when:** no release-blocking defect remains and all accepted limitations are documented.

## Dependency and gate rules

- Phases are sequential by default. A later phase may prototype structure, but may not publish results before upstream gates pass.
- Phase 3 is a hard data gate: Phase 4 cannot begin with serious unresolved validation failures.
- KPI definitions in Phase 6 govern all later calculations; a definition change returns affected work to validation.
- A finding rejected during visualization or dashboard reconciliation returns to Phase 7, not merely to chart styling.
- Final QA failures return to the owning phase and are rechecked before completion.
- At every phase boundary: verify artifacts, summarize decisions, list unresolved risks, update `docs/project_status.md`, and wait for user approval.

## Folder and naming rules

1. `data/raw/` is immutable. Until relocation is possible, the current `dataset/shopee_sales_data.csv` receives identical protection.
2. Final validated datasets belong in `data/processed/`; temporary reproducible datasets belong in `data/interim/`.
3. Reusable analysis code belongs in `src/`; exploration and explanatory sequences belong in `notebooks/`.
4. Generated charts and analytical results belong in `outputs/`; Power BI files belong in `dashboard/`.
5. Methodology and definitions belong in `docs/`; phase and narrative reports belong in `reports/`; checks belong in `tests/`.
6. Configuration must be non-secret and belong in `config/`; secrets remain outside version control.
7. Do not create random root files, duplicate data copies, or filenames such as `final_final`, `new_final`, or `cleaned_v2`.
8. Prefer stable semantic names. Replace an artifact reproducibly only when its role is identical; otherwise give it a distinct documented purpose.
