# Shopee Sales Analytics

A portfolio Data Analytics project that turns raw Shopee sales data into validated, reproducible business intelligence. The project is designed to demonstrate practical data cleaning, validation, exploratory analysis, KPI design, business analysis, visualization, Power BI, and communication skills.

## Current status

Phase 4 transformation is ready for review. Six reproducible analytical tables now provide clear snapshot, matched-observation, product, daily, Level-2 category-day, and Level-2 category grains. All reconciliations and 35 independent transformation checks pass. No EDA, category ranking, final KPI, or recommendation has started, and `total_sold` remains unusable as sales evidence. See [the project status](docs/project_status.md), [the Phase 4 report](reports/phase_4_transformation_report.md), and [the data dictionary](docs/data_dictionary.md).

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

Cleaning, validation, and structural transformation are complete through their technical gates. No EDA, category ranking, final KPI, visualization, dashboard, or campaign recommendation has been performed.

## Reproducibility rules

- Never modify a file in `data/raw/` or the current legacy `dataset/` source location.
- Do not advance a phase until its required validation and deliverables have been reviewed.
- Put reusable logic in `src/`; use notebooks for exploration and communication, not as the only source of critical logic.
- Define KPI grain, numerator, denominator, filters, and aggregation behavior before calculation.
- Do not claim causality or business meaning beyond what the data supports.
