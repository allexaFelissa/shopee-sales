# Phase 8 Power BI Handoff

Status: `REVIEW REQUIRED`  
Target phase: Phase 9 only after explicit approval  
Power BI dashboard built in Phase 8: **No**

## Non-negotiable analytical contract

Power BI must display the governed question exactly:

> Which broad product categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

The five approved KPIs remain:

1. Observed Stable-Category Product Count
2. Eligible Favorite-Movement Product Count
3. Positive Favorite-Movement Breadth
4. Median Daily Favorite Movement per Product
5. Evidence Sufficiency Tier

Do not create a momentum score, performance rank, sales/revenue/order/customer/conversion metric, campaign-effectiveness metric, or campaign recommendation.

## Tables to use

| Power BI role | File | Grain | Use |
|---|---|---|---|
| Category scorecard fact | `outputs/tables/phase_7_category_comparison.csv` | one Broad Product Category for the fixed 20-day window | Main KPI values, denominators, dates, Wilson uncertainty, eligible share, sensitivity status, interpretation |
| Published category view | `outputs/tables/phase_7_category_business_analysis.csv` | one Broad Product Category | Reconciliation of the five displayed KPIs and governed blank behavior |
| Sensitivity fact | `outputs/tables/phase_7_sensitivity_analysis.csv` | Broad Product Category × sensitivity scenario | Primary-versus-alternative plots and tooltip differences |
| Findings text | `outputs/tables/phase_7_business_findings.csv` | finding | Approved explanatory callouts; not a ranking table |
| Visual contract | `outputs/tables/phase_8_visual_specification.csv` | visual | Titles, encodings, filters, safeguards, and tooltip requirements |
| Dashboard contract | `outputs/tables/phase_8_dashboard_specification.csv` | page | Page purpose, content, interactions, and limitations |

Use Phase 7 publication tables rather than recalculating KPI cohorts from raw or Phase 4 tables inside Power BI. Phase 9 must reconcile measures to the publication values before release.

## Recommended model

```text
Dim Broad Product Category (24 unique categories)
        1 ───────────── 1  Category Scorecard Fact
        │
        └────────────── *  Sensitivity Fact

Findings Text (disconnected or keyed only for approved callouts)
```

- Create the category dimension from the distinct governed category values during Power Query/model preparation; do not create a new project dataset in Phase 8.
- Keep the fixed study window explicit. Phase 7 tables are already aggregated to this window.
- Do not expose a date slicer against precomputed KPIs. A date filter would change evidence gates and denominators without recomputation.
- Use a one-to-many relationship from category to sensitivity.
- The scorecard and publication tables are both one row per category; prefer the comparison table as the model fact and retain the publication table as a reconciliation input or merge its business interpretation carefully.
- Avoid bidirectional relationships and many-to-many category relationships.

## Field naming

Use business-facing names in the report:

| Source field | Display name |
|---|---|
| `broad_product_category` | Broad Product Category |
| `observed_stable_category_product_count` | Observed Stable-Category Products |
| `eligible_favorite_movement_product_count` | Eligible Tracked Products |
| `positive_favorite_movement_breadth` | Positive Favorite-Movement Breadth |
| `median_daily_favorite_movement_per_product` | Median Daily Favorite Movement per Product |
| `evidence_sufficiency_tier` | Evidence Sufficiency Tier |
| `observed_date_count` | Observed Dates |
| `positive_breadth_wilson_95_lower_percent` | Breadth Wilson 95% Lower |
| `positive_breadth_wilson_95_upper_percent` | Breadth Wilson 95% Upper |
| `sensitivity_status` | Sensitivity Status |

Map Broad Product Category to source `category_level_2` once in a methodology note; do not use “Level-2 Product Category” as the report label.

## Fields not to expose

- `total_sold`, any parsed equivalent, or any field presented as sales/units.
- `total_rating` as a proxy or outcome.
- Price × sold, revenue, AOV, order, customer, conversion, market-share, demand, or campaign fields.
- Internal row numbers, URLs, raw descriptions, source-system status flags, and raw favorite strings.
- A free-form date slicer, interval-length slicer, favorite-format slicer, outlier switch, category-stability switch, or eligibility-rule override.
- `further_investigation_candidate_flag` as a promotional badge. Its all-false state may be summarized only as “formal gate passes: 0.”
- Technical scenario codes in business-facing labels; translate them with the governed display names.

## Page 1 — Category Engagement Overview

- **Purpose:** orient the viewer and compare the publishable category landscape without a composite score.
- **Audience:** category lead and portfolio reviewer.
- **Question:** Which sampled categories show wider and larger observed favorite-engagement movement, and how much evidence supports them?
- **Cards:** fixed 20-day period; Observed Stable-Category Products; Eligible Tracked Products; category counts by evidence tier. Label the tier counts as supporting overview statistics, not performance KPIs.
- **Primary visual:** recreate V01 breadth-versus-magnitude scatter.
- **Secondary content:** compact evidence-tier strip and approved callouts for Groceries & Pets, Health & Beauty, Women's Bags, and the all-category gate result.
- **Filters:** Evidence Sufficiency Tier, Sensitivity Status, and an optional category highlighter. Default must retain all categories.
- **Interaction:** filters cross-highlight rather than silently remove context where possible. Selecting a category enables drill-through to Page 2.
- **Required text:** “Observed favorite engagement among eligible tracked listings in a sampled 20-day dataset. Not sales or platform growth.”
- **Footnote:** ten categories have insufficient evidence and are N/A/unranked; no category passes the complete formal further-investigation gate.

## Page 2 — Category Evidence Deep Dive

- **Purpose:** explain why a selected category looks noteworthy, mixed, weak, or uninterpretable.
- **Audience:** analyst and category lead validating a category.
- **Question:** What breadth, typical movement, denominator, calendar presence, evidence tier, and sensitivity pattern support this category?
- **Cards:** the four category values plus the Evidence Sufficiency Tier. Movement cards return blank with the text `N/A — insufficient evidence` when the tier is insufficient.
- **Charts:** selected-category breadth; selected-category median movement; observed-versus-eligible evidence context; selected-category sensitivity comparison; observed-date microbar/text.
- **Filter:** single-select Broad Product Category.
- **Sensitivity control:** may choose which alternative is displayed, but the primary exact/product result must remain fixed and visually dominant.
- **Drill-through:** receive category from Page 1 and include a back button. Do not add product-level drill-through until a governed product-level supporting fact is explicitly approved for the model.
- **Tooltips:** numerator, denominator, zero/negative counts, exact-only label, dates, Wilson bounds, tier, sensitivity status, primary and alternative values.
- **Required note:** evidence tier is evidence availability, not category performance.

## Page 3 — Evidence & Limitations

- **Purpose:** make evidence gates, sensitivity, and unsupported interpretations impossible to overlook.
- **Audience:** reviewer, analyst, governance stakeholder.
- **Question:** Which results can be compared, which are sensitivity-dependent, and what can the sample not establish?
- **Cards:** HIGH 4; MODERATE 10; INSUFFICIENT 10; complete formal gate passes 0.
- **Charts:** recreate V02 evidence sufficiency, V03 eligible evidence, and V06 sensitivity summary; list all ten N/A categories.
- **Filters:** Evidence Sufficiency Tier and Sensitivity Status only.
- **Text:** show exact HIGH/MODERATE/INSUFFICIENT gate definitions.
- **Limitations block:** cannot determine sales growth, revenue growth, order growth, customer demand, market share, platform-wide category growth, campaign effectiveness, discount/pricing causality, or future category performance.

## Visual recreation requirements

### Scatter

- X = `[Positive Favorite-Movement Breadth]`.
- Y = `[Median Daily Favorite Movement per Product]`.
- Details = Broad Product Category.
- Size = `[Eligible Favorite-Movement Product Count]`.
- Legend/shape = Evidence Sufficiency Tier. If the native scatter cannot encode shape, use color plus direct tier label/tooltips and preserve neutral semantics.
- Exclude insufficient rows from numeric coordinates through blank KPI behavior, not a visual-level “not zero” hack.
- Add a 50% breadth line labeled “product-majority reference—not target.”

### Breadth and magnitude comparisons

- Keep tier-group order and category name order; do not sort all categories into a single winner list.
- Preserve N/A as a separate status field or matrix column.
- Use no conditional formatting that turns HIGH green or INSUFFICIENT red.

### Sensitivity

- Use small multiples or an approved paired-dot custom visual.
- Repeat the primary exact/product point in every panel.
- Do not average scenarios.
- Directly label `ROBUST`, `DIRECTIONALLY STABLE`, `SENSITIVE`, and `UNSTABLE` with the Phase 7 values.
- `NOT_ASSESSABLE_INSUFFICIENT_EVIDENCE` must display as `Not assessable — insufficient evidence`.

## Filter and denominator behavior

- Category and tier filters operate on the fixed publication layer.
- Sensitivity Status may filter category rows but must not change primary KPI calculations.
- Scenario selection changes only the alternative comparison series.
- Insufficient evidence returns blank for breadth and median; use an accompanying status text measure to show N/A.
- No filter may include compact observations in the primary KPI, retain category-changing products, change product-versus-interval weighting, or bypass evidence suppression.
- The 20-day context is a report label, not a slicer, unless Phase 7 is rerun under a separately governed context.

## Tooltip requirements

Every category movement tooltip should include:

- Broad Product Category
- primary/sensitivity label
- Positive Favorite-Movement Breadth
- positive product count
- Eligible Tracked Products denominator
- Median Daily Favorite Movement per Product
- Evidence Sufficiency Tier
- observed dates out of 20
- Wilson lower, upper, and width
- Sensitivity Status
- statement: “Favorite engagement in sampled eligible listings; not sales.”

## Interaction safeguards

- Default view contains all 24 categories, including the N/A group.
- A category selection may highlight related evidence but must not recalculate from raw intervals.
- Cross-filtering from the sensitivity visual should not redefine the scorecard cohort.
- Clear-filter/reset navigation should restore the governed all-category view.
- Avoid decorative bookmarks, animations, and slicers unrelated to a page question.

## Validation benchmarks for Phase 9

- 24 Broad Product Categories.
- Evidence tiers: HIGH 4, MODERATE 10, INSUFFICIENT 10.
- Groceries & Pets: breadth 64.28571429%, median 0.2111111111 favorites/day, eligible products 112, HIGH, `DIRECTIONALLY_STABLE`.
- Health & Beauty: breadth 62.90801187%, median 0.1666666667, eligible products 337, MODERATE, `ROBUST`.
- Women's Bags: breadth 58.69565217%, median 0.2792207792, eligible products 46, MODERATE, `ROBUST`.
- Automotive and Sports & Outdoor: median 0; breadth below 50%; `ROBUST` does not mean strong movement.
- Ten insufficient categories: blank breadth and median, never zero.
- Outlier-excluded governed movement values equal primary values for all 14 published categories.
- Compact-inclusive breadth is the principal divergence, including a 10.86 percentage-point difference for Groceries & Pets.

Phase 9 must reconcile these benchmarks and every displayed denominator before dashboard review.

