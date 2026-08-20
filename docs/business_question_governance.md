# Phase 6 Business Question Governance

Status: `REVIEW REQUIRED`  
Governed window: 2023-04-24 through 2023-05-13 (20 dates)  
Primary category grain: Level 2  
Evidence basis: validated Phase 2-4 structures and Phase 5 facts

## Governance decision

The original Big Question is not supported. The proposed sampled-listing traction reframing is supportable only after narrowing “traction” to a transparent scorecard of favorite-engagement movement, sampled scale, and evidence sufficiency. It is not a sales, demand, platform-growth, or campaign-performance construct.

The final governed analytical question is:

> Which Broad Product Categories show stronger observed favorite-engagement movement among eligible repeatedly tracked listings in this 20-day sampled dataset, when breadth, typical per-day movement, sampled scale, and evidence sufficiency are reported separately?

The word “stronger” permits governed comparison in Phase 7, but only for categories meeting the evidence rules. It does not authorize a platform ranking or campaign recommendation.

## Original Big Question component review

Original wording:

> Which product categories are gaining momentum fastest on the platform, and which of those should a marketplace's category team prioritize featuring in upcoming campaigns and collections?

| Component | Support decision | Reason | Missing evidence |
|---|---|---|---|
| A. “categories” | Supported with restriction | Level-2 categories are complete and broad enough for the sample. Deeper levels are fragmented; eight products change Level 2. | A source-governed taxonomy and stable category history would be needed for unrestricted category claims. |
| B. “gaining momentum” | Not supported as business or sales momentum | No verified sales or outcome measure exists. Favorites can describe observed engagement movement only. | Verified longitudinal orders/units/revenue or another validated business outcome over a longer period. |
| C. “fastest” | Not supported as written; replace with gated “stronger observed movement” | Per-day normalization can compare the proxy, but sparse histories, rounded values, and uncertainty prevent an unconditional fastest-category claim. | Regular longitudinal measurement, sufficient matched products, validated outcome semantics, and stable results across definitions. |
| D. “on the platform” | Not supported | The data is an uneven scraped sample, not a census or known probability sample. Daily volume varies 18.54×. | Known sampling frame, inclusion probabilities, or platform-wide aggregates. |
| E. “prioritize featuring” | Not supported | Engagement-display movement alone does not establish commercial value or operational feasibility. | Conversion, margin, inventory, assortment strategy, audience fit, opportunity cost, and decision thresholds. |
| F. “upcoming campaigns and collections” | Not supported | There is no campaign exposure, outcome, control, seasonality, or future-demand evidence. | Campaign history, impressions/clicks/conversion, treatment/control evidence, calendar context, inventory, margin, and forecast horizon. |

The unsupported components are not silently rewritten. They remain documented exclusions.

## Governed operational definitions

| Term | Governed definition | What it does not mean |
|---|---|---|
| Observed | Directly displayed listing attributes captured in the sample on its recorded dates. | Verified transactions, latent demand, or platform estimates. |
| Favorite engagement | The displayed favorite count, treated as a secondary engagement proxy. Primary movement uses exact displays only. | Purchases, customers, conversion, or causal campaign response. |
| Traction | A non-composite scorecard: Positive Favorite-Movement Breadth, Median Daily Favorite Movement per Product, Observed Stable-Category Product Count, Eligible Favorite-Movement Product Count, and Evidence Sufficiency Tier. | A weighted momentum score, sales growth, or a single rank. |
| Repeatedly tracked | A product with at least two snapshots and at least one eligible consecutive favorite interval: both endpoints exact and valid, elapsed days positive, both dates in context, and no Level-2 change anywhere in its study history. | Every repeated product, or products with rounded/missing endpoints in the primary cohort. |
| Category | The validated Level-2 category for products whose Level-2 membership is stable across the study. | Level-3/4 taxonomy or a platform-governed category universe. |
| Sampled dataset | 20,312 listing snapshots for 16,614 products observed on 20 dates from 2023-04-24 to 2023-05-13 under an unknown, uneven scraping process. | A representative Shopee Malaysia panel or platform census. |

## Analysis contract

### Question as measurable claim

- Plain question: Which sampled Level-2 categories exhibit stronger observed favorite-engagement movement?
- Measurable version: compare product-level positive favorite breadth and the median of product-level daily favorite changes, accompanied by stable-category product scale and an evidence tier.
- Do not claim: verified sales, demand, platform growth, causality, future performance, or campaign priority.

### Unit, numerator, denominator, and comparison

- Interval base unit: one consecutive product observation pair with both endpoints in the date context.
- KPI unit: one stable-category product summarized to its median eligible daily favorite change.
- Breadth numerator: eligible products whose product-level median daily change is greater than zero.
- Breadth denominator: all eligible products, including products with zero or negative medians.
- Magnitude statistic: category median of product-level median daily changes.
- Main comparison: Level-2 categories meeting at least `MODERATE` evidence.
- Sensitivities: compact-inclusive, outlier-endpoint-excluded, and interval-weighted results, kept separate from the primary values.

### Support, weakening, and falsification

- A sampled category pattern is supported for further investigation when evidence is `HIGH`, the Wilson lower bound for positive breadth exceeds 50%, median daily movement is positive, and required sensitivities do not conflict.
- It is weakened by `MODERATE` evidence, a zero median, wide uncertainty, material sensitivity differences, or high dependence on observation rules.
- It is not comparable when evidence is `INSUFFICIENT`; KPI cells must be blank, not zero.
- The interpretation is falsified as a robust sampled engagement pattern when the direction changes under reasonable compact, outlier, or weighting sensitivity definitions.
- Even a robust sampled engagement pattern cannot validate sales momentum, platform growth, or campaign causality.

## Why the final question is supported

The Phase 4 matched table provides consecutive product intervals with positive elapsed days, favorite comparison status, category history, and lineage. Phase 5 shows 3,489 valid favorite intervals and meaningful directional variation, unlike average rating, while exposing the compact-display and sampling limitations. Product-level aggregation avoids overweighting the minority of products with more intervals, exact-only primary values prevent rounded displays from being treated as exact, and evidence gates prevent sparse categories from appearing equally reliable.

Support remains conditional and sample-bound. The question is suitable for a transparent portfolio analysis, not for estimating marketplace performance.

## Legitimate dashboard claims

The dashboard may claim that, within the sampled 20-day listing data:

- an eligible sampled category had a stated share of products with positive exact displayed-favorite movement;
- the typical eligible product had a stated median displayed-favorite change per elapsed day;
- the comparison used a disclosed number of stable-category products and sampled dates;
- evidence met a declared `HIGH`, `MODERATE`, or `INSUFFICIENT` rule;
- results were or were not stable under required sensitivity definitions.

## Claims the dashboard must not make

The dashboard must not claim sales, units, revenue, orders, AOV, customers, conversion, market share, platform-wide category growth, demand, causality, campaign effectiveness, future performance, or a campaign priority. It must not use `total_sold`, `total_rating`, price × sold, or a composite momentum score. Displayed prices are not realized revenue, and favorites are not purchases.

## Business decision boundary

Passing the analytical follow-up rule means only “worth further investigation.” A campaign decision additionally requires verified conversion or commercial outcomes, margin, inventory, audience and assortment fit, campaign cost, risk, and ideally causal or controlled evidence. Phase 6 defines no campaign recommendation.
