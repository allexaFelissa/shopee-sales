# Project workspace guidelines

- Keep the project root clean and organized.
- Group related files into a small number of clearly named folders.
- Do not create or retain unnecessary files, duplicate artifacts, temporary outputs, or disposable debug files.
- Reuse existing folders when they fit; create a new folder only when it gives a distinct category of files a clear home.
- Before finishing work, remove temporary files created during the task and verify that all newly added files are necessary.

## Shopee sales analytics workflow

- Project objective: produce a professional, portfolio-ready Shopee Sales Analytics project that demonstrates job-ready Data Analyst and Data Science internship skills through accurate, reproducible, business-focused work suitable for recruiters and employers.
- Intended deliverables: a clean and validated dataset, reproducible analysis, meaningful KPIs, EDA, business-focused insights, high-quality visualizations, a Power BI dashboard, actionable recommendations, and professional documentation.
- The user identifies `20240121_shopee_sample_data (1).csv` as the main source and `shopee_sales_cleaned.csv` as the intended cleaned output. The current workspace instead contains `dataset/shopee_sales_data.csv`; reconcile this filename/source discrepancy during the initial inventory before processing. The cleaned output does not yet exist.
- Treat files in `dataset/` as source data unless the user explicitly identifies a generated or cleaned file. Never overwrite a raw dataset.
- Use this stage order for full analytics work: raw dataset -> data profiling -> data cleaning -> data validation -> data transformation -> EDA -> KPI definition -> business analysis -> visualization selection -> chart critique -> dashboard -> business insights -> final report/documentation.
- Work one phase at a time. At the end of every phase, verify the outputs, summarize decisions and evidence, report limitations, and wait for the user before advancing to the next phase.
- Inspect the actual schema, row grain, columns, data types, date coverage, missingness, uniqueness, and available business dimensions before proposing metrics or analytical claims.
- Treat major analysis as a measurable business question. Define the unit of analysis, numerator, denominator, filters, comparison or baseline, metric, and conditions that would weaken or falsify a claim.
- Start analytical work with `karthik-analysis-planner` to define the question, grain, numerator, denominator, comparisons, assumptions, and validation criteria.
- Use `data-cleaner` for missing values, data types, duplicates, format normalization, and anomaly checks; preserve an auditable distinction between raw and cleaned data.
- Use `data-transformer` for joins, reshaping, aggregation, derived fields, and documented business rules. Use `pandas-helper` for Python/pandas profiling, validation, EDA, and analysis operations.
- Use `sql-analyst` when structured SQL queries make the analysis clearer or more reproducible.
- Use `kpi-tracker` to define and validate sales KPIs, especially numerator, denominator, time grain, filters, targets, and aggregation behavior.
- Use `dataviz-orchestrator` to coordinate the handoffs from analysis contract through prepared facts, chart specification, rendered output, critique, and revision. Route chart choice to `dataviz-selector`, visual execution rules to `karthik-data-visualization`, and review to `dataviz-critique`.
- Use `dashboard-builder` to structure the final Power BI-oriented dashboard only after KPI definitions and validated analysis are stable.
- Use `data-storyteller` after analysis and visualization validation to translate evidence into business insights, caveats, recommendations, and final documentation.
- At every stage, retain the relevant validation results and do not advance claims that the available data cannot support.
- Prioritize data accuracy, raw-data integrity, reproducibility, business relevance, clear visualization, professional presentation, and honest analysis over speed or chart volume.
- Never invent columns, relationships, business context, targets, causality, KPIs, or conclusions. If the data cannot support an intended question, narrow it or report the limitation.
