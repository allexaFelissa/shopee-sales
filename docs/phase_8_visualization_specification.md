# Phase 8 Controlled Visualization Specification

Status: `COMPLETED`
Publication grain: 12 governed Broad Product Categories
Window: 2023-04-24 through 2023-05-13

## Evidence contract

The six visuals consume recalculated Phase 7 publication tables. They do not aggregate or relabel former Level-2 KPIs. `category_level_2` remains in upstream data for lineage, but is not the primary Phase 8 publication category.

- Primary: exact-display, product-level favorite movement.
- Denominator: eligible repeatedly tracked products after the unchanged Level-2 stability exclusion.
- Breadth: share of eligible products with positive product medians.
- Magnitude: median daily favorite movement across product medians.
- Evidence: date presence, eligible-product count, and Wilson precision.
- Sensitivities: compact-inclusive, outlier-excluded, and interval-weighted.
- Missingness: insufficient movement values are N/A, never zero.

## Visual inventory

| ID | Form | Analytical job | Principal safeguard |
|---|---|---|---|
| V01 | Labeled bubble scatter | Compare breadth with typical magnitude | No quadrant priority language; insufficient groups excluded from quantitative axes |
| V02 | Evidence bar/table hybrid | Show products, dates, Wilson width, and tier for all 12 groups | Tier explicitly means evidence availability, not performance |
| V03 | Horizontal lollipop | Show eligible tracked-product denominator | Explicitly not category size, market share, or demand |
| V04 | Dot-and-Wilson-interval plot | Compare exact-display positive breadth | Four insufficient groups shown as N/A outside the numeric scale |
| V05 | Horizontal lollipop | Compare exact-display median favorites/day | Two-stage median and zero interpretation stated; insufficient groups N/A |
| V06 | 2×3 paired-dot small multiples | Compare breadth and median under three sensitivities | Primary hollow circle dominates; no scenario averaging or score |

The detailed machine-readable contract is `outputs/tables/phase_8_visual_specification.csv`.

## Semantic design

Broad Product Category is the sole primary publication identity. Position carries the quantitative comparison; restrained blue/grey styling and marker shape carry evidence context. HIGH is not green, INSUFFICIENT is not red, and ROBUST is never used as a synonym for strong movement. Categories are grouped by evidence for reading, not sorted into business priority.

Reference lines have limited meanings: 50% breadth denotes a product majority, zero median separates positive from nonpositive typical movement, and 30/100 product guides show only one component of the evidence rules. None is a performance target.

## Chart-selection rationale

The scatter is appropriate because the question asks about a relationship between two distinct continuous measures. Horizontal aligned plots preserve long labels and accurate category comparisons. Evidence counts use a zero baseline. Sensitivities use small multiples because breadth and median have different units and because alternatives must remain comparisons to the primary rather than being blended.

Rejected forms include a composite score, quadrant priority matrix, pie/donut, automatic ranking, sales proxy, and date-sliced trend. Each would either combine governed concepts, imply an unsupported decision, or conflict with the fixed-window facts.

## Interpretation boundary

The figures may describe sampled favorite-engagement signals, observed movement, evidence availability, sensitivity, and need for further validation. They cannot establish sales, revenue, orders, customer demand, market share, platform growth, campaign effectiveness, future performance, or campaign priority.

No Broad Product Category passes the complete further-investigation gate.
