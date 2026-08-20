# Broad Product Category Governance and Analysis Contract

## Purpose and status

`broad_product_category` is a project-defined analytical grouping introduced to make the executive dashboard easier to scan. It is not asserted to be an official Shopee taxonomy. The source-derived `category_level_2` remains unchanged and remains the detailed category and drill-down field.

The governed hierarchy is:

`broad_product_category` → `category_level_2`

Every observed Level-2 value must map to exactly one broad group. New or unmapped Level-2 values are a hard validation failure; they are never silently assigned to `Others`.

## Analysis contract for the controlled revision

- Question: how do the five approved favorite-engagement KPIs compare at a readable dashboard-level category grain?
- Unit of analysis: product within Broad Product Category after the existing product-level aggregation rules.
- Primary population: repeatedly observed products whose Level-2 category is stable, with positive elapsed intervals and exact favorite displays.
- Denominators: recomputed directly from eligible observations within each broad group; old Level-2 KPI values must not be summed or averaged.
- Primary metrics: the existing five Phase 6 KPIs, unchanged.
- Sensitivities: compact-inclusive, outlier-excluded, and interval-weighted, kept separate from the exact-display primary result.
- Comparison: broad groups within the fixed 20-day sampled window, with Wilson intervals and evidence sufficiency shown separately.
- Exclusions: the existing conservative exclusion of any product that changes Level 2 remains authoritative, even if both Level-2 values map to the same broad group.
- Unsupported claims: sales, revenue, orders, conversion, platform growth, campaign effectiveness, and a composite momentum score remain prohibited.
- Falsification/weakening conditions: an unmapped Level-2 value, changed row count, altered protected hash, incorrect denominator, sensitivity reversal, or inadequate evidence prevents publication.

## Mapping version 1.0.0

| Broad Product Category | Included Category Level 2 values |
|---|---|
| Automotive | Automotive |
| Baby & Kids | Baby & Toys |
| Entertainment & Hobbies | Games, Books & Hobbies |
| Fashion | Fashion Accessories; Men Clothes; Men Shoes; Men's Bags & Wallets; Muslim Fashion; Watches; Women Clothes; Women Shoes; Women's Bags |
| Groceries & Pets | Groceries & Pets |
| Health & Beauty | Health & Beauty |
| Home | Home & Living; Home Appliances |
| Mobile & Technology | Cameras & Drones; Computer & Accessories; Gaming & Consoles; Mobile & Accessories |
| Others | Others |
| Sports & Outdoor | Sports & Outdoor |
| Tickets & Vouchers | Tickets & Vouchers |
| Travel | Travel & Luggage |

`Gaming & Consoles` is grouped with technology because its source category centers on device hardware and its ecosystem; the mixed `Games, Books & Hobbies` category remains under entertainment. `Watches`, which was present in validated data but omitted from the request's example list, is grouped with Fashion as a wearable accessory. `Groceries & Pets` cannot be separated because the source already combines those domains.

## Stability governance

Level-2 stability and broad-category stability are recorded separately. A move between two Level-2 categories in the same broad group is broad-stable but Level-2-unstable. Such a product remains excluded from governed movement analysis because the approved conservative rule is based on Level-2 stability. The broad stability flag is diagnostic only and does not weaken that rule.

## Reproducibility and limitations

The executable mapping lives in `src/data/broad_product_category.py`; `outputs/tables/broad_product_category_mapping.csv` is generated from it. The grouping improves readability but can conceal variation among Level-2 categories, so Level 2 remains available for detail and drill-down. The taxonomy reflects semantic judgment applied to this observed dataset and must be reviewed if new Level-2 values appear.
