# Phase 6 — Business Questions & KPI Design Report

Status: `COMPLETED`
Phase type: governance and definition  
Study window: 2023-04-24 through 2023-05-13  
Primary publication grain: Broad Product Category (12 governed groups)

## 1. Executive decision

The original question—“Which product categories are gaining momentum fastest on the platform, and which of those should a marketplace's category team prioritize featuring in upcoming campaigns and collections?”—is not supported. The dataset has no verified sales, orders, realized revenue, customers, conversion, campaign exposure, inventory, margin, or representative platform sampling frame.

Phase 6 approves this narrower question:

> Which Broad Product Categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

The question is supported for sample-bound description because the matched table contains consecutive product observations, positive elapsed days, exact/compact favorite status, and category history. It does not authorize a category ranking in Phase 6, a platform-growth claim, or a campaign recommendation.

## 2. Evidence reviewed

The design traces to `docs/business_questions.md`, `docs/analysis_plan.md`, `docs/data_dictionary.md`, `docs/phase_5_analysis_contract.md`, `reports/phase_5_eda_report.md`, the Phase 4 transformation report, Phase 3 validation report, Phase 2 cleaning report, and the Phase 5 facts tables.

Key constraints retained:

- 20,312 sampled snapshots, 16,614 products, 24 Level-2 categories, and 20 dates.
- Daily sampling ranges from 201 to 3,727 snapshots, an 18.54× spread.
- Only 3,070 products repeat; 3,698 irregular consecutive intervals exist.
- Favorite comparisons provide 3,489 valid intervals: 1,518 positive, 1,891 zero, and 80 negative.
- Exact-only favorite comparisons provide 2,603 intervals; 886 valid intervals contain a compact endpoint.
- Compact displays account for 4,738 of 19,241 valid favorite snapshots (24.62%).
- Average rating is unchanged in 3,414 of 3,500 valid intervals (97.54%).
- Displayed prices are highly right-skewed and are not realized revenue.
- Nine intervals cross Level-2 categories; eight products change Level 2 over the study.
- Phase 5 sensitivity results differ by definition, especially exact versus compact-inclusive favorite movement.

These facts rule out sales and platform momentum while allowing a carefully labeled favorite-engagement analysis.

## 3. Business question governance

Broad Product Categories are supported for sample-bound comparison through the deterministic 24-to-12 mapping, while original Level-2 values remain available for traceability. Products with changing Level-2 membership remain excluded. “Gaining momentum,” “fastest,” and “on the platform” are not supported as written. They are replaced only in the governed question by stronger observed favorite-engagement movement under explicit eligibility, product weighting, and evidence gates. “Prioritize featuring” and “upcoming campaigns and collections” remain unsupported because commercial outcomes and causal decision inputs are absent.

Detailed component decisions and definitions of observed, favorite engagement, traction, repeatedly tracked, category, and sampled dataset are in `docs/business_question_governance.md`.

## 4. Approved KPI framework

The scorecard contains five items:

| KPI | Status | Purpose |
|---|---|---|
| Observed Stable-Category Product Count | Approved context | Sample scale |
| Eligible Favorite-Movement Product Count | Approved context | Movement denominator/evidence base |
| Positive Favorite-Movement Breadth | Approved core | Breadth of positive product movement |
| Median Daily Favorite Movement per Product | Approved core | Typical movement magnitude/direction |
| Evidence Sufficiency Tier | Approved governance | Comparison permission and suppression |

The primary interval cohort requires exact valid favorite displays at both endpoints, `elapsed_days > 0`, both dates in the active context, and a product that never changes Level-2 category. Each product is reduced to its median daily change before category aggregation. This prevents interval-heavy products from receiving extra weight.

Positive breadth includes zero and negative product medians in its denominator. It therefore measures how widespread positive movement is, not the amount moved. The magnitude KPI uses a two-stage median because Phase 5 found skew and outlier influence; means and relative growth are not suitable headline measures.

## 5. Candidate KPI decisions

- Observed scale is retained as a distinct stable-category product count, explicitly not market share.
- Observation coverage is a reliability input, not a performance KPI.
- Repeated-product coverage becomes the eligible product denominator.
- Favorite breadth and product-level median movement are core because they provide nonredundant breadth and magnitude views.
- Price and discount are excluded from traction because they are listing attributes with no verified outcome or causal link.
- Average-rating movement is rejected because 97.54% of intervals are unchanged.
- Relative favorite growth is rejected because zero/small starting values and compact rounding create unstable percentages.
- Mean and trimmed-mean movement are diagnostics only; the median is the governed magnitude statistic.
- Category listing share is rejected because an unknown scraper sample cannot support a market-share interpretation.
- A generic Favorite Movement Rate is rejected as ambiguous and redundant with breadth or median daily movement.

## 6. Favorite approximation decision

Exact-only displays are primary. Exact + compact values are required as a separately labeled product-level directional sensitivity. Approximate-only analysis is not a KPI. Interval-censored modeling is deferred because it would require extra assumptions and would not be straightforward to reproduce in Power BI.

This choice reduces valid interval coverage from 3,489 to 2,603, retaining 74.61% and excluding 25.39%. The loss is material and must be displayed. It is accepted because the primary KPI should not interpret quantized compact endpoints as exact changes. Compact-inclusive sensitivity cannot upgrade the evidence tier or replace the primary value.

## 7. Positive breadth and magnitude governance

The breadth formula is:

```text
100 × eligible products with product median daily change > 0
    / all eligible products
```

Products with zero and negative movement remain in the denominator. Negative values are not clamped. Very short intervals are allowed when elapsed days are positive; per-day normalization is exact with respect to the observed endpoints but does not reveal when change occurred. Boundary-crossing intervals are excluded under date filters.

Magnitude is the category median of product-level median daily changes. Median is preferred to mean and trimmed mean because it is understandable, resistant to extreme product changes, and gives each product equal category weight. Relative growth is rejected because a zero or near-zero start can generate undefined or exaggerated values.

## 8. Evidence framework

The Phase 5 screen (20 dates, at least 75 contributing products, Wilson width at most 20 points) was exploratory. The 75-product floor is not sufficient at the worst-case 50% proportion to guarantee a 20-point Wilson width. Phase 6 replaces it with explicit tiers:

| Tier | Required conditions | Permitted interpretation |
|---|---|---|
| HIGH | 20 observed dates; at least 100 eligible exact-display products; product-breadth Wilson 95% width ≤20 pp | Comparative within-sample interpretation, subject to sensitivities |
| MODERATE | Not HIGH; at least 15 observed dates; at least 30 eligible products; Wilson width ≤35 pp | Coarse directional within-sample interpretation |
| INSUFFICIENT | Any MODERATE gate fails or denominator is zero | No comparative movement claim; movement KPIs blank |

At `n=100`, the worst-case Wilson width is about 19.25 points; at `n=30`, it is about 33.7 points. Full date presence is required for high evidence because the study is only 20 days. Fifteen dates provides a transparent 75% floor for moderate evidence. These rules do not correct daily volume variation or establish representativeness.

Exact-only eligibility already governs approximation. Excluding all Level-2-changing products governs category stability. Valid interval and product counts remain visible. Daily coverage variation and top-product concentration remain diagnostics; no arbitrary score weights are assigned to them.

## 9. Sensitivity and conflict handling

Required sensitivity views are compact-inclusive product-level, outlier-endpoint-excluded product-level, and interval-weighted. A sensitivity review flag is raised if breadth differs by more than 10 percentage points, crosses 50%, or the median movement direction changes. Conflicting dimensions remain visible rather than being averaged.

Examples:

- High breadth with low magnitude means broad but small movement.
- Low breadth with high magnitude signals uneven or concentrated movement.
- Strong point estimates with insufficient evidence remain suppressed.
- Large observed scale with weak movement describes the sample, not business underperformance.

## 10. Composite momentum score

No composite score is justified. There is no empirical basis for weights, and a weighted score would conceal trade-offs and manufacture an ordinal ranking from analyst preferences. A transparent scorecard is the governed design. Consequently, no weight sensitivity test is needed and no composite field exists.

## 11. Business decision boundary

A category may be labeled for further investigation only when it has `HIGH` evidence, a positive-breadth Wilson lower bound above 50%, positive median daily favorite movement, and no sensitivity conflict. This is not a campaign recommendation. Campaign prioritization requires conversion or commercial outcomes, margin, inventory, campaign fit, cost, and ideally causal/control evidence.

## 12. KPI dependency map

```text
raw id / date / category / favorite display
    ↓
validated product_id / observation_date / Level-2 stability /
favorite parsed value + exact/compact status
    ↓
Phase 4 snapshots + consecutive matched observations
    ↓
eligible exact, positive-elapsed, stable-category intervals
    ↓
interval favorite change per day
    ↓
one median daily change per product-category
    ├── positive / zero / negative product outcome
    │       ↓
    │   Positive Favorite-Movement Breadth + Wilson precision
    ├── category median
    │       ↓
    │   Median Daily Favorite Movement per Product
    └── eligible product count + observed date count
            ↓
        Evidence Sufficiency Tier

stable snapshot products
    ↓
Observed Stable-Category Product Count

total_sold / total_rating
    ↓
blocked trust statuses
    ↓
no KPI
```

The row-level machine-readable dependency map is `outputs/tables/phase_6_kpi_dependency_map.csv`.

## 13. Power BI implementation specification

The exact measure names, source fields, grain, denominator behavior, blank handling, date/category behavior, and suppression rules are in `outputs/tables/phase_6_kpi_specification.csv`. Phase 7 should prepare a product-category favorite-movement fact with one row per eligible product and primary/sensitivity variants. Phase 9 should then use simple distinct-count, share, median, Wilson, and tier measures rather than rebuilding interval logic in presentation DAX.

## 14. Validation specification

Eighteen independent validation rules cover ranges, worked examples, category changes, exact-display eligibility, product grain, elapsed days, date filters, zero denominators, Wilson intervals, tier boundaries, sensitivity separation, and prohibited metrics. Key checks include:

- 100 positive of 200 eligible products equals 50% breadth.
- Product medians `[-1, 0, 3]` produce a category median of `0`.
- Positive + zero + negative product counts reconcile to eligible products.
- Breadth remains in 0%-100%; counts are nonnegative integers.
- `n=0` yields `INSUFFICIENT` and blank movement KPIs.
- `n=100`, 20 dates, and 19-point Wilson width yields `HIGH`.
- Compact and outlier sensitivities never alter the exact-only primary values.
- No approved KPI uses `total_sold`, `total_rating`, sales, revenue, orders, AOV, customers, conversion, campaign effectiveness, or a composite momentum score.

The complete test contract is `outputs/tables/phase_6_kpi_validation_rules.csv`.

## 15. Quality gate and limitations

Every approved KPI has an explicit formula, grain, numerator/denominator behavior, eligibility, exclusion, minimum sample, missing/approximate/outlier/category-change rules, Power BI notes, and validation rule. Small categories are protected through tier-based suppression. Zero denominators return blank, never a false zero. No analytical dataset was modified.

Remaining limitations survive unchanged: short window, uneven unknown sampling, sparse repeats, favorites as an engagement proxy, loss of compact-display coverage, irregular intervals, and no commercial/causal evidence.

## 16. Artifacts

- `docs/business_question_governance.md`
- `docs/kpi_definitions.md`
- `outputs/tables/phase_6_kpi_specification.csv`
- `outputs/tables/phase_6_kpi_validation_rules.csv`
- `outputs/tables/phase_6_kpi_dependency_map.csv`
- `outputs/tables/phase_6_category_eligibility_rules.csv`
- `outputs/tables/phase_6_kpi_design_validation_results.csv`
- `src/analysis/build_phase_6_kpi_specs.py`
- `outputs/analysis_results/phase_6_kpi_design_manifest.json`
- `tests/data_validation/validate_phase_6_kpi_design.py`
- `reports/phase_6_kpi_design_report.md`

Phase 6 definitions are frozen and `COMPLETED`; the current Phase 7 broad-category analysis applies them without modification.
