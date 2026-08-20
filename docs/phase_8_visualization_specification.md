# Phase 8 Visualization Specification

Status: `REVIEW REQUIRED`  
Visual layer version: `1.0.0`  
Analysis window: 2023-04-24 through 2023-05-13 (20 dates)  
Business-facing category: **Broad Product Category** = source `category_level_2`

## Governed purpose

The visual layer answers:

> Which broad product categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

The visuals communicate a sampled listing-engagement scorecard. They do not estimate sales, revenue, orders, customers, demand, market share, platform growth, campaign effectiveness, or future performance. No visual combines the approved KPIs into a composite score or final category ranking.

## Audience and delivery context

- Primary audience: marketplace category stakeholder and non-technical portfolio reviewer.
- Secondary audience: analyst reviewing KPI evidence and implementation details.
- Phase 8 medium: inspected static PNG analytical exports.
- Phase 9 medium: approximately three interactive Power BI pages based on the same governed facts.
- Intended first read: movement breadth and typical magnitude are different; evidence quality controls whether either value can be interpreted.

## Visual story

1. **Context:** state the 20-day sampled-listing window, the favorite-engagement proxy, and the explicit non-sales boundary.
2. **Executive category view:** show breadth and typical movement together, with eligible product count and evidence tier visible but not combined.
3. **Breadth versus magnitude:** explain whether positive movement is widespread and whether the typical product moves meaningfully.
4. **Evidence quality:** expose category-level product counts, observed dates, Wilson precision, and suppression.
5. **Sensitivity:** keep the exact-display product-level result primary and compare each governed alternative separately.
6. **Limitations:** retain N/A for insufficient evidence and repeat the unsupported-claim boundary on every page.

## Semantic system

### Evidence quality

Evidence tier is not performance. It uses a neutral blue/grey family plus a redundant shape channel:

| Tier | Color | Shape | Meaning |
|---|---|---|---|
| HIGH | dark navy | circle | All 20 dates, at least 100 eligible products, Wilson width at most 20 percentage points |
| MODERATE | mid blue | diamond | At least 15 dates, at least 30 eligible products, Wilson width at most 35 percentage points, but HIGH fails |
| INSUFFICIENT | grey | x or explicit N/A text | At least one MODERATE gate fails; movement values are unpublished |

No green/red performance scale is used. Direct labels, tier grouping, and status text prevent evidence meaning from depending on color alone.

### Primary and sensitivity

- Primary exact/product result: navy hollow circle in sensitivity comparisons.
- Compact-inclusive: orange diamond.
- Outlier-excluded: purple square.
- Interval-weighted exact: grey triangle.
- Primary remains visible when an alternative has the same value; alternatives never replace the governed primary.

### Missing and insufficient evidence

- Movement values for `INSUFFICIENT` categories stay blank.
- Comparison visuals retain the category row and show `N/A — insufficient evidence` in a separate status column.
- The scatter does not place insufficient categories at `(0, 0)`; a side note reports that ten categories are N/A and unranked.
- A true zero is shown only for an approved count or a published median that is actually zero.

## Visual inventory

| ID | Visual | Main job | Phase 8 export |
|---|---|---|---|
| V01 | Category breadth vs magnitude | Relate breadth and typical movement without a score | `phase_8_category_breadth_vs_magnitude.png` |
| V02 | Evidence sufficiency | Show why analytical support differs across categories | `phase_8_evidence_sufficiency.png` |
| V03 | Eligible tracked products | Expose the denominator scale behind movement KPIs | `phase_8_eligible_tracked_products.png` |
| V04 | Breadth comparison | Compare how widespread positive movement is | `phase_8_positive_breadth_by_category.png` |
| V05 | Median movement comparison | Compare typical per-day displayed-favorite movement | `phase_8_median_daily_movement_by_category.png` |
| V06 | Sensitivity summary | Compare the primary result with all required sensitivities | `phase_8_sensitivity_summary.png` |

The complete machine-readable contract is `outputs/tables/phase_8_visual_specification.csv`.

## V01 — Category breadth vs magnitude

- **Title:** Breadth and typical movement reveal different sampled engagement patterns.
- **Business question:** Which sufficiently evidenced categories combine wider positive movement with larger typical daily movement?
- **Chart type:** bubble scatter with an explanatory side panel.
- **X-axis:** Positive Favorite-Movement Breadth, percent of eligible tracked products.
- **Y-axis:** Median Daily Favorite Movement per Product, displayed favorites per product per day.
- **Point:** Broad Product Category.
- **Point size:** Eligible Favorite-Movement Product Count.
- **Group treatment:** Evidence Sufficiency Tier uses color and shape.
- **Filters:** fixed 20-day window; exact-display primary cohort; stable-category products; only HIGH/MODERATE categories receive quantitative coordinates.
- **Sorting:** none; points occupy their governed coordinates and are not ranked.
- **Tooltip:** category, breadth, median movement, eligible products, evidence tier, observed dates, Wilson interval, sensitivity status.
- **Evidence treatment:** eligible count controls size; tier controls shape/color; the side panel discloses the ten N/A categories.
- **Missing treatment:** no insufficient point and no fake zero.
- **Why appropriate:** two positional encodings keep breadth and magnitude separate while revealing disagreement. Size adds denominator context without combining values.
- **Misinterpretation risk:** the top-right region could be read as a campaign-priority quadrant.
- **Safeguards:** no quadrant names, score, winner label, or recommendation; the 50% line is explicitly a product-majority reference, not a target; the chart states that it is not a campaign-priority map.
- **Direct annotations:** Groceries & Pets, Health & Beauty, Women's Bags, and the Men Clothes / Men's Bags & Wallets / Watches breadth-magnitude disagreement.

## V02 — Evidence sufficiency

- **Title:** Evidence tier requires product count, calendar presence, and breadth precision.
- **Business question:** How much analytical support exists for each category?
- **Chart type:** horizontal evidence bar/table hybrid.
- **X-axis:** Eligible Favorite-Movement Product Count.
- **Y-axis:** all 24 Broad Product Categories.
- **Series:** Evidence Sufficiency Tier.
- **Measures/context:** eligible products, observed dates, Wilson 95% width, evidence tier.
- **Filters:** fixed governed window; all categories.
- **Sorting:** tier group, then category name; never movement performance.
- **Tooltip:** product count, dates, Wilson bounds/width, tier, and the failed gate where useful.
- **Evidence treatment:** 30- and 100-product reference lines plus direct tier/date/precision labels.
- **Missing treatment:** missing Wilson width is N/A; zero eligible products is a valid evidence count, not zero movement.
- **Why appropriate:** aligned bars make the product-count gate comparable while direct text carries the other two gates.
- **Misinterpretation risk:** HIGH may be mistaken for high performance.
- **Safeguards:** movement values are absent; subtitle explicitly says evidence availability is not category performance; colors are not good/bad semantics.

## V03 — Eligible tracked products

- **Title:** Eligible tracked-product counts show the evidence scale behind movement KPIs.
- **Business question:** How many independent product summaries support each category's movement values?
- **Chart type:** zero-based horizontal lollipop.
- **X-axis:** Eligible Favorite-Movement Product Count.
- **Y-axis:** all 24 Broad Product Categories.
- **Series:** Evidence Sufficiency Tier.
- **Filters:** exact-display primary eligibility; fixed window; stable-category products.
- **Sorting:** tier group, then category name.
- **Tooltip:** eligible products, Observed Stable-Category Product Count, eligible share of observed stable products, tier.
- **Evidence treatment:** direct count labels and tier grouping.
- **Missing treatment:** a displayed zero is a real eligible-product count, not a suppressed movement value.
- **Why appropriate:** an aligned zero baseline makes denominator scale easy to compare.
- **Misinterpretation risk:** eligible products could be read as market size or category size.
- **Safeguards:** title and subtitle call this evidence scale and explicitly reject market-share, category-size, and demand interpretations.

## V04 — Positive movement breadth

- **Title:** Positive-movement breadth shows how widespread the observed signal is.
- **Business question:** What share of eligible tracked products has positive movement in each sufficiently evidenced category?
- **Chart type:** horizontal dot-and-Wilson-interval plot with a separate availability column.
- **X-axis:** Positive Favorite-Movement Breadth, 0–100%.
- **Y-axis:** all 24 Broad Product Categories.
- **Series:** Evidence Sufficiency Tier.
- **Denominator:** all eligible product-level medians, including positive, zero, and negative values.
- **Filters:** exact-display primary cohort, stable category, fixed window.
- **Sorting:** tier group, then category name; not a momentum rank.
- **Tooltip:** positive/zero/negative product counts, denominator, breadth, Wilson bounds, evidence tier, sensitivity status.
- **Evidence treatment:** Wilson interval and tier marker; insufficient rows have no quantitative mark.
- **Missing treatment:** N/A text is outside the 0–100 quantitative area.
- **Why appropriate:** the aligned percentage position answers breadth, and uncertainty shows how precisely the share is observed.
- **Misinterpretation risk:** 50% may be read as a business target or proof of demand.
- **Safeguards:** denominator and proxy are explicit; the reference is descriptive only; no sales or demand language.

## V05 — Median daily movement

- **Title:** Typical movement magnitude remains separate from positive-movement breadth.
- **Business question:** What is the typical displayed-favorite movement per day for an eligible product in each category?
- **Chart type:** horizontal lollipop with a separate availability column.
- **X-axis:** Median Daily Favorite Movement per Product, favorites/day.
- **Y-axis:** all 24 Broad Product Categories.
- **Series:** Evidence Sufficiency Tier.
- **Aggregation:** interval change/day → product median → category median.
- **Filters:** exact-display primary cohort, stable category, fixed window.
- **Sorting:** tier group, then category name; not a rank.
- **Tooltip:** median movement, breadth, eligible products, tier, dates, sensitivity status.
- **Evidence treatment:** tier marker plus denominator label.
- **Missing treatment:** insufficient rows are N/A outside the quantitative region.
- **Why appropriate:** a common baseline exposes typical magnitude while the median limits the influence of extreme products.
- **Misinterpretation risk:** favorites/day may be mistaken for sales/day, and a zero median may be mistaken for no movement anywhere.
- **Safeguards:** the unit says displayed favorites; the two-stage median is disclosed; the subtitle explains the meaning of zero.

## V06 — Sensitivity summary

- **Title:** Primary exact-display breadth remains the reference across all sensitivities.
- **Business question:** Do published category breadth patterns remain similar under compact-inclusive, outlier-excluded, and interval-weighted specifications?
- **Chart type:** three aligned paired-dot panels.
- **X-axis:** Positive movement breadth, percent.
- **Y-axis:** 14 HIGH/MODERATE categories in a shared order.
- **Series:** primary exact/product compared separately with each sensitivity.
- **Filters:** sufficiently evidenced categories; all four governed scenarios.
- **Sorting:** tier group then category name, identical in every panel.
- **Tooltip:** primary/alternative values, percentage-point difference, median direction-change flag, material-conflict flag, sensitivity status, tier.
- **Evidence treatment:** sensitivity status is directly labeled on the right; the exact/product primary uses the same hollow navy marker in every panel.
- **Missing treatment:** insufficient categories are not quantitatively assessed and are disclosed as such.
- **Why appropriate:** small multiples prevent alternative definitions from being averaged or blended and make deviation from the primary visible.
- **Misinterpretation risk:** an alternative may be read as a corrected result or as a new KPI.
- **Safeguards:** primary remains foregrounded; every alternative is labeled as a sensitivity; no cross-scenario average or score exists.

## Annotation decisions

- **Groceries & Pets:** identify the strongest HIGH-evidence primary pattern and state `DIRECTIONALLY_STABLE`, not robust.
- **Health & Beauty:** identify the strongest robust positive pattern and explain that evidence is MODERATE because the category appears on 19 of 20 dates.
- **Women's Bags:** identify the largest published median while showing `n=46` and 17/20 dates.
- **Men Clothes, Men's Bags & Wallets, Watches:** label the breadth-magnitude disagreement: a positive median without a majority of products above zero.
- **Automotive and Sports & Outdoor:** describe robustness only in sensitivity views; do not imply strong movement because both have sub-50% breadth and a zero median.

## Optional visuals not approved for the core layer

- Date-coverage heatmap: rejected because V02 already exposes the decisive date count and an additional 24×20 grid would add density without changing the decision.
- Product-level concentration plot: retained as Phase 7 diagnostic evidence, not a core Phase 8 visual, because the approved category story is already protected by a two-stage median and outlier sensitivity.
- Category evidence matrix/quadrants: rejected because meaningful movement thresholds are not governed and quadrant labels would invite a pseudo-score.
- Price/discount visuals: rejected because they are not approved Phase 6 core KPIs and do not answer the governed question.

## Accessibility and readability rules

- White background, dark text, restrained grid lines, and minimum delivery-size PNG dimensions.
- No red/green dependency; evidence uses direct labels and redundant shape encoding.
- Categories use a common business-facing name and horizontal reading direction.
- Every figure contains a source/period/proxy note.
- Text labels and marks were inspected on the exact exports after rendering.
- Power BI tooltips must expose units, denominator, tier, dates, and sensitivity status without requiring the viewer to infer them.

## Visual QA outcome

All six exports passed source-value reconciliation, approved-KPI, terminology, denominator/unit, insufficient-as-N/A, evidence-semantics, claim-boundary, and delivery-size review. Initial overlaps in four title/subtitle regions and the sensitivity legend were corrected before release; the final artifacts have no unresolved fatal or major critique issue. See `outputs/tables/phase_8_visual_qa.csv` and `outputs/tables/phase_8_visual_validation_results.csv`.

