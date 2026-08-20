"""Render deterministic Phase 9 design previews from governed Phase 7 facts.

These PNGs support layout/readability QA when Power BI Desktop is unavailable.
They are not substitutes for Desktop-rendered screenshots.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/figures"
SCORE = pd.read_csv(ROOT / "outputs/tables/phase_7_category_comparison.csv")
SENS = pd.read_csv(ROOT / "outputs/tables/phase_7_sensitivity_analysis.csv")
NAVY, BLUE, ORANGE, PURPLE, GRAY = "#16324F", "#3E6B89", "#D97706", "#6D5BD0", "#737B84"
TIER = {"HIGH": NAVY, "MODERATE": BLUE, "INSUFFICIENT": "#AEB5BC"}


def frame(title, subtitle):
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(.035, .955, title, fontsize=23, weight="bold", color=NAVY, va="top")
    fig.text(.035, .905, subtitle, fontsize=11, color="#5C6773", va="top")
    fig.text(.965, .955, "20-day sample  |  Favorite engagement, not sales", fontsize=10,
             color=ORANGE, ha="right", va="top", weight="bold")
    return fig


def footer(fig, text):
    fig.text(.035, .025, text, fontsize=8.5, color="#5C6773")


def overview():
    fig = frame("Category Engagement Overview", "Breadth, typical movement, sampled scale, and evidence remain separate.")
    pub = SCORE[SCORE.evidence_sufficiency_tier != "INSUFFICIENT"].copy()
    ax = fig.add_axes([.055, .18, .59, .64])
    for tier, group in pub.groupby("evidence_sufficiency_tier"):
        ax.scatter(group.positive_favorite_movement_breadth,
                   group.median_daily_favorite_movement_per_product,
                   s=35 + group.eligible_favorite_movement_product_count * .75,
                   c=TIER[tier], alpha=.78, edgecolor="white", linewidth=1.2, label=f"{tier} evidence")
    for cat in ["Groceries & Pets", "Health & Beauty", "Women's Bags", "Men Clothes"]:
        row = pub[pub.broad_product_category == cat].iloc[0]
        ax.annotate(cat, (row.positive_favorite_movement_breadth, row.median_daily_favorite_movement_per_product),
                    xytext=(5, 6), textcoords="offset points", fontsize=8.5, color="#17202A")
    ax.axvline(50, color="#C8CDD2", lw=1, ls="--")
    ax.axhline(0, color="#C8CDD2", lw=1)
    ax.set_xlabel("Positive Favorite-Movement Breadth (%)")
    ax.set_ylabel("Median Daily Favorite Movement per Product (favorites/day)")
    ax.set_title("Breadth vs typical displayed-favorite movement", loc="left", color=NAVY, weight="bold")
    ax.grid(alpha=.16)
    ax.legend(frameon=False, loc="upper left")
    ax2 = fig.add_axes([.69, .57, .27, .25])
    counts = SCORE.evidence_sufficiency_tier.value_counts().reindex(["HIGH", "MODERATE", "INSUFFICIENT"])
    ax2.barh(counts.index[::-1], counts.values[::-1], color=[TIER[x] for x in counts.index[::-1]])
    ax2.set_title("Evidence availability — not performance", loc="left", fontsize=11, weight="bold", color=NAVY)
    ax2.spines[:].set_visible(False); ax2.tick_params(axis="x", bottom=False, labelbottom=False)
    for y, v in enumerate(counts.values[::-1]): ax2.text(v + .2, y, str(v), va="center", fontsize=10)
    fig.text(.69, .50, f"{int(pub.eligible_favorite_movement_product_count.sum()):,}", fontsize=25, weight="bold", color=NAVY)
    fig.text(.69, .465, "eligible tracked products in published categories", fontsize=9, color="#5C6773")
    fig.text(.84, .50, "14 / 24", fontsize=25, weight="bold", color=NAVY)
    fig.text(.84, .465, "categories with published movement", fontsize=9, color="#5C6773")
    note = ("READ WITH CONTEXT\n\nGroceries & Pets: strongest HIGH-evidence primary pattern; directionally stable.\n\n"
            "Health & Beauty: strongest robust positive pattern; MODERATE evidence.\n\n"
            "Women's Bags: largest published median; n=46 across 17 dates.\n\nTop-right is not a campaign-priority map.")
    fig.text(.69, .405, note, fontsize=10, va="top", color="#17202A",
             bbox=dict(boxstyle="round,pad=.8", facecolor="#F5F7F9", edgecolor="#D9E0E6"))
    footer(fig, "Source: governed Phase 7 outputs, fixed 2023-04-24 to 2023-05-13. Ten insufficient categories remain N/A and unranked.")
    fig.savefig(OUT / "phase_9_page_1_category_engagement_overview_preview.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def deep_dive(category="Health & Beauty"):
    fig = frame("Category Evidence Deep Dive", f"Illustrative selected category: {category}  |  PRIMARY is exact-display product analysis.")
    row = SCORE[SCORE.broad_product_category == category].iloc[0]
    labels = ["Positive Breadth", "Median Favorites / Day", "Eligible Tracked Products", "Evidence Tier"]
    vals = [f"{row.positive_favorite_movement_breadth:.1f}%", f"{row.median_daily_favorite_movement_per_product:.3f}",
            f"{int(row.eligible_favorite_movement_product_count):,}", row.evidence_sufficiency_tier]
    for j, (label, val) in enumerate(zip(labels, vals)):
        x = .055 + j*.225
        fig.text(x, .79, val, fontsize=22, weight="bold", color=NAVY)
        fig.text(x, .75, label, fontsize=9, color="#5C6773")
    ax = fig.add_axes([.055, .22, .57, .45])
    subset = SENS[SENS.broad_product_category == category].copy()
    order = ["PRIMARY_EXACT_PRODUCT", "COMPACT_INCLUSIVE_PRODUCT", "OUTLIER_EXCLUDED_PRODUCT", "INTERVAL_WEIGHTED_EXACT"]
    subset.sensitivity_scenario = pd.Categorical(subset.sensitivity_scenario, order, ordered=True)
    subset = subset.sort_values("sensitivity_scenario")
    names = ["PRIMARY — exact", "SENS — compact", "SENS — outlier", "SENS — interval"]
    colors = [NAVY, ORANGE, PURPLE, GRAY]
    ax.barh(names[::-1], subset.positive_favorite_movement_breadth.values[::-1], color=colors[::-1])
    ax.set_xlim(0, 100); ax.set_xlabel("Positive breadth (%)")
    ax.set_title("Primary breadth versus governed sensitivities", loc="left", weight="bold", color=NAVY)
    ax.grid(axis="x", alpha=.16)
    for y, v in enumerate(subset.positive_favorite_movement_breadth.values[::-1]): ax.text(v+1, y, f"{v:.1f}%", va="center")
    ax2 = fig.add_axes([.67, .24, .29, .42]); ax2.axis("off")
    context = (f"PRIMARY EVIDENCE CONTEXT\n\nObserved dates: {int(row.observed_date_count)} / 20\n"
               f"Wilson 95% interval: {row.positive_breadth_wilson_95_lower_percent:.1f}%–{row.positive_breadth_wilson_95_upper_percent:.1f}%\n"
               f"Wilson width: {row.positive_breadth_wilson_95_width_percentage_points:.1f} pp\n"
               f"Sensitivity status: {row.sensitivity_status}\n\n"
               "N/A — insufficient evidence is distinct from zero. Sensitivities do not replace the primary KPI.")
    ax2.text(0, 1, context, va="top", fontsize=11, color="#17202A",
             bbox=dict(boxstyle="round,pad=.9", facecolor="#F5F7F9", edgecolor="#D9E0E6"))
    footer(fig, "The production page uses a Broad Product Category selector; no date slicer is exposed because the KPI window is fixed.")
    fig.savefig(OUT / "phase_9_page_2_category_evidence_deep_dive_preview.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def evidence():
    fig = frame("Evidence & Limitations", "Evidence tier describes analytical support, not category performance.")
    ordered = SCORE.sort_values(["evidence_sufficiency_tier", "eligible_favorite_movement_product_count"], ascending=[True, True])
    ax = fig.add_axes([.055, .14, .50, .70])
    y = np.arange(len(ordered))
    ax.barh(y, ordered.eligible_favorite_movement_product_count, color=[TIER[x] for x in ordered.evidence_sufficiency_tier])
    ax.set_yticks(y, ordered.broad_product_category, fontsize=7.5)
    ax.set_xlabel("Eligible tracked products (evidence scale, not market size)")
    ax.set_title("Eligible evidence by Broad Product Category", loc="left", weight="bold", color=NAVY)
    ax.grid(axis="x", alpha=.15)
    ax2 = fig.add_axes([.60, .50, .36, .34]); ax2.axis("off")
    tiers = ("EVIDENCE GATES\n\nHIGH — 20 dates, n≥100, Wilson width≤20pp\n"
             "MODERATE — ≥15 dates, n≥30, width≤35pp\n"
             "INSUFFICIENT — any moderate gate fails\n\n"
             "Counts: 4 HIGH  •  10 MODERATE  •  10 INSUFFICIENT")
    ax2.text(0, 1, tiers, va="top", fontsize=11, bbox=dict(boxstyle="round,pad=.8", facecolor="#F5F7F9", edgecolor="#D9E0E6"))
    ax3 = fig.add_axes([.60, .13, .36, .31]); ax3.axis("off")
    limits = ("LIMITATIONS\n\nSampled listing snapshots over 20 days; only a minority of products repeat; daily sampling is uneven; favorites can be compact/rounded.\n\n"
              "DOES NOT ESTABLISH\nSales/revenue/orders • conversion • customer demand • platform growth/market share • campaign effectiveness • future performance")
    ax3.text(0, 1, limits, va="top", fontsize=10.5, color="#17202A",
             bbox=dict(boxstyle="round,pad=.8", facecolor="#FFF8EB", edgecolor="#E8C98C"))
    footer(fig, "Exact-display results are primary. Compact-inclusive, outlier-excluded, and interval-weighted results are sensitivity analyses.")
    fig.savefig(OUT / "phase_9_page_3_evidence_and_limitations_preview.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    overview(); deep_dive(); evidence()
    print("Rendered three Phase 9 design previews")
