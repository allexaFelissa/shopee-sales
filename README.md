# Shopee Sales Analytics

A portfolio Data Analytics project that turns raw Shopee sales data into validated, reproducible business intelligence. The project is designed to demonstrate practical data cleaning, validation, exploratory analysis, KPI design, business analysis, visualization, Power BI, and communication skills.

## Current status

The controlled category-taxonomy revision is at its Phase 4 review gate. The pipeline now preserves `category_level_2` as detail and adds a governed 12-group `broad_product_category`; all 24 observed Level-2 values map exactly once. Downstream Phase 6-9 outputs have not yet been recalculated at the new grain and must not be treated as current broad-group results. See [the taxonomy governance](docs/broad_product_category_governance.md) and [the project status](docs/project_status.md).

## Project objective

Produce a recruiter-ready analysis that answers measurable business questions with calculations supported by the available data. The project must preserve the original source, expose important assumptions, validate every major transformation, and distinguish evidence from interpretation.

## Planned workflow

```text
Raw data -> Profiling -> Cleaning -> Validation -> Transformation
         -> EDA -> KPI design -> Business analysis -> Visualization
         -> Power BI dashboard -> Insights -> Documentation -> Final QA
```

## Repository layout

- `data/raw/` — immutable source data after the pending source-file relocation
- `data/interim/` — reproducible temporary stage outputs
- `data/processed/` — validated, analysis-ready datasets
- `notebooks/` — numbered exploratory and explanatory notebooks created only when needed
- `src/` — reusable data, analysis, and visualization code
- `outputs/` — generated figures, tables, and analysis results
- `dashboard/` — Power BI source files and dashboard-specific assets
- `docs/` — methodology, definitions, business questions, and project governance
- `reports/` — phase reports and final narrative deliverables
- `tests/` — automated data validation checks
- `config/` — non-secret project configuration

## Data integrity

The currently available raw file is `dataset/shopee_sales_data.csv`. It remains there temporarily because another process has the file open and Windows blocked relocation. Its SHA-256 baseline is:

`afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69`

Cleaning, validation, transformation, EDA, KPI governance, governed business analysis, visualization, and the Phase 9 dashboard build have passed their available technical gates. The dashboard is a sampled favorite-engagement view, not verified sales or platform growth. No composite momentum score or campaign recommendation has been created; Phase 10 has not started.

## Reproducibility rules

- Never modify a file in `data/raw/` or the current legacy `dataset/` source location.
- Do not advance a phase until its required validation and deliverables have been reviewed.
- Put reusable logic in `src/`; use notebooks for exploration and communication, not as the only source of critical logic.
- Define KPI grain, numerator, denominator, filters, and aggregation behavior before calculation.
- Do not claim causality or business meaning beyond what the data supports.
