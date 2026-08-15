# Phase 5 — Exploratory Data Analysis Report

Status: `REVIEW REQUIRED`  
Study window: 2023-04-24 through 2023-05-13 (20 consecutive dates)  
Primary category grain: Level 2 (24 categories)  
Source: six validated Phase 4 analytical tables

## 1. Executive summary

Phase 5 found enough repeated-listing evidence to explore sampled engagement behavior, but not enough valid business-performance evidence to answer the original platform momentum and campaign-priority question. The sample contains 20,312 product snapshots for 16,614 products; only 3,070 products (18.48%) repeat, producing 3,698 irregular matched intervals. Daily volume ranges from 201 to 3,727 snapshots, an 18.54× spread, so raw listing-count changes cannot be interpreted as category growth.

Favorites provide the only changing engagement signal with useful coverage, but remain an approximate display measure: 4,738 of 19,241 valid snapshot values (24.62%) are compact/rounded. Across 3,489 valid favorite intervals, 1,518 (43.51%) increase, 1,891 (54.20%) are unchanged, and 80 (2.29%) decrease. The median normalized favorite change is zero in 15 of the 23 categories with any valid interval. Apparent high breadth in small categories has wide uncertainty and often high single-product influence.

The original Big Question is therefore **not defensibly answerable**. A narrower question about observed traction among repeatedly tracked sampled listings is **conditionally supportable for exploration**, provided Phase 6 governs the proxy, denominator, inclusion rules, uncertainty, and reliability requirements. This report does not approve that reframing, finalize a KPI, rank categories, or recommend campaigns.

## 2. Dataset structure

| Structure | Grain | Rows | Key / unit |
|---|---|---:|---|
| Product snapshots | Product listing on an observation date | 20,312 | (`product_id`, `observation_date`) |
| Matched observations | Consecutive observations for one product | 3,698 | Product plus previous/current dates |
| Product coverage | Product | 16,614 | `product_id` |
| Daily coverage | Date | 20 | `observation_date` |
| Category daily coverage | Level-2 category/date | 480 | (`category_level_2`, `observation_date`) |
| Category summary | Level-2 category | 24 | `category_level_2` |

Field availability is high for valid displayed price (20,282 snapshots; 99.85%), favorites (19,241; 94.73%), and average rating (19,384; 95.43%). Availability does not establish business meaning: prices are displayed listing values, favorites are partly rounded, ratings are nearly static, and neither `total_sold` nor `total_rating` is a verified sales measure.

## 3. Sampling and coverage

- Daily snapshots: mean 1,015.6, median 606, standard deviation 1,024.6, minimum 201, maximum 3,727, coefficient of variation 1.01.
- Daily maximum/minimum ratio: 18.54×. This is direct evidence of changing scraper coverage.
- Category snapshots range from 45 (`Others`) to 2,464 (`Health & Beauty`), a 54.76× evidence-volume spread.
- Only six categories appear on all 20 dates: `Groceries & Pets`, `Home Appliances`, `Men Clothes`, `Mobile & Accessories`, `Watches`, and `Women Clothes`.
- `Gaming & Consoles` appears on 9 dates, `Travel & Luggage` on 10, and `Others` on 2. Several additional categories miss 3–8 dates.
- The complete 24×20 category/date grid contains 97 absent category-date cells.

Consequently, observed daily or category listing totals are sampling diagnostics, not platform growth measures. Category comparisons must carry both date coverage and repeated-product evidence.

## 4. Product observation behavior

| Observations per product | Products | Share |
|---:|---:|---:|
| 1 | 13,544 | 81.52% |
| 2 | 2,535 | 15.26% |
| 3 | 449 | 2.70% |
| 4 | 79 | 0.48% |
| 5 | 7 | 0.04% |

- Repeated products: 3,070 of 16,614 (18.48%).
- Snapshot rows belonging to repeated products: 6,768 of 20,312 (33.32%).
- Products with 3+ observations: 535; products with 4+ observations: 86.
- Matched intervals span 1–19 days; median is 4 days and 2,043 of 3,698 (55.25%) are 1–4 days.
- Irregular gaps make per-day normalization useful for description, but they do not create a balanced panel.

Short-term matched comparison is possible for a minority cohort. Acceleration or sustained-change analysis is weak because most repeated products have only two observations.

## 5. Category structure

The Level-2 categories differ substantially in snapshot count, unique products, repeated products, calendar coverage, and valid engagement intervals. The most extensive repeated-product evidence is in `Men Clothes` (527 repeated products), `Health & Beauty` (443), `Women Clothes` (414), and `Mobile & Accessories` (389). At the opposite end, `Others` has no repeated products; `Tickets & Vouchers`, `Gaming & Consoles`, `Travel & Luggage`, and `Cameras & Drones` each have at most 13.

For a transparent Phase 5 follow-up screen—not a reliability tier—three evidence conditions were examined: all 20 dates observed, at least 75 distinct products contributing valid favorite intervals, and a Wilson 95% interval width no greater than 20 percentage points. Five categories pass all three:

| Category | Valid favorite intervals | Products | Positive breadth | Wilson width | Median favorite change/day |
|---|---:|---:|---:|---:|---:|
| Groceries & Pets | 163 | 146 | 51.53% | 15.17 pp | 0.083 |
| Home Appliances | 103 | 96 | 45.63% | 18.89 pp | 0.000 |
| Men Clothes | 613 | 481 | 39.48% | 7.72 pp | 0.000 |
| Mobile & Accessories | 482 | 380 | 40.66% | 8.74 pp | 0.000 |
| Women Clothes | 488 | 395 | 40.57% | 8.68 pp | 0.000 |

These are categories with a comparatively usable evidence base for further investigation, not “winning” categories. `Health & Beauty`, `Home & Living`, and `Baby & Toys` also have substantial interval evidence but miss one sampled date. Phase 6 must decide whether complete calendar presence is required and what precision is acceptable.

## 6. Price exploration

- Valid actual price: n=20,282; median 10.00; mean 345.10; 95th percentile 587.96; maximum 205,500.
- Valid original price: n=20,097; median 19.90; mean 404.48; 95th percentile 769.00; maximum 274,342.79.
- Valid discount percentage: n=20,086; median 8.88%; mean 25.59%; 46.4% of valid pairs have zero displayed discount.
- The Phase 2 deterministic method flags 2,353 actual-price snapshots as statistical outliers; they remain in the data.
- Mean-versus-median and 10% trimmed means demonstrate extreme right tails. `Automotive`, for example, has an actual-price mean/median ratio above 2,200, so raw means are not representative.
- Across valid matched pairs, the median actual-price change and median discount change are zero.

Price must be summarized robustly, and currency remains unverified. Displayed price cannot be interpreted as realized revenue, value, or campaign return.

## 7. Engagement exploration

Favorites:

- Valid snapshots: 19,241; median 207; mean 1,296.7; 95th percentile 5,900; maximum 96,600.
- Compact/rounded snapshots: 4,738 (24.62% of valid values).
- Valid matched intervals: 3,489; 1,518 positive, 1,891 zero, 80 negative.
- The all-interval positive breadth is 43.51%, while the typical interval change is zero.
- Exact-display-only comparisons contain 2,603 intervals (74.61% of valid intervals). Exact-only breadth is commonly higher than all-value breadth, by as much as 24.44 percentage points in `Muslim Fashion`. This demonstrates material rounding sensitivity rather than a corrected estimate.

Average rating:

- Valid snapshots: 19,384; median 4.9; mean 4.890; standard deviation 0.154.
- Valid matched intervals: 3,500; 3,414 (97.54%) unchanged, 34 positive, and 52 negative.
- Average rating supplies little short-window variation and is not a strong standalone traction signal.

## 8. Matched-product analysis

Matched intervals were analyzed at the current Level-2 category, with per-day normalization for unequal elapsed time. Favorite direction was evaluated only where both endpoints were valid; compact displays remained marked approximate. Product-level sensitivity first took each product's median daily favorite change before computing category breadth, preventing highly observed products from automatically receiving more weight.

All-interval favorite breadth and product-level breadth generally tell the same broad story, but differences of several percentage points occur in large categories. This shows that interval weighting can affect category summaries. Median price, discount, and average-rating changes are predominantly zero. No `total_sold` movement, sales velocity, revenue growth, or sales momentum field was calculated.

## 9. Category traction exploration

The exploratory dimensions remain separate:

1. Observed sample scale: snapshots and unique products.
2. Repeated-product evidence: products, intervals, and observation span.
3. Favorite movement: median change/day and positive/zero/negative breadth.
4. Evidence precision: Wilson interval width and distinct products.
5. Concentration: largest product's share of absolute favorite movement.
6. Sensitivity: exact displays, outlier endpoints, product weighting, and stable categories.
7. Sampling coverage: dates present and daily volume variation.

No single category is simultaneously proven to have “momentum” on all these dimensions. `Groceries & Pets` is the only category in the conservative follow-up screen with positive breadth above 50% and a positive median daily favorite change, but its 163 intervals are sampled engagement observations, 22.70% of absolute movement is attributable to its largest contributing product, and this is not sales or platform growth. It is evidence worth investigating, not a business rank or recommendation.

High apparent breadth in `Games, Books & Hobbies` (73.91%, n=23), `Muslim Fashion` (68.42%, n=19), and `Tickets & Vouchers` (66.67%, n=3) is accompanied by wide Wilson intervals and/or high concentration. Those values are not reliable comparative conclusions.

## 10. Outlier and sensitivity analysis

- Price findings reverse in magnitude when comparing mean, median, trimmed mean, and outlier-excluded mean; robust summaries are mandatory.
- Removing intervals with a favorite-outlier endpoint reduces valid favorite intervals from 3,489 to 3,006, but does not justify deleting those observations.
- Exact-only favorite results differ systematically from all-value results, confirming that compact rounding affects movement detection.
- Product-level and interval-level breadth differ because some products contribute multiple intervals.
- In sparse categories, the largest product accounts for 39.8%–96.7% of absolute favorite movement; small-category averages are particularly fragile.
- The median normalized favorite change is zero in 15 of 23 categories with valid intervals, so positive breadth must not be confused with a positive typical change.

## 11. Category-change analysis

The matched table contains 9 Level-2-changing intervals across 8 products and 20 full-path-changing intervals across 19 products. Excluding the 9 Level-2-changing intervals leaves 3,480 valid favorite intervals rather than 3,489. Positive favorite breadth is 43.53% for stable Level-2 intervals and 33.33% for changing intervals, but the changed group is far too small for comparative inference.

Category-changing products should remain preserved and be excluded or separately reported in any governed category movement calculation. They must not be silently reassigned.

## 12. Evidence quality

Every category engagement result in `phase_5_category_evidence.csv` includes its valid interval denominator, distinct-product count, Wilson bounds, compact interval count, and top-product concentration. Coverage columns include snapshots, unique products, repeated products, matched intervals, dates observed, and daily-volume variation.

No HIGH/MEDIUM/LOW tier was assigned because threshold governance belongs to Phase 6. Evidence quality is currently continuous and visible. Apparent category patterns are treated as exploratory when sample size is small, interval precision is wide, date coverage is incomplete, or product concentration is high.

## 13. Major findings

1. **Coverage variation can overwhelm naive trends.** Daily sample volume varies 18.54× and category evidence 54.76×; raw counts do not represent growth.
2. **Repeated histories are limited.** Only 18.48% of products repeat, and only 535 have three or more observations.
3. **Favorites change for a minority of valid intervals.** Positive breadth is 43.51%; 54.20% are unchanged and the overall median daily change is zero.
4. **Rounded displays materially affect favorite movement.** One quarter of valid snapshot values are compact, and exact-only breadth can differ substantially.
5. **Ratings are nearly static.** 97.54% of valid matched rating intervals are unchanged.
6. **Price distributions require robust statistics.** Means are often dominated by extreme right tails; prices describe listings, not revenue.
7. **Only a subset has a comparatively strong evidence base.** Five categories satisfy the transparent full-coverage/precision/product-count follow-up screen, but this does not establish traction or priority.

## 14. Important non-findings

- No verified sales momentum, category sales growth, revenue, orders, AOV, customers, conversion, campaign effect, margin, or platform-wide category share was found or calculated.
- No evidence supports treating `total_sold` or `total_rating` as sales.
- No category has been established as a platform growth leader.
- No causal relationship between discount, price, and engagement has been established.
- No final traction definition, KPI, reliability tier, category rank, momentum score, or campaign recommendation was created.
- The 20-day window and sparse histories do not broadly support sustained momentum or acceleration.

## 15. Big Question feasibility assessment

| Component | Assessment | Reason |
|---|---|---|
| A. Verified sales momentum | Not supported | No independently verified unit/sales measure. |
| B. Category business growth | Not supported | Coverage changes sharply; engagement fields are proxies. |
| C. Platform-wide category growth | Not supported | Uneven scraped sample, not a platform census. |
| D. Categories with observed traction | Partially supportable for exploration | Matched favorite/rating and listing-price observations can be reported as separate dimensions with evidence counts. |
| E. Campaign priorities | Not supported | No campaign exposure, conversion, revenue, margin, inventory, or causal evidence. |
| F. Original Big Question overall | Not defensibly answerable | Its performance, platform-inference, and decision requirements are unmet. |

Proposed question: “Which product categories show the strongest observed traction among repeatedly tracked Shopee listings in this sampled dataset?”

Assessment: **conditionally supportable, requires approval**. The data can describe sampled scale, favorite movement, breadth, coverage, and sensitivity separately. Phase 6 must approve the wording and methodology. This proposal has not replaced the original question.

To answer the original question properly, obtain verified longitudinal transactions or cumulative unit sales; order and realized-revenue records; a known platform sampling frame; longer category history covering seasonality; product/category history; and campaign exposure, impressions, clicks, conversion, inventory, margin, refunds, and experimental/control evidence.

## 16. Candidate analytical directions for Phase 6

These are governance candidates, not final KPIs:

- Sample evidence measures: dates observed, repeated products, valid intervals, distinct contributing products, interval span, and Wilson precision.
- Observed scale: distinct sampled products within a comparable cohort, clearly labeled as sample representation.
- Engagement breadth: products or intervals with positive favorite movement divided by an approved valid comparator denominator.
- Typical engagement movement: median per-product favorite change per elapsed day, explicitly approximate.
- Concentration: largest product's share of absolute movement or another approved influence diagnostic.
- Stability requirements: exact-display sensitivity, category-stable cohort, outlier-endpoint sensitivity, and interval-versus-product weighting.
- Multidimensional scorecard: scale, engagement movement, breadth, coverage, and evidence reliability shown separately; no weighted score without explicit governance.

Phase 6 must also decide whether favorite movement is an acceptable proxy at all. If not, the portfolio should present a data-limitations/measurement case rather than a category-priority analysis.

## 17. Limitations

- Twenty-day observational window; no seasonal or long-run perspective.
- Uneven and undocumented scraper sampling frame.
- 81.52% of products appear once; most repeated products appear only twice.
- Irregular intervals from 1 to 19 days.
- Favorites are displayed engagement, not demand or sales, and 24.62% are rounded.
- Average rating is nearly invariant over this period.
- Displayed prices have unverified currency and extreme right tails.
- Category changes are rare but require governed handling.
- No transactions, customers, revenue, orders, conversion, campaigns, inventory, margin, refunds, or causal design.
- `total_sold` and `total_rating` remain unverified and unusable for sales analysis.

## 18. Reproducibility results

- Reusable code: `src/analysis/eda_utils.py` and `src/analysis/run_phase_5_eda.py`.
- Independent gate: `tests/data_validation/validate_phase_5_eda.py`.
- Validation result: 44 checks passed, 0 failed.
- Reproducibility: 23 generated artifacts compared; 0 SHA-256 differences after rerun.
- Six Phase 4 input-table hashes match the Phase 4 manifest.
- Phase 4 transformation manifest SHA-256 remains `108c829c2e7f0d34334749421a1a30be516aa04a3de9cabe3409816b87789ac2`.
- Phase 2 cleaned dataset SHA-256 remains `407c6f5e654283461c8eba20a3a1721f5105650212e92ae99206ea6dbadd199d`.
- A standard hash read encountered an external file lock, but a read-only shared-file handle successfully verified the original raw CSV SHA-256 as `afed3932287c81df7eefcd7397b723cc2e2ca71d73690dc661ad250c7c78bc69`. Phase 5 reads only Phase 4 tables and made no raw or processed-data writes.

Run:

```powershell
C:\Python314\python.exe src\analysis\run_phase_5_eda.py
C:\Python314\python.exe tests\data_validation\validate_phase_5_eda.py
```

Phase 5 stops here. Phase 6 remains `NOT STARTED` pending review and explicit approval.
