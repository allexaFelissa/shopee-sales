"""Render deterministic previews of the three Power BI Phase 9 pages.

The previews verify information hierarchy and text density. They do not replace
native Power BI rendering or interactive QA.
"""

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/figures"
SCORE = pd.read_csv(ROOT / "outputs/tables/phase_7_category_comparison.csv")
SENS = pd.read_csv(ROOT / "outputs/tables/phase_7_sensitivity_analysis.csv")

NAVY, ORANGE, BLUE_GRAY, TEAL, ROSE = "#0C1F39", "#F96722", "#6E8BA6", "#2D7A70", "#C55A6A"
PAGE, WHITE, BORDER, MUTED, INK = "#F5F7FA", "#FFFFFF", "#DDE3EA", "#687586", "#172535"
TIER = {"HIGH": NAVY, "MODERATE": BLUE_GRAY, "INSUFFICIENT": ROSE}


def frame(title: str, subtitle: str, methodology: str) -> plt.Figure:
    figure = plt.figure(figsize=(16, 9), facecolor=PAGE)
    figure.text(.035, .955, title, fontsize=23, weight="bold", color=NAVY, va="top")
    figure.text(.035, .913, subtitle, fontsize=11, color=MUTED, va="top")
    figure.text(.035, .885, methodology, fontsize=9.5, color=ORANGE, va="top", weight="bold")
    return figure


def card(figure: plt.Figure, left: float, bottom: float, width: float, height: float,
         value: str, label: str, value_color: str = NAVY) -> None:
    axes = figure.add_axes([left, bottom, width, height], facecolor=WHITE)
    for spine in axes.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(.9)
    axes.set_xticks([]); axes.set_yticks([])
    axes.text(.06, .63, value, color=value_color, fontsize=19, weight="bold", transform=axes.transAxes)
    axes.text(.06, .24, label, color=MUTED, fontsize=8.5, transform=axes.transAxes)


def footer(figure: plt.Figure, text: str) -> None:
    figure.text(.035, .025, text, fontsize=8.5, color=MUTED)


def overview() -> None:
    figure = frame(
        "Category Engagement Overview",
        "How do observed favorite-engagement movement patterns differ across broad categories?",
        "Observed favorite-display engagement | Sales metrics excluded | Fixed sampled observation window",
    )
    sufficient = SCORE.query("evidence_sufficiency_tier != 'INSUFFICIENT'")
    card(figure, .035, .705, .21, .105, f"{len(sufficient)} / {len(SCORE)}", "Evidence-sufficient categories")
    card(figure, .262, .705, .21, .105, f"{sufficient.positive_favorite_movement_breadth.max():.1f}%", "Maximum observed breadth", ORANGE)
    card(figure, .489, .705, .21, .105, f"{sufficient.median_daily_favorite_movement_per_product.max():.3f}", "Maximum typical movement", ORANGE)
    card(figure, .716, .705, .245, .105, f"{int(SCORE.eligible_favorite_movement_product_count.sum()):,}", "Eligible / tracked products")

    scatter = figure.add_axes([.05, .16, .49, .47], facecolor=WHITE)
    for tier, group in sufficient.groupby("evidence_sufficiency_tier"):
        scatter.scatter(group.positive_favorite_movement_breadth, group.median_daily_favorite_movement_per_product, s=35 + group.eligible_favorite_movement_product_count * .65, color=TIER[tier], alpha=.84, edgecolor=WHITE, linewidth=1.3, label=tier)
    label_offsets = {"Fashion": (5, 10), "Mobile & Technology": (5, -9), "Automotive": (7, 4), "Sports & Outdoor": (5, 12)}
    for _, row in sufficient.iterrows():
        scatter.annotate(row.broad_product_category, (row.positive_favorite_movement_breadth, row.median_daily_favorite_movement_per_product), xytext=label_offsets.get(row.broad_product_category, (4, 5)), textcoords="offset points", fontsize=6.8, color=INK)
    scatter.axvline(50, color=BORDER, lw=.8, ls="--"); scatter.axhline(0, color=BORDER, lw=.8)
    scatter.grid(alpha=.12); scatter.legend(frameon=False, fontsize=7, title="Evidence tier", title_fontsize=7)
    scatter.set_title("Category Engagement Movement", loc="left", color=NAVY, weight="bold", fontsize=12)
    scatter.set_xlabel("Positive Favorite-Movement Breadth (%)", fontsize=8)
    scatter.set_ylabel("Median Daily Favorite Movement per Product", fontsize=8)
    figure.text(.06, .175, "Farther right and higher = more positive observed movement | Bubble size = eligible products", fontsize=7.5, color=MUTED)

    for bottom, column, title, xlabel in [(.43, "positive_favorite_movement_breadth", "Positive Favorite-Movement Breadth", "Breadth (%)"), (.12, "median_daily_favorite_movement_per_product", "Median Daily Favorite Movement", "Favorites / day")]:
        axes = figure.add_axes([.62, bottom, .33, .20], facecolor=WHITE)
        ordered = sufficient.sort_values(column)
        axes.barh(ordered.broad_product_category, ordered[column], color=[TIER[tier] for tier in ordered.evidence_sufficiency_tier])
        axes.set_title(title, loc="left", color=NAVY, weight="bold", fontsize=11)
        axes.set_xlabel(xlabel, fontsize=7); axes.tick_params(axis="y", labelsize=6.5); axes.grid(axis="x", alpha=.12)
        for spine in axes.spines.values(): spine.set_color(BORDER)
    footer(figure, "Observed favorite engagement is not sales performance.")
    figure.savefig(OUT / "phase_9_page_1_category_engagement_overview_preview.png", dpi=160, bbox_inches="tight", facecolor=PAGE)
    plt.close(figure)


def deep_dive(category: str = "Health & Beauty") -> None:
    row = SCORE.loc[SCORE.broad_product_category.eq(category)].iloc[0]
    figure = frame("Category Evidence Deep Dive", "Inspect the strength, coverage, and stability of the selected category's engagement signal.", "Selected Category: Health & Beauty | Primary result: exact favorite display | Sensitivity views test measurement stability")
    values = [(f"{row.positive_favorite_movement_breadth:.1f}%", "Positive-movement breadth", ORANGE), (f"{row.median_daily_favorite_movement_per_product:.3f}", "Median daily favorite movement", ORANGE), (f"{int(row.eligible_favorite_movement_product_count):,}", "Eligible product count", NAVY), (f"{int(row.positive_product_count):,}", "Positive-movement products", NAVY), (row.evidence_sufficiency_tier, "Evidence sufficiency tier", TIER[row.evidence_sufficiency_tier])]
    for index, (value, label, color) in enumerate(values):
        card(figure, .035 + index * .187, .705, .17, .105, value, label, color)

    coverage = figure.add_axes([.05, .38, .38, .23], facecolor=WHITE)
    coverage.barh(["Eligible products", "Positive products", "Relevant intervals"], [row.eligible_favorite_movement_product_count, row.positive_product_count, row.eligible_exact_interval_count], color=[NAVY, ORANGE, BLUE_GRAY])
    coverage.set_title("Evidence Coverage", loc="left", color=NAVY, weight="bold", fontsize=11)
    coverage.tick_params(axis="y", labelsize=8); coverage.grid(axis="x", alpha=.12)

    bounds = figure.add_axes([.47, .42, .48, .19], facecolor=WHITE); bounds.set_xlim(0, 100); bounds.set_ylim(0, 1); bounds.axis("off")
    lower, estimate, upper = row.positive_breadth_wilson_95_lower_percent, row.positive_favorite_movement_breadth, row.positive_breadth_wilson_95_upper_percent
    bounds.hlines(.48, lower, upper, color=BLUE_GRAY, lw=5); bounds.vlines([lower, upper], .38, .58, color=BLUE_GRAY, lw=2); bounds.scatter(estimate, .48, s=100, color=ORANGE, zorder=3)
    bounds.text(0, .90, "Wilson Evidence Bounds", color=NAVY, weight="bold", fontsize=11)
    bounds.text(lower, .17, f"Lower {lower:.1f}%", ha="center", color=MUTED, fontsize=8)
    bounds.text(estimate, .75, f"Estimate {estimate:.1f}%", ha="center", color=NAVY, fontsize=8, weight="bold")
    bounds.text(upper, .17, f"Upper {upper:.1f}%", ha="center", color=MUTED, fontsize=8)
    card(figure, .47, .305, .22, .075, f"{int(row.observed_date_count)} observed", "Sampled dates")
    card(figure, .72, .305, .23, .075, f"{int(row.eligible_exact_interval_count):,}", "Relevant observation count")

    subset = SENS[SENS.broad_product_category.eq(category)].copy()
    order = ["PRIMARY_EXACT_PRODUCT", "COMPACT_INCLUSIVE_PRODUCT", "OUTLIER_EXCLUDED_PRODUCT", "INTERVAL_WEIGHTED_EXACT"]
    labels = ["Primary exact", "Compact-inclusive", "Outlier-excluded", "Interval-weighted"]
    subset = subset.set_index("sensitivity_scenario").loc[order].reset_index()
    axes = figure.add_axes([.05, .095, .90, .16], facecolor=WHITE)
    axes.barh(labels[::-1], subset.positive_favorite_movement_breadth.iloc[::-1], color=[TEAL, BLUE_GRAY, ORANGE, NAVY])
    axes.set_xlim(0, 100); axes.grid(axis="x", alpha=.12); axes.tick_params(axis="y", labelsize=8)
    axes.set_title("Sensitivity Scenario Comparison", loc="left", color=NAVY, weight="bold", fontsize=11)
    axes.set_xlabel("Positive favorite-movement breadth (%)", fontsize=7)
    footer(figure, "Sensitivity scenarios test stability; they do not replace the primary exact-display KPI. N/A indicates insufficient evidence, not zero.")
    figure.savefig(OUT / "phase_9_page_2_category_evidence_deep_dive_preview.png", dpi=160, bbox_inches="tight", facecolor=PAGE)
    plt.close(figure)


def evidence() -> None:
    figure = frame("Evidence & Limitations", "How strong is the evidence behind each category comparison?", "Evidence evaluates confidence in the signal - not performance.")
    tiers = SCORE.evidence_sufficiency_tier.value_counts().reindex(["HIGH", "MODERATE", "INSUFFICIENT"])
    axes = figure.add_axes([.05, .57, .28, .20], facecolor=WHITE)
    axes.barh(tiers.index[::-1], tiers.values[::-1], color=[TIER[tier] for tier in tiers.index[::-1]])
    axes.set_title("Categories by Evidence Tier", loc="left", color=NAVY, weight="bold", fontsize=11); axes.grid(axis="x", alpha=.12); axes.tick_params(axis="y", labelsize=8)
    stable = SCORE.sensitivity_status.map(lambda value: "Stable" if value in {"ROBUST", "DIRECTIONALLY_STABLE"} else "Unstable").value_counts().reindex(["Stable", "Unstable"], fill_value=0)
    axes = figure.add_axes([.36, .57, .28, .20], facecolor=WHITE)
    axes.barh(stable.index[::-1], stable.values[::-1], color=[ORANGE, TEAL])
    axes.set_title("Signal Stability", loc="left", color=NAVY, weight="bold", fontsize=11); axes.grid(axis="x", alpha=.12); axes.tick_params(axis="y", labelsize=8)
    ordered = SCORE.sort_values("eligible_favorite_movement_product_count")
    axes = figure.add_axes([.68, .42, .27, .35], facecolor=WHITE)
    axes.barh(ordered.broad_product_category, ordered.eligible_favorite_movement_product_count, color=[TIER[tier] for tier in ordered.evidence_sufficiency_tier])
    axes.set_title("Evidence Coverage by Category", loc="left", color=NAVY, weight="bold", fontsize=11); axes.grid(axis="x", alpha=.12); axes.tick_params(axis="y", labelsize=5.5)
    axes.set_xlabel("Eligible evidence/product count", fontsize=7)

    insufficient = SCORE.query("evidence_sufficiency_tier == 'INSUFFICIENT'").reset_index(drop=True)
    positions = [(.05, .33), (.27, .33), (.05, .20), (.27, .20)]
    for row, (left, bottom) in zip(insufficient.itertuples(), positions, strict=True):
        axes = figure.add_axes([left, bottom, .20, .10], facecolor="#FFF6F5")
        for spine in axes.spines.values(): spine.set_color(BORDER)
        axes.axis("off")
        axes.text(.05, .76, f"INSUFFICIENT | {row.broad_product_category}", fontsize=7.2, color=ROSE, weight="bold", transform=axes.transAxes)
        axes.text(.05, .10, textwrap.fill(row.business_interpretation, 45), fontsize=5.8, color=INK, va="bottom", transform=axes.transAxes)

    can_support = "What this analysis can support\n• Compare patterns across sufficiently\n  observed categories\n• Compare breadth and typical movement\n• Assess evidence and sensitivity"
    cannot_support = "What this analysis cannot support\n• Sales performance or growth claims\n• Causal campaign impact\n• Campaign prioritization or generalization\n  beyond the sampled window"
    for left, text, color in [(.50, can_support, WHITE), (.73, cannot_support, "#FFF9F4")]:
        axes = figure.add_axes([left, .17, .20, .18], facecolor=color)
        for spine in axes.spines.values(): spine.set_color(BORDER)
        axes.axis("off"); axes.text(.06, .90, text, fontsize=7, color=INK, va="top", linespacing=1.55, transform=axes.transAxes)
    footer(figure, "Four insufficient-evidence categories remain visible by design; movement KPIs are blank rather than zero.")
    figure.savefig(OUT / "phase_9_page_3_evidence_and_limitations_preview.png", dpi=160, bbox_inches="tight", facecolor=PAGE)
    plt.close(figure)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    overview(); deep_dive(); evidence()
    print("Rendered three Phase 9 design previews")
