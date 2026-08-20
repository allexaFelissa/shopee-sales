# Phase 8 Visualization Report

Status: `REVIEW REQUIRED`  
Visualization version: `1.0.0`  
Window: 2023-04-24 through 2023-05-13

## 1. Executive Summary

Phase 8 converts the approved Phase 7 category findings into six reviewed analytical visuals and a three-page Power BI specification. The design keeps breadth, typical movement, eligible product scale, evidence quality, and sensitivity separate. It creates no composite score, performance ranking, sales metric, or campaign recommendation.

The executive scatter makes the central analytical distinction visible: a category may have a positive typical movement without a majority of products moving positively, and strong evidence availability does not guarantee a strong or robust engagement pattern. Ten insufficient categories remain visible as N/A and unranked rather than being plotted at zero.

All six final PNGs passed manual delivery-size inspection. The independent validation gate passed 57 of 57 checks. Ten generated artifacts reproduced byte-for-byte with zero SHA-256 differences, and all governed Phase 4, Phase 6, and Phase 7 input hashes remained unchanged.

## 2. Visualization Objectives

The visual system allows a stakeholder to understand:

- what the sample measures and what it cannot measure;
- how widespread positive favorite movement is among eligible products;
- how large the typical per-day product movement is;
- how many products and dates support each category;
- which categories have published versus suppressed movement values;
- whether the primary result changes under the three governed sensitivities.

The objective is evidence-aware interpretation, not a “Top 5” category list.

## 3. Governed Question

> Which broad product categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

Broad Product Category maps to the source `category_level_2` field. The question remains sample-bound and does not support a platform-wide claim.

## 4. Approved KPI Framework

Phase 8 uses only:

1. Observed Stable-Category Product Count
2. Eligible Favorite-Movement Product Count
3. Positive Favorite-Movement Breadth
4. Median Daily Favorite Movement per Product
5. Evidence Sufficiency Tier

Exact favorite displays remain primary. Compact-inclusive, outlier-excluded, and interval-weighted results are labeled sensitivities. Category-changing products remain excluded. Insufficient evidence suppresses movement values to blank.

## 5. Visualization Story

The story begins with the governed proxy and time window, then moves from the category landscape to the two movement dimensions, evidence sufficiency, sensitivity, and finally limitations. This sequence prevents a visually prominent category from being interpreted before its denominator and reliability are understood.

The central visual is not a quadrant classifier. The scatter uses X and Y position for the two movement dimensions, point size for eligible products, and evidence tier as a redundant color/shape grouping. A companion side panel explains the three focal patterns and the N/A universe.

## 6. Visual Inventory

| Visual | Purpose | Main safeguard |
|---|---|---|
| V01 Breadth vs magnitude | See relationship and disagreement across published categories | Explicitly not a campaign-priority map |
| V02 Evidence sufficiency | Explain tier using products, dates, and precision | Tier is labeled as evidence, not performance |
| V03 Eligible tracked products | Expose sample denominator scale | Not market/category size |
| V04 Breadth | Compare how widespread positive movement is | Denominator and Wilson interval shown; N/A outside scale |
| V05 Median movement | Compare typical movement magnitude | Two-stage median and zero meaning disclosed |
| V06 Sensitivity | Compare primary with three governed alternatives | Primary repeated and foregrounded in every panel |

## 7. Chart Selection Rationale

The scatter is the simplest form that supports the relationship between two separate movement dimensions. Horizontal aligned plots are used for dense category comparisons because long category labels remain readable and quantitative position is precise. The evidence view uses bars because eligible product count has a meaningful zero baseline. Sensitivity uses aligned paired dots in small multiples because the task is comparing each alternative with the same primary value, not blending scenarios.

Rejected core forms include pie/donut charts, a composite scorecard rank, four-quadrant category labels, and a dense date heatmap. Those forms either weaken quantitative comparison, imply an unsupported decision threshold, or add detail without serving the governed question.

## 8. Evidence Visualization

Evidence quality appears in every relevant visual but is never colored as “good” or “bad.” The main evidence view reports eligible products, dates out of 20, and Wilson interval width. Threshold guides at 30 and 100 products explain only the product-count component; direct labels prevent those guides from being mistaken for the complete tier rule.

The evidence distribution remains HIGH 4, MODERATE 10, and INSUFFICIENT 10. HIGH indicates stronger within-sample evidence availability, not performance. This distinction is especially important because Men Clothes, Mobile & Accessories, and Women Clothes are HIGH but sensitivity-unstable.

## 9. Sensitivity Visualization

The sensitivity summary uses three aligned panels:

- compact-inclusive versus primary exact/product;
- outlier-excluded versus primary;
- interval-weighted versus primary product-level breadth.

The primary exact/product result uses the same hollow navy circle in all panels. When the outlier-excluded value is identical, the smaller alternative marker sits inside a visible primary ring. This makes the Phase 7 result—no governed change for all 14 published categories—visually legible instead of hiding one series.

Compact displays remain the principal source of instability. The chart does not imply that the alternative specification is a correction; rounded displays cannot identify exact movement.

## 10. Dashboard Page Architecture

### Page 1 — Category Engagement Overview

Answers which categories show wider and larger sampled engagement signals and how much evidence supports them. It uses the scatter, limited context cards, evidence tier controls, and approved callouts.

### Page 2 — Category Evidence Deep Dive

Explains one selected category through breadth, typical magnitude, eligible products, date coverage, Wilson uncertainty, tier, and sensitivity. It uses a single-select category control and keeps the primary result fixed.

### Page 3 — Evidence & Limitations

Explains tier gates, eligible-product scale, full sensitivity results, all N/A categories, and unsupported claims. It is the governance page, not a low-priority appendix.

## 11. Interaction Design

Only Broad Product Category, Evidence Sufficiency Tier, and Sensitivity Status are proposed as filters. Sensitivity scenario may act as a labeled comparison control on the deep-dive page, but cannot replace the primary. A free-form date filter is prohibited because Phase 7 values are precomputed for the governed window and evidence gates would need to be recalculated.

Cross-highlighting is preferred to removing context. Drill-through is limited to category-to-deep-dive navigation. No interaction may bypass exact-display, stable-category, product-level, or evidence-suppression rules.

## 12. Accessibility / Readability

The system uses a white background, dark text, restrained grids, direct labels, and a color-blind-safer neutral blue/grey palette. Evidence tiers use marker shape in addition to color. Sensitivity scenarios use distinct shapes and direct legend labels. Long categories are horizontal, and all final PNGs exceed the minimum delivery dimensions validated by the test suite.

## 13. Visual QA Results

The first render exposed two major presentation defects: four subtitle lines overlapped their titles, and panel legends obscured the bottom sensitivity row. Identical outlier values also visually hid the primary point. These defects were corrected by moving titles/subtitles to figure-level layout, consolidating the sensitivity legend above the panels, and drawing the primary as a larger hollow circle.

The final review checked labels, units, axes, sorting, category names, N/A behavior, evidence semantics, overlaps, legends, annotations, and the risk of a sales-growth reading. Six of six final exports received `PASS_VISUAL_QA`. Structured results are in `outputs/tables/phase_8_visual_qa.csv`.

## 14. Power BI Handoff

The handoff freezes the three-page architecture, table roles, field names, filter behavior, tooltip content, N/A behavior, evidence semantics, and validation benchmarks. Phase 9 should use the Phase 7 category and sensitivity publication tables, not recompute the analytical cohort from raw data.

The handoff explicitly blocks raw sales/rating counters, platform-share language, date slicing against fixed aggregates, and any visual or interaction that treats a sensitivity as the primary KPI.

## 15. Limitations

The visualization layer describes observed displayed-favorite engagement among eligible repeatedly tracked listings in an uneven 20-day sample. It cannot determine sales growth, revenue growth, orders, customers, conversion, market share, platform-wide category growth, customer demand, campaign effectiveness, causal price/discount impact, or future performance.

No category passes the complete Phase 6 gate for formal further business investigation. Visual emphasis on Groceries & Pets, Health & Beauty, or Women's Bags communicates an observed pattern requiring validation, not a campaign recommendation.

## 16. Phase 9 Requirements

Phase 9 must:

- follow `docs/phase_8_powerbi_handoff.md` without redesigning KPI logic;
- use the five approved KPIs and the Phase 7 publication facts;
- preserve exact-only primary values and blank insufficient values;
- reconcile all cards, charts, filters, and tooltips to the Phase 7 benchmarks;
- keep evidence tier distinct from performance;
- retain the sample/proxy limitations on every page;
- create no campaign recommendation.

Phase 9 remains `NOT STARTED` until explicit user approval.

