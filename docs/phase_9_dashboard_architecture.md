# Phase 9 Power BI Dashboard Architecture

Status: `REVIEW REQUIRED`
Dashboard version: `2.0.0`
Publication grain: Broad Product Category
Power BI project: `dashboard/Shopee_Category_Engagement.pbip`

## Governed purpose

The dashboard answers:

> Which Broad Product Categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

It is an evidence-aware listing-engagement dashboard. It is not a sales, revenue, demand, platform-growth, campaign-effectiveness, ranking, or forecasting dashboard.

## Data and responsibility boundary

```text
Phase 7 category comparison (12 rows) -> Category Scorecard (1 row/category)
                                              1
                                              |
                                              *
Phase 7 sensitivity (48 rows) --------> Sensitivity (category x scenario)
                                              |
                                              v
                                     Three-page PBIR report
```

Python owns cohort eligibility, product aggregation, Wilson intervals, evidence classification, sensitivity calculations, and governed findings. Power BI imports the prepared facts and owns semantic presentation, filtering, display measures, and exploration. It does not reconstruct interval logic.

## Portable import strategy

PBIP does not expose a stable project-directory variable for `File.Contents`. The deterministic generator reads the two small governed Phase 7 CSVs and embeds their bytes as Base64 CSV inside the Power Query M partitions. Power Query uses the supported `Binary.FromText(..., BinaryEncoding.Base64)` and `Csv.Document` functions.

This strategy has no machine-specific path and requires no manual parameter edit. To refresh after analytical facts change:

```powershell
python src/dashboard/build_phase_9_powerbi_project.py
```

Then open `dashboard/Shopee_Category_Engagement.pbip` in Power BI Desktop and refresh. Regeneration, rather than DAX, is the governed refresh boundary.

## Pages

1. **Category Engagement Overview** — breadth-versus-magnitude scatter, eligible-product scale, 4/4/4 evidence availability, and guarded current findings.
2. **Category Evidence Deep Dive** — single-select Broad Product Category, five governed KPIs/context fields, Wilson evidence, and four separate primary/sensitivity scenarios.
3. **Evidence & Limitations** — all 12 groups, evidence gates, sensitivity status, four insufficient groups, and unsupported-claim boundary.

## Redesign implementation

The redesign uses a soft light-gray canvas, white rounded visual containers, `#0C1F39` navy typography, `#F96722` accents, soft blue-gray secondary marks, teal stable-status marks, and muted rose insufficient-evidence marks. This palette is presentation-only and does not alter evidence definitions.

- **Page 1:** keeps the breadth-versus-magnitude bubble chart as the primary comparison, adds two descending horizontal bars for breadth and median daily movement, and uses four compact cards for evidence-sufficient categories, maximum observed breadth, maximum typical movement, and eligible tracked products.
- **Page 2:** retains the single-select category view with five governed KPI concepts, then presents evidence coverage, Wilson lower/estimate/upper context, date and relevant-observation cards, and a separate primary-versus-sensitivity comparison.
- **Page 3:** replaces the category evidence table with an all-category evidence-coverage bar chart, retains tier and stability summaries, keeps all four insufficient groups as source-governed reason cards, and uses concise support/limitation cards.

## Filters and relationships

The only user-facing filter fields are Broad Product Category, Evidence Sufficiency Tier, and Sensitivity Status. No date or Level-2 slicer exists. The single relationship filters `Sensitivity` from the unique `Category Scorecard` category key; it is not bidirectional and not many-to-many.

## N/A behavior

Entertainment & Hobbies, Others, Tickets & Vouchers, and Travel retain counts and evidence diagnostics. Their movement values are blank in the imported facts and display as `N/A — insufficient evidence`, never zero.

## Reproduction and validation

```powershell
python src/dashboard/build_phase_9_powerbi_project.py
python src/dashboard/render_phase_9_previews.py
python tests/data_validation/validate_phase_9_dashboard.py
powerbi-report-author validate dashboard/Shopee_Category_Engagement.Report
```

The deterministic redesign passes 33/33 Phase 9 checks and native PBIR structural validation with zero errors; seven warnings only report unreachable remote schemas. This includes the three-page visual inventory, removal of the legacy evidence-availability chart, Page 3 bar-chart replacement, four insufficient-category cards, model safeguards, and governed source reconciliation. The project remains at `REVIEW REQUIRED` pending a final native Desktop page-render, slicer, cross-filter, and N/A-display walkthrough. Phase 10 portfolio communication is also `REVIEW REQUIRED` and introduces no unsupported commercial recommendation.
