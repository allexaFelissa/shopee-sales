# Phase 8-9 Broad-Category Regeneration Audit

Audit status: `COMPLETED`  
Audit scope: read-only pre-regeneration inspection  
Canonical publication grain: 12 `broad_product_category` values

## Canonical inputs

- `outputs/tables/phase_7_category_business_analysis.csv`: 12 publication rows.
- `outputs/tables/phase_7_category_comparison.csv`: 12 governed category facts; evidence distribution 4 `HIGH`, 4 `MODERATE`, 4 `INSUFFICIENT`.
- `outputs/tables/phase_7_sensitivity_analysis.csv`: 48 rows; 12 categories x four governed scenarios.
- `outputs/tables/phase_7_business_findings.csv`: current broad-category finding language.
- Phase 6 KPI definitions and eligibility rules remain authoritative and unchanged.
- `category_level_2` remains a required detail and lineage field in the analytical data. It is not the publication grain.

## Stale downstream artifacts requiring regeneration

- The Phase 9 PBIP/PBIR semantic model and report were built against the former 24-category facts.
- Phase 9 validation and KPI reconciliation still expect 24 categories, 4/10/10 evidence tiers, 96 sensitivity rows, and `Women's Bags` as a publication category.
- Phase 9 preview code and narrative text contain former Level-2 examples.
- Power Query expressions in `model.bim` contain machine-specific absolute paths.
- Phase 9 architecture/report documentation describes the former dashboard generation.
- Project status and analysis-plan documents contain duplicated historical 24-category notes below current broad-category notes.
- Phase 6 governance documentation still labels Level 2 as the primary publication grain even though the executable specification and current question use Broad Product Category.

## Files requiring regeneration or controlled update

- `src/visualization/create_phase_8_visuals.py` and the six canonical Phase 8 PNGs.
- Phase 8 specifications, QA tables, validation table, report, and Power BI handoff.
- `src/dashboard/build_phase_9_powerbi_project.py` and `src/dashboard/render_phase_9_previews.py`.
- The existing `dashboard/Shopee_Category_Engagement.*` PBIP/PBIR project in place.
- Phase 9 validation code, validation outputs, preview figures, architecture, report, and manifest.
- Current-status and active-governance sections in project documentation.

## Obsolete artifacts eligible for deletion after reference checks

- Former Phase 7 analytical figures whose filenames begin `phase_7_` and that have been replaced by the six canonical Phase 8 publication figures.
- Former Phase 9 preview images and validation outputs only if their canonical filenames are regenerated in place; no duplicate old/new versions are required.
- Duplicated historical publication notes inside active status/plan documents.

Deletion requires a final repository-wide reference search after regeneration. Git history provides historical recovery.

## Artifacts that must be preserved

- Raw data and its SHA-256 baseline.
- Cleaned and analytical data required by the current pipeline.
- Level-2 fields, Level-2 structural tables, Phase 0-5 profiling/EDA evidence, and the Level-2-to-broad mapping.
- Phase 6 KPI definitions and current Phase 7 governed facts.
- The six canonical Phase 8 figure filenames and the single canonical PBIP/PBIR project.

Level-2 category names in raw profiling, Phase 4 structural tables, Phase 5 EDA, and taxonomy documentation are traceability evidence, not stale publication logic.
