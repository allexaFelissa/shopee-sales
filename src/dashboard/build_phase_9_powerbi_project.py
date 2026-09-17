"""Build the Phase 9 Power BI Project (PBIP) from governed Phase 7 tables.

The generated PBIR report is deliberately source-controlled and deterministic.
It does not recompute any governed KPI from upstream listing data.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "dashboard"
NAME = "Shopee_Category_Engagement"
REPORT = DASHBOARD / f"{NAME}.Report"
MODEL = DASHBOARD / f"{NAME}.SemanticModel"
DEFINITION = REPORT / "definition"
PAGES = DEFINITION / "pages"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"

SCORECARD_SOURCE = ROOT / "outputs/tables/phase_7_category_comparison.csv"
SENSITIVITY_SOURCE = ROOT / "outputs/tables/phase_7_sensitivity_analysis.csv"
FINDINGS_SOURCE = ROOT / "outputs/tables/phase_7_business_findings.csv"

PAGE_IDS = {
    "overview": "ReportSection0a1b2c3d4e5f60718293a4b5",
    "deep_dive": "ReportSection1b2c3d4e5f60718293a4b5c6",
    "evidence": "ReportSection2c3d4e5f60718293a4b5c6d7",
}

COLORS = {
    "navy": "#0C1F39",
    "orange": "#F96722",
    "blue_gray": "#6E8BA6",
    "teal": "#2D7A70",
    "rose": "#C55A6A",
    "page": "#F5F7FA",
    "border": "#DDE3EA",
    "ink": "#172535",
    "muted": "#687586",
    "white": "#FFFFFF",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def literal(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def column(table: str, name: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def measure(table: str, name: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def projection(field: dict, query_ref: str, label: str | None = None) -> dict:
    return {"field": field, "queryRef": query_ref, "nativeQueryRef": label or query_ref.split(".")[-1]}


def visual_id(page_key: str, ordinal: int) -> str:
    return hashlib.sha1(f"phase9:{page_key}:{ordinal}".encode()).hexdigest()[:20]


def position(x: int, y: int, width: int, height: int, order: int) -> dict:
    return {"x": x, "y": y, "z": order * 1000, "height": height, "width": width, "tabOrder": order}


def container_objects(title: str | None = None) -> dict:
    out = {
        "background": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#FFFFFF'")}}, "transparency": literal("0D")}}],
        "border": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal(f"'{COLORS['border']}'")}}, "radius": literal("10D")}}],
        "dropShadow": [{"properties": {"show": literal("false")}}],
    }
    if title:
        out["title"] = [{"properties": {"show": literal("true"), "text": literal(f"'{title}'"), "fontColor": {"solid": {"color": literal(f"'{COLORS['navy']}'")}}, "fontSize": literal("12D"), "bold": literal("true"), "alignment": literal("'left'")}}]
    return out


def textbox(page_key: str, ordinal: int, text: str, x: int, y: int, w: int, h: int,
            size: int = 14, color: str = COLORS["ink"], weight: str | None = None,
            card_style: bool = False, card_color: str = COLORS["white"]) -> dict:
    style = {"fontFamily": "Segoe UI", "fontSize": f"{size}px", "color": color}
    if weight:
        style["fontWeight"] = weight
    return {
        "$schema": f"{SCHEMA}/visualContainer/2.9.0/schema.json",
        "name": visual_id(page_key, ordinal),
        "position": position(x, y, w, h, ordinal),
        "visual": {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": text, "textStyle": style}], "horizontalTextAlignment": "left"}]}}]},
            "visualContainerObjects": {
                "background": [{"properties": {
                    "show": literal("true" if card_style else "false"),
                    "color": {"solid": {"color": literal(f"'{card_color}'")}},
                }}],
                "border": [{"properties": {
                    "show": literal("true" if card_style else "false"),
                    "color": {"solid": {"color": literal(f"'{COLORS['border']}'")}},
                    "radius": literal("10D"),
                }}],
                "padding": [{"properties": {"top": literal("0D"), "bottom": literal("0D"), "left": literal("0D"), "right": literal("0D")}}],
            },
        },
    }


def data_visual(page_key: str, ordinal: int, visual_type: str, roles: dict, x: int, y: int,
                w: int, h: int, title: str | None = None, objects: dict | None = None,
                sort: dict | None = None) -> dict:
    visual = {
        "visualType": visual_type,
        "query": {"queryState": roles},
        "visualContainerObjects": container_objects(title),
    }
    if objects:
        visual["objects"] = objects
    if sort:
        visual["sortDefinition"] = sort
    return {
        "$schema": f"{SCHEMA}/visualContainer/2.9.0/schema.json",
        "name": visual_id(page_key, ordinal),
        "position": position(x, y, w, h, ordinal),
        "visual": visual,
    }


def slicer(page_key: str, ordinal: int, table: str, field_name: str, x: int, y: int, w: int, h: int,
           title: str, single_select: bool = False) -> dict:
    roles = {"Values": {"projections": [projection(column(table, field_name), f"{table}.{field_name}", field_name)]}}
    objects = {
        "data": [{"properties": {"mode": literal("'Dropdown'")}}],
        "selection": [{"properties": {
            "singleSelect": literal("true" if single_select else "false"),
            "selectAllCheckboxEnabled": literal("false" if single_select else "true"),
        }}],
    }
    return data_visual(page_key, ordinal, "slicer", roles, x, y, w, h, title, objects)


def card(page_key: str, ordinal: int, measure_name: str, x: int, y: int, w: int, h: int, title: str) -> dict:
    roles = {"Data": {"projections": [projection(measure("Category Scorecard", measure_name), f"Category Scorecard.{measure_name}", title)]}}
    return data_visual(page_key, ordinal, "cardVisual", roles, x, y, w, h, title)


def descending_sort(field: dict) -> dict:
    return {"sort": [{"field": field, "direction": "Descending"}]}


def chart_objects(fill: str | None = None, labels: bool = False) -> dict:
    objects: dict = {}
    if fill:
        objects["dataPoint"] = [{"properties": {"fill": {"solid": {"color": literal(f"'{fill}'")}}}}]
    if labels:
        objects["labels"] = [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal(f"'{COLORS['navy']}'")}}}}]
    return objects


def write_visual(page_key: str, visual: dict) -> str:
    page_id = PAGE_IDS[page_key]
    path = PAGES / page_id / "visuals" / visual["name"] / "visual.json"
    write_json(path, visual)
    return visual["name"]


def page_header(page_key: str, title: str, subtitle: str, methodology: str) -> int:
    write_visual(page_key, textbox(page_key, 1, title, 28, 18, 760, 42, 24, COLORS["navy"], "bold"))
    write_visual(page_key, textbox(page_key, 2, subtitle, 28, 56, 820, 26, 12, COLORS["muted"]))
    write_visual(page_key, textbox(page_key, 3, methodology, 28, 84, 800, 22, 10, COLORS["orange"], "bold"))
    return 4


def build_overview() -> None:
    key = "overview"
    i = page_header(key, "Category Engagement Overview", "How do observed favorite-engagement movement patterns differ across broad categories?", "Observed favorite-display engagement | Sales metrics excluded | Fixed sampled observation window")
    write_visual(key, slicer(key, i, "Category Scorecard", "Broad Product Category", 810, 22, 140, 78, "Broad Product Category")); i += 1
    write_visual(key, slicer(key, i, "Category Scorecard", "Evidence Sufficiency Tier", 960, 22, 135, 78, "Evidence Tier")); i += 1
    write_visual(key, slicer(key, i, "Category Scorecard", "Sensitivity Status", 1105, 22, 145, 78, "Sensitivity Status")); i += 1
    write_visual(key, card(key, i, "Evidence-Sufficient Category Count Display", 28, 126, 286, 92, "Evidence-Sufficient Categories")); i += 1
    write_visual(key, card(key, i, "Maximum Positive Favorite-Movement Breadth Display", 330, 126, 286, 92, "Maximum Observed Breadth")); i += 1
    write_visual(key, card(key, i, "Maximum Median Daily Favorite Movement Display", 632, 126, 286, 92, "Maximum Typical Movement")); i += 1
    write_visual(key, card(key, i, "Eligible Favorite-Movement Product Count", 934, 126, 316, 92, "Eligible / Tracked Products")); i += 1

    scatter_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category")]},
        "Series": {"projections": [projection(column("Category Scorecard", "Evidence Sufficiency Tier"), "Category Scorecard.Evidence Sufficiency Tier")]},
        "X": {"projections": [projection(measure("Category Scorecard", "Positive Favorite-Movement Breadth"), "Category Scorecard.Positive Favorite-Movement Breadth")]},
        "Y": {"projections": [projection(measure("Category Scorecard", "Median Daily Favorite Movement per Product"), "Category Scorecard.Median Daily Favorite Movement per Product")]},
        "Size": {"projections": [projection(measure("Category Scorecard", "Eligible Favorite-Movement Product Count"), "Category Scorecard.Eligible Favorite-Movement Product Count")]},
        "Tooltips": {"projections": [
            projection(measure("Category Scorecard", "Observed Dates"), "Category Scorecard.Observed Dates"),
            projection(measure("Category Scorecard", "Breadth Wilson 95% Width"), "Category Scorecard.Breadth Wilson 95% Width"),
        ]},
    }
    scatter_objects = {"categoryLabels": [{"properties": {"show": literal("true")}}]}
    write_visual(key, data_visual(key, i, "scatterChart", scatter_roles, 28, 238, 650, 405, "Category Engagement Movement", scatter_objects)); i += 1
    write_visual(key, textbox(key, i, "Farther right and higher = more positive observed movement | Bubble size = eligible products", 44, 612, 605, 20, 9, COLORS["muted"])); i += 1
    breadth_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category")]},
        "Y": {"projections": [projection(measure("Category Scorecard", "Positive Favorite-Movement Breadth"), "Category Scorecard.Positive Favorite-Movement Breadth")]},
        "Series": {"projections": [projection(column("Category Scorecard", "Evidence Sufficiency Tier"), "Category Scorecard.Evidence Sufficiency Tier")]},
    }
    write_visual(key, data_visual(key, i, "barChart", breadth_roles, 700, 238, 550, 195, "Positive Favorite-Movement Breadth", chart_objects(labels=True), descending_sort(measure("Category Scorecard", "Positive Favorite-Movement Breadth")))); i += 1
    movement_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category")]},
        "Y": {"projections": [projection(measure("Category Scorecard", "Median Daily Favorite Movement per Product"), "Category Scorecard.Median Daily Favorite Movement per Product")]},
        "Series": {"projections": [projection(column("Category Scorecard", "Evidence Sufficiency Tier"), "Category Scorecard.Evidence Sufficiency Tier")]},
    }
    write_visual(key, data_visual(key, i, "barChart", movement_roles, 700, 448, 550, 195, "Median Daily Favorite Movement", chart_objects(labels=True), descending_sort(measure("Category Scorecard", "Median Daily Favorite Movement per Product")))); i += 1
    write_visual(key, textbox(key, i, "Observed favorite engagement is not sales performance.", 28, 676, 740, 18, 10, COLORS["muted"]))


def build_deep_dive() -> None:
    key = "deep_dive"
    i = page_header(key, "Category Evidence Deep Dive", "Inspect the strength, coverage, and stability of the selected category's engagement signal.", "Primary result: exact favorite display | Sensitivity views test measurement stability")
    write_visual(key, slicer(key, i, "Category Scorecard", "Broad Product Category", 890, 22, 360, 78,
                             "Selected Category", single_select=True)); i += 1
    write_visual(key, card(key, i, "Positive Favorite-Movement Breadth Display", 28, 128, 230, 92, "Positive-Movement Breadth")); i += 1
    write_visual(key, card(key, i, "Median Daily Favorite Movement Display", 274, 128, 230, 92, "Median Daily Favorite Movement")); i += 1
    write_visual(key, card(key, i, "Eligible Favorite-Movement Product Count Display", 520, 128, 230, 92, "Eligible Product Count")); i += 1
    write_visual(key, card(key, i, "Positive Favorite-Movement Product Count", 766, 128, 230, 92, "Positive-Movement Products")); i += 1
    write_visual(key, card(key, i, "Evidence Sufficiency Tier Display", 1012, 128, 238, 92, "Evidence Sufficiency Tier")); i += 1

    coverage_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category")]},
        "Y": {"projections": [
            projection(measure("Category Scorecard", "Eligible Favorite-Movement Product Count"), "Category Scorecard.Eligible Favorite-Movement Product Count"),
            projection(measure("Category Scorecard", "Positive Favorite-Movement Product Count"), "Category Scorecard.Positive Favorite-Movement Product Count"),
            projection(measure("Category Scorecard", "Eligible Exact Interval Observation Count"), "Category Scorecard.Eligible Exact Interval Observation Count"),
        ]},
    }
    write_visual(key, data_visual(key, i, "barChart", coverage_roles, 28, 250, 510, 225, "Evidence Coverage", chart_objects(labels=True))); i += 1

    table_roles = {"Values": {"projections": [
        projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category"),
        projection(measure("Category Scorecard", "Observed Dates"), "Category Scorecard.Observed Dates"),
        projection(measure("Category Scorecard", "Breadth Wilson 95% Lower"), "Category Scorecard.Breadth Wilson 95% Lower"),
        projection(measure("Category Scorecard", "Breadth Wilson 95% Upper"), "Category Scorecard.Breadth Wilson 95% Upper"),
        projection(measure("Category Scorecard", "Breadth Wilson 95% Width"), "Category Scorecard.Breadth Wilson 95% Width"),
        projection(column("Category Scorecard", "Sensitivity Status"), "Category Scorecard.Sensitivity Status"),
    ]}}
    write_visual(key, data_visual(key, i, "tableEx", table_roles, 560, 250, 690, 145, "Wilson Evidence Bounds")); i += 1
    write_visual(key, card(key, i, "Observed Dates Display", 560, 413, 330, 78, "Sampled Dates Observed")); i += 1
    write_visual(key, card(key, i, "Eligible Exact Interval Observation Count", 908, 413, 342, 78, "Relevant Observation Count")); i += 1

    sensitivity_roles = {
        "Category": {"projections": [projection(column("Sensitivity", "Scenario Display"), "Sensitivity.Scenario Display")]},
        "Series": {"projections": [projection(column("Sensitivity", "Scenario Type"), "Sensitivity.Scenario Type")]},
        "Y": {"projections": [projection(measure("Sensitivity", "Scenario Positive Breadth"), "Sensitivity.Scenario Positive Breadth")]},
        "Tooltips": {"projections": [projection(measure("Sensitivity", "Difference from Primary"), "Sensitivity.Difference from Primary")]},
    }
    write_visual(key, data_visual(key, i, "barChart", sensitivity_roles, 28, 510, 1222, 145, "Sensitivity Scenario Comparison", chart_objects(labels=True))); i += 1
    write_visual(key, textbox(key, i, "N/A - insufficient evidence is distinct from zero. Sensitivity scenarios test stability; they do not replace the primary exact-display KPI.", 28, 676, 1090, 18, 10, COLORS["muted"]))


def build_evidence() -> None:
    key = "evidence"
    i = page_header(key, "Evidence & Limitations", "How strong is the evidence behind each category comparison?", "Evidence evaluates confidence in the signal - not performance.")
    write_visual(key, slicer(key, i, "Category Scorecard", "Evidence Sufficiency Tier", 960, 22, 135, 78, "Evidence Tier")); i += 1
    write_visual(key, slicer(key, i, "Category Scorecard", "Sensitivity Status", 1105, 22, 145, 78, "Sensitivity Status")); i += 1

    tier_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Evidence Sufficiency Tier"), "Category Scorecard.Evidence Sufficiency Tier")]},
        "Y": {"projections": [projection(measure("Category Scorecard", "Broad Product Category Count"), "Category Scorecard.Broad Product Category Count")]},
    }
    write_visual(key, data_visual(key, i, "barChart", tier_roles, 28, 128, 370, 195, "Categories by Evidence Tier", chart_objects(labels=True))); i += 1
    stability_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Sensitivity Status"), "Category Scorecard.Sensitivity Status")]},
        "Y": {"projections": [projection(measure("Category Scorecard", "Broad Product Category Count"), "Category Scorecard.Broad Product Category Count")]},
    }
    write_visual(key, data_visual(key, i, "barChart", stability_roles, 418, 128, 370, 195, "Signal Stability", chart_objects(COLORS["teal"], labels=True))); i += 1

    product_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category")]},
        "Series": {"projections": [projection(column("Category Scorecard", "Evidence Sufficiency Tier"), "Category Scorecard.Evidence Sufficiency Tier")]},
        "Y": {"projections": [projection(measure("Category Scorecard", "Eligible Favorite-Movement Product Count"), "Category Scorecard.Eligible Favorite-Movement Product Count")]},
        "Tooltips": {"projections": [projection(measure("Category Scorecard", "Observed Dates"), "Category Scorecard.Observed Dates")]},
    }
    write_visual(key, data_visual(key, i, "barChart", product_roles, 808, 128, 442, 215, "Evidence Coverage by Category", chart_objects(labels=True), descending_sort(measure("Category Scorecard", "Eligible Favorite-Movement Product Count")))); i += 1

    insufficient = csv.DictReader(SCORECARD_SOURCE.open(encoding="utf-8"))
    insufficient_rows = [row for row in insufficient if row["evidence_sufficiency_tier"] == "INSUFFICIENT"]
    positions = [(28, 352), (337, 352), (28, 447), (337, 447)]
    for row, (x, y) in zip(insufficient_rows, positions, strict=True):
        write_visual(key, textbox(key, i, f"INSUFFICIENT | {row['broad_product_category']}\n{row['business_interpretation']}", x, y, 292, 80, 9, COLORS["ink"], None, True, "#FFF6F5")); i += 1
    can_support = ("What this analysis can support\n"
                   "• Compare patterns across sufficiently observed categories\n"
                   "• Identify stronger or broader engagement signals\n"
                   "• Assess evidence strength and sensitivity")
    cannot_support = ("What this analysis cannot support\n"
                      "• Sales performance or growth claims\n"
                      "• Causal campaign impact\n"
                      "• Campaign prioritization or generalization beyond the sampled window")
    write_visual(key, textbox(key, i, can_support, 658, 365, 282, 162, 10, COLORS["ink"], None, True)); i += 1
    write_visual(key, textbox(key, i, cannot_support, 958, 365, 292, 162, 10, COLORS["ink"], None, True, "#FFF9F4")); i += 1
    write_visual(key, textbox(key, i, "Four insufficient-evidence categories remain visible by design; movement KPIs are blank rather than zero.", 658, 548, 590, 20, 10, COLORS["muted"]))


def m_csv(path: Path, columns: list[tuple[str, str]]) -> list[str]:
    """Embed the small governed publication fact as portable Base64 CSV.

    PBIP exposes no stable project-directory variable for File.Contents. The
    deterministic generator therefore embeds the 12-row and 48-row publication
    facts while keeping every governed calculation upstream in Python.
    """
    source = base64.b64encode(path.read_bytes()).decode("ascii")
    types = ", ".join(f'{{"{name}", {kind}}}' for name, kind in columns)
    return [
        "let",
        f'    Source = Csv.Document(Binary.FromText("{source}", BinaryEncoding.Base64), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
        f"    Types = Table.TransformColumnTypes(Headers, {{{types}}})",
        "in",
        "    Types",
    ]


def model_column(name: str, data_type: str, source: str | None = None, hidden: bool = False) -> dict:
    result = {"name": name, "dataType": data_type, "sourceColumn": source or name}
    if hidden:
        result["isHidden"] = True
    return result


def calculated_column(name: str, data_type: str, expression: str) -> dict:
    """Return a TMSL calculated column, explicitly discriminated from source columns."""
    return {"type": "calculated", "name": name, "dataType": data_type, "expression": expression}


def model_measure(name: str, expression: str, fmt: str | None = None) -> dict:
    result = {"name": name, "expression": expression}
    if fmt:
        result["formatString"] = fmt
    return result


def build_model() -> None:
    score_cols = [
        ("Broad Product Category", "string", "broad_product_category"),
        ("Observed Stable-Category Product Count Value", "int64", "observed_stable_category_product_count"),
        ("Stable Repeated Product Count", "int64", "stable_repeated_product_count"),
        ("Observed Date Count", "int64", "observed_date_count"),
        ("Eligible Exact Interval Count", "int64", "eligible_exact_interval_count"),
        ("Eligible Favorite-Movement Product Count Value", "int64", "eligible_favorite_movement_product_count"),
        ("Positive Product Count", "int64", "positive_product_count"),
        ("Zero Product Count", "int64", "zero_product_count"),
        ("Negative Product Count", "int64", "negative_product_count"),
        ("Breadth Wilson 95% Lower Value", "double", "positive_breadth_wilson_95_lower_percent"),
        ("Breadth Wilson 95% Upper Value", "double", "positive_breadth_wilson_95_upper_percent"),
        ("Breadth Wilson 95% Width Value", "double", "positive_breadth_wilson_95_width_percentage_points"),
        ("Evidence Sufficiency Tier", "string", "evidence_sufficiency_tier"),
        ("Eligible Share of Observed Stable Products", "double", "eligible_product_share_of_observed_stable_products_percent"),
        ("Sensitivity Status", "string", "sensitivity_status"),
        ("Positive Favorite-Movement Breadth Value", "double", "positive_favorite_movement_breadth"),
        ("Median Daily Favorite Movement Value", "double", "median_daily_favorite_movement_per_product"),
        ("Further Investigation Candidate", "boolean", "further_investigation_candidate_flag"),
        ("Analysis Classification", "string", "analysis_classification"),
        ("Breadth-Magnitude Pattern", "string", "breadth_magnitude_pattern"),
        ("Business Interpretation", "string", "business_interpretation"),
    ]
    score_types = [(src, {"string": "type text", "int64": "Int64.Type", "double": "type number", "boolean": "type logical"}[dtype]) for _, dtype, src in score_cols]
    score_measures = [
        model_measure("Observed Stable-Category Product Count", "SUM('Category Scorecard'[Observed Stable-Category Product Count Value])", "#,0"),
        model_measure("Eligible Favorite-Movement Product Count", "SUM('Category Scorecard'[Eligible Favorite-Movement Product Count Value])", "#,0"),
        model_measure("Eligible Exact Interval Observation Count", "SUM('Category Scorecard'[Eligible Exact Interval Count])", "#,0"),
        model_measure("Positive Favorite-Movement Product Count", "SUM('Category Scorecard'[Positive Product Count])", "#,0"),
        model_measure("Positive Favorite-Movement Breadth", "IF(HASONEVALUE('Category Scorecard'[Broad Product Category]), SELECTEDVALUE('Category Scorecard'[Positive Favorite-Movement Breadth Value]), BLANK())", "0.0\"%\""),
        model_measure("Median Daily Favorite Movement per Product", "IF(HASONEVALUE('Category Scorecard'[Broad Product Category]), SELECTEDVALUE('Category Scorecard'[Median Daily Favorite Movement Value]), BLANK())", "0.000"),
        model_measure("Observed Dates", "SELECTEDVALUE('Category Scorecard'[Observed Date Count])", "0"),
        model_measure("Breadth Wilson 95% Lower", "SELECTEDVALUE('Category Scorecard'[Breadth Wilson 95% Lower Value])", "0.0\"%\""),
        model_measure("Breadth Wilson 95% Upper", "SELECTEDVALUE('Category Scorecard'[Breadth Wilson 95% Upper Value])", "0.0\"%\""),
        model_measure("Breadth Wilson 95% Width", "SELECTEDVALUE('Category Scorecard'[Breadth Wilson 95% Width Value])", "0.0\" pp\""),
        model_measure("Broad Product Category Count", "DISTINCTCOUNT('Category Scorecard'[Broad Product Category])", "0"),
        model_measure("Publishable Broad Product Category Count", "CALCULATE(DISTINCTCOUNT('Category Scorecard'[Broad Product Category]), 'Category Scorecard'[Evidence Sufficiency Tier] <> \"INSUFFICIENT\")", "0"),
        model_measure("Insufficient Broad Product Category Count", "CALCULATE(DISTINCTCOUNT('Category Scorecard'[Broad Product Category]), 'Category Scorecard'[Evidence Sufficiency Tier] = \"INSUFFICIENT\")", "0"),
        model_measure("Evidence-Sufficient Category Count Display", "VAR sufficient = CALCULATE(DISTINCTCOUNT('Category Scorecard'[Broad Product Category]), 'Category Scorecard'[Evidence Sufficiency Tier] <> \"INSUFFICIENT\") VAR total = CALCULATE(DISTINCTCOUNT('Category Scorecard'[Broad Product Category]), REMOVEFILTERS('Category Scorecard'[Evidence Sufficiency Tier], 'Category Scorecard'[Sensitivity Status])) RETURN FORMAT(sufficient, \"0\") & \" / \" & FORMAT(total, \"0\")"),
        model_measure("Maximum Positive Favorite-Movement Breadth Display", "VAR maximum = MAXX(VALUES('Category Scorecard'[Broad Product Category]), CALCULATE([Positive Favorite-Movement Breadth])) RETURN IF(ISBLANK(maximum), \"N/A - insufficient evidence\", FORMAT(maximum / 100, \"0.0%\"))"),
        model_measure("Maximum Median Daily Favorite Movement Display", "VAR maximum = MAXX(VALUES('Category Scorecard'[Broad Product Category]), CALCULATE([Median Daily Favorite Movement per Product])) RETURN IF(ISBLANK(maximum), \"N/A - insufficient evidence\", FORMAT(maximum, \"0.000\"))"),
        model_measure("Positive Favorite-Movement Breadth Display", "VAR v=[Positive Favorite-Movement Breadth] RETURN IF(ISBLANK(v), \"N/A — insufficient evidence\", FORMAT(v/100, \"0.0%\"))"),
        model_measure("Median Daily Favorite Movement Display", "VAR v=[Median Daily Favorite Movement per Product] RETURN IF(ISBLANK(v), \"N/A — insufficient evidence\", FORMAT(v, \"0.000\"))"),
        model_measure("Eligible Favorite-Movement Product Count Display", "FORMAT([Eligible Favorite-Movement Product Count], \"#,0\")"),
        model_measure("Observed Dates Display", "VAR observed = [Observed Dates] RETURN IF(ISBLANK(observed), \"N/A\", FORMAT(observed, \"0\") & \" observed\")"),
        model_measure("Evidence Sufficiency Tier Display", "SELECTEDVALUE('Category Scorecard'[Evidence Sufficiency Tier], \"Select one category\")"),
    ]
    score_table = {
        "name": "Category Scorecard",
        "columns": [model_column(name, dtype, src) for name, dtype, src in score_cols],
        "measures": score_measures,
        "partitions": [{"name": "Category Scorecard", "mode": "import", "source": {"type": "m", "expression": m_csv(SCORECARD_SOURCE, score_types)}}],
    }

    sens_cols = [
        ("Broad Product Category", "string", "broad_product_category"),
        ("Evidence Sufficiency Tier", "string", "evidence_sufficiency_tier"),
        ("Sensitivity Status", "string", "sensitivity_status"),
        ("Sensitivity Scenario", "string", "sensitivity_scenario"),
        ("Unit of Analysis", "string", "unit_of_analysis"),
        ("Eligible Unit Count", "int64", "eligible_unit_count"),
        ("Positive Unit Count", "int64", "positive_unit_count"),
        ("Zero Unit Count", "int64", "zero_unit_count"),
        ("Negative Unit Count", "int64", "negative_unit_count"),
        ("Positive Breadth Value", "double", "positive_favorite_movement_breadth"),
        ("Median Movement Value", "double", "median_daily_favorite_movement"),
        ("Difference from Primary Value", "double", "breadth_difference_from_primary_percentage_points"),
        ("Interpretation Note", "string", "interpretation_note"),
    ]
    sens_types = [(src, {"string": "type text", "int64": "Int64.Type", "double": "type number"}[dtype]) for _, dtype, src in sens_cols]
    scenario_display = "SWITCH('Sensitivity'[Sensitivity Scenario], \"PRIMARY_EXACT_PRODUCT\", \"PRIMARY — exact displays\", \"COMPACT_INCLUSIVE_PRODUCT\", \"SENSITIVITY — compact inclusive\", \"OUTLIER_EXCLUDED_PRODUCT\", \"SENSITIVITY — outlier excluded\", \"INTERVAL_WEIGHTED_EXACT\", \"SENSITIVITY — interval weighted\", 'Sensitivity'[Sensitivity Scenario])"
    scenario_type = "IF('Sensitivity'[Sensitivity Scenario] = \"PRIMARY_EXACT_PRODUCT\", \"PRIMARY\", \"SENSITIVITY\")"
    sens_table = {
        "name": "Sensitivity",
        "columns": [model_column(name, dtype, src) for name, dtype, src in sens_cols] + [
            calculated_column("Scenario Display", "string", scenario_display),
            calculated_column("Scenario Type", "string", scenario_type),
        ],
        "measures": [
            model_measure("Scenario Positive Breadth", "SELECTEDVALUE('Sensitivity'[Positive Breadth Value])", "0.0\"%\""),
            model_measure("Scenario Median Movement", "SELECTEDVALUE('Sensitivity'[Median Movement Value])", "0.000"),
            model_measure("Difference from Primary", "SELECTEDVALUE('Sensitivity'[Difference from Primary Value])", "0.0\" pp\""),
            model_measure("Scenario Eligible Units", "SELECTEDVALUE('Sensitivity'[Eligible Unit Count])", "#,0"),
        ],
        "partitions": [{"name": "Sensitivity", "mode": "import", "source": {"type": "m", "expression": m_csv(SENSITIVITY_SOURCE, sens_types)}}],
    }
    model = {
        "name": NAME,
        "compatibilityLevel": 1600,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "tables": [score_table, sens_table],
            "relationships": [{
                "name": "CategoryScorecard_to_Sensitivity",
                "fromTable": "Sensitivity", "fromColumn": "Broad Product Category",
                "toTable": "Category Scorecard", "toColumn": "Broad Product Category",
            }],
        },
    }
    write_json(MODEL / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "1.0",
        "settings": {"qnaEnabled": False},
    })
    write_json(MODEL / "model.bim", model)


def build_scaffold() -> None:
    DASHBOARD.mkdir(exist_ok=True)
    write_json(DASHBOARD / f"{NAME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    })
    write_json(REPORT / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}},
    })
    write_json(REPORT / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": "Shopee Category Engagement"},
        "config": {"version": "2.0", "logicalId": "0f08cfb9-4460-4b1a-a3cf-3bd08c8946d1"},
    })
    write_json(MODEL / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": "Shopee Category Engagement"},
        "config": {"version": "2.0", "logicalId": "3d68333d-18cb-4828-9cda-84a1eecf811b"},
    })
    write_json(DEFINITION / "version.json", {
        "$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0",
    })
    write_json(DEFINITION / "report.json", {
        "$schema": f"{SCHEMA}/report/3.3.0/schema.json",
        # report/3.3.0 requires themeCollection. An empty collection delegates
        # the base theme to Power BI Desktop without inventing a resource name.
        "themeCollection": {},
        "objects": {"section": [{"properties": {"verticalAlignment": literal("'Top'")}}]},
    })
    page_order = [PAGE_IDS["overview"], PAGE_IDS["deep_dive"], PAGE_IDS["evidence"]]
    write_json(PAGES / "pages.json", {
        "$schema": f"{SCHEMA}/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_order,
        "activePageName": PAGE_IDS["overview"],
    })
    page_meta = {
        "overview": ("Category Engagement Overview", "Executive view of breadth, magnitude, evidence, and sampled scale."),
        "deep_dive": ("Category Evidence Deep Dive", "Single-category primary and sensitivity evidence."),
        "evidence": ("Evidence & Limitations", "Evidence gates, sampling constraints, and unsupported claims."),
    }
    for key, page_id in PAGE_IDS.items():
        display, _ = page_meta[key]
        write_json(PAGES / page_id / "page.json", {
            "$schema": f"{SCHEMA}/page/2.1.0/schema.json",
            "name": page_id,
            "displayName": display,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
            "objects": {
                "background": [{"properties": {"color": {"solid": {"color": literal(f"'{COLORS['page']}'")}}, "transparency": literal("0D")}}]
            },
        })


def build_manifest() -> None:
    files = sorted(p for p in DASHBOARD.rglob("*") if p.is_file())
    manifest = {
        "phase": 9,
        "analysis_version": "2.0.0",
        "publication_grain": "Broad Product Category",
        "category_count": 12,
        "portable_import_strategy": "Base64-embedded governed Phase 7 publication facts; rebuild with the generator to refresh",
        "project": str((DASHBOARD / f"{NAME}.pbip").relative_to(ROOT)).replace("\\", "/"),
        "source_tables": [str(p.relative_to(ROOT)).replace("\\", "/") for p in (SCORECARD_SOURCE, SENSITIVITY_SOURCE, FINDINGS_SOURCE)],
        "pages": ["Category Engagement Overview", "Category Evidence Deep Dive", "Evidence & Limitations"],
        "files": [{
            "path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size,
        } for p in files if p.name != "phase_9_build_manifest.json"],
    }
    write_json(DASHBOARD / "phase_9_build_manifest.json", manifest)


def main() -> None:
    for source in (SCORECARD_SOURCE, SENSITIVITY_SOURCE, FINDINGS_SOURCE):
        if not source.exists():
            raise FileNotFoundError(source)
    build_scaffold()
    build_model()
    build_overview()
    build_deep_dive()
    build_evidence()
    build_manifest()
    print(f"Built {DASHBOARD / (NAME + '.pbip')}")


if __name__ == "__main__":
    main()
