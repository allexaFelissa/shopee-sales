"""Build the Phase 9 Power BI Project (PBIP) from governed Phase 7 tables.

The generated PBIR report is deliberately source-controlled and deterministic.
It does not recompute any governed KPI from upstream listing data.
"""

from __future__ import annotations

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
    "navy": "#16324F",
    "blue": "#3E6B89",
    "light_blue": "#DCEAF3",
    "orange": "#D97706",
    "purple": "#6D5BD0",
    "gray": "#737B84",
    "light_gray": "#EEF1F4",
    "ink": "#17202A",
    "muted": "#5C6773",
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
        "border": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#D9E0E6'")}}, "radius": literal("6D")}}],
        "dropShadow": [{"properties": {"show": literal("false")}}],
    }
    if title:
        out["title"] = [{"properties": {"show": literal("true"), "text": literal(f"'{title}'"), "fontColor": {"solid": {"color": literal("'#16324F'")}}, "fontSize": literal("12D"), "bold": literal("true"), "alignment": literal("'left'")}}]
    return out


def textbox(page_key: str, ordinal: int, text: str, x: int, y: int, w: int, h: int,
            size: int = 14, color: str = COLORS["ink"], weight: str | None = None) -> dict:
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
                "background": [{"properties": {"show": literal("false")}}],
                "border": [{"properties": {"show": literal("false")}}],
                "padding": [{"properties": {"top": literal("0D"), "bottom": literal("0D"), "left": literal("0D"), "right": literal("0D")}}],
            },
        },
    }


def data_visual(page_key: str, ordinal: int, visual_type: str, roles: dict, x: int, y: int,
                w: int, h: int, title: str | None = None, objects: dict | None = None) -> dict:
    visual = {
        "visualType": visual_type,
        "query": {"queryState": roles},
        "visualContainerObjects": container_objects(title),
    }
    if objects:
        visual["objects"] = objects
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


def write_visual(page_key: str, visual: dict) -> str:
    page_id = PAGE_IDS[page_key]
    path = PAGES / page_id / "visuals" / visual["name"] / "visual.json"
    write_json(path, visual)
    return visual["name"]


def page_header(page_key: str, title: str, subtitle: str) -> int:
    write_visual(page_key, textbox(page_key, 1, title, 28, 18, 820, 42, 25, COLORS["navy"], "bold"))
    write_visual(page_key, textbox(page_key, 2, subtitle, 28, 60, 1040, 42, 12, COLORS["muted"]))
    write_visual(page_key, textbox(page_key, 3, "20-day sampled Shopee listing data  •  Favorite engagement, not sales", 930, 20, 320, 38, 11, COLORS["orange"], "bold"))
    return 4


def build_overview() -> None:
    key = "overview"
    i = page_header(key, "Category Engagement Overview", "Breadth, typical daily movement, eligible tracked-product scale, and evidence are separate dimensions.")
    write_visual(key, slicer(key, i, "Category Scorecard", "Evidence Sufficiency Tier", 930, 56, 150, 76, "Evidence Tier")); i += 1
    write_visual(key, slicer(key, i, "Category Scorecard", "Sensitivity Status", 1090, 56, 160, 76, "Sensitivity Status")); i += 1

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
    write_visual(key, data_visual(key, i, "scatterChart", scatter_roles, 28, 134, 790, 480, "Breadth vs typical displayed-favorite movement")); i += 1

    evidence_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Evidence Sufficiency Tier"), "Category Scorecard.Evidence Sufficiency Tier")]},
        "Y": {"projections": [projection(measure("Category Scorecard", "Broad Product Category Count"), "Category Scorecard.Broad Product Category Count")]},
    }
    write_visual(key, data_visual(key, i, "barChart", evidence_roles, 838, 134, 412, 190, "Evidence availability (not performance)")); i += 1
    write_visual(key, card(key, i, "Eligible Favorite-Movement Product Count", 838, 340, 198, 115, "Eligible Tracked Products")); i += 1
    write_visual(key, card(key, i, "Publishable Broad Product Category Count", 1052, 340, 198, 115, "Published Categories")); i += 1
    callout = ("Observed patterns to read with evidence context:\n"
               "• Groceries & Pets: strongest HIGH-evidence primary pattern; directionally stable.\n"
               "• Health & Beauty: strongest robust positive pattern; MODERATE evidence.\n"
               "• Women's Bags: largest published median; 46 eligible products / 17 dates.\n"
               "Top-right is not an automatic campaign priority.")
    write_visual(key, textbox(key, i, callout, 850, 478, 390, 150, 12, COLORS["ink"])); i += 1
    write_visual(key, textbox(key, i, "Source: governed Phase 7 category outputs, fixed 2023-04-24 to 2023-05-13 window. Ten insufficient categories remain unranked and have N/A movement values.", 28, 650, 1218, 42, 10, COLORS["muted"]))


def build_deep_dive() -> None:
    key = "deep_dive"
    i = page_header(key, "Category Evidence Deep Dive", "Select one Broad Product Category. Primary exact-display KPIs are prominent; sensitivities remain separate.")
    write_visual(key, slicer(key, i, "Category Scorecard", "Broad Product Category", 28, 106, 320, 76,
                             "Broad Product Category", single_select=True)); i += 1
    write_visual(key, card(key, i, "Positive Favorite-Movement Breadth Display", 370, 112, 205, 105, "Positive Breadth")); i += 1
    write_visual(key, card(key, i, "Median Daily Favorite Movement Display", 590, 112, 205, 105, "Median Favorites / Day")); i += 1
    write_visual(key, card(key, i, "Eligible Favorite-Movement Product Count Display", 810, 112, 205, 105, "Eligible Tracked Products")); i += 1
    write_visual(key, card(key, i, "Evidence Sufficiency Tier Display", 1030, 112, 220, 105, "Evidence Tier")); i += 1

    table_roles = {"Values": {"projections": [
        projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category"),
        projection(measure("Category Scorecard", "Observed Dates"), "Category Scorecard.Observed Dates"),
        projection(measure("Category Scorecard", "Breadth Wilson 95% Lower"), "Category Scorecard.Breadth Wilson 95% Lower"),
        projection(measure("Category Scorecard", "Breadth Wilson 95% Upper"), "Category Scorecard.Breadth Wilson 95% Upper"),
        projection(measure("Category Scorecard", "Breadth Wilson 95% Width"), "Category Scorecard.Breadth Wilson 95% Width"),
        projection(column("Category Scorecard", "Sensitivity Status"), "Category Scorecard.Sensitivity Status"),
    ]}}
    write_visual(key, data_visual(key, i, "tableEx", table_roles, 28, 238, 520, 205, "Primary evidence context")); i += 1

    sensitivity_roles = {
        "Category": {"projections": [projection(column("Sensitivity", "Scenario Display"), "Sensitivity.Scenario Display")]},
        "Series": {"projections": [projection(column("Sensitivity", "Scenario Type"), "Sensitivity.Scenario Type")]},
        "Y": {"projections": [projection(measure("Sensitivity", "Scenario Positive Breadth"), "Sensitivity.Scenario Positive Breadth")]},
        "Tooltips": {"projections": [projection(measure("Sensitivity", "Difference from Primary"), "Sensitivity.Difference from Primary")]},
    }
    write_visual(key, data_visual(key, i, "barChart", sensitivity_roles, 570, 238, 680, 310, "PRIMARY exact-display breadth vs SENSITIVITY specifications")); i += 1

    median_roles = {"Values": {"projections": [
        projection(column("Sensitivity", "Scenario Display"), "Sensitivity.Scenario Display"),
        projection(measure("Sensitivity", "Scenario Eligible Units"), "Sensitivity.Scenario Eligible Units"),
        projection(measure("Sensitivity", "Scenario Positive Breadth"), "Sensitivity.Scenario Positive Breadth"),
        projection(measure("Sensitivity", "Difference from Primary"), "Sensitivity.Difference from Primary"),
        projection(measure("Sensitivity", "Scenario Median Movement"), "Sensitivity.Scenario Median Movement"),
    ]}}
    write_visual(key, data_visual(key, i, "tableEx", median_roles, 28, 462, 520, 165, "Sensitivity evidence by specification")); i += 1
    write_visual(key, textbox(key, i, "N/A — insufficient evidence is intentionally distinct from zero. Compact-inclusive, outlier-excluded, and interval-weighted values are sensitivity checks, not replacements for the primary KPI.", 570, 568, 680, 56, 11, COLORS["orange"], "bold")); i += 1
    write_visual(key, textbox(key, i, "Fixed 20-day window; no date slicer. Broad Product Category selection filters the scorecard and sensitivity fact through a one-to-many category relationship.", 28, 650, 1218, 36, 10, COLORS["muted"]))


def build_evidence() -> None:
    key = "evidence"
    i = page_header(key, "Evidence & Limitations", "Evidence tier describes analytical support, not category performance.")
    write_visual(key, slicer(key, i, "Category Scorecard", "Evidence Sufficiency Tier", 920, 56, 160, 76, "Evidence Tier")); i += 1
    write_visual(key, slicer(key, i, "Category Scorecard", "Sensitivity Status", 1090, 56, 160, 76, "Sensitivity Status")); i += 1

    product_roles = {
        "Category": {"projections": [projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category")]},
        "Series": {"projections": [projection(column("Category Scorecard", "Evidence Sufficiency Tier"), "Category Scorecard.Evidence Sufficiency Tier")]},
        "Y": {"projections": [projection(measure("Category Scorecard", "Eligible Favorite-Movement Product Count"), "Category Scorecard.Eligible Favorite-Movement Product Count")]},
        "Tooltips": {"projections": [projection(measure("Category Scorecard", "Observed Dates"), "Category Scorecard.Observed Dates")]},
    }
    write_visual(key, data_visual(key, i, "barChart", product_roles, 28, 132, 610, 380, "Eligible tracked products by Broad Product Category")); i += 1

    evidence_table = {"Values": {"projections": [
        projection(column("Category Scorecard", "Broad Product Category"), "Category Scorecard.Broad Product Category"),
        projection(column("Category Scorecard", "Evidence Sufficiency Tier"), "Category Scorecard.Evidence Sufficiency Tier"),
        projection(measure("Category Scorecard", "Observed Dates"), "Category Scorecard.Observed Dates"),
        projection(measure("Category Scorecard", "Eligible Favorite-Movement Product Count"), "Category Scorecard.Eligible Favorite-Movement Product Count"),
        projection(measure("Category Scorecard", "Breadth Wilson 95% Width"), "Category Scorecard.Breadth Wilson 95% Width"),
        projection(column("Category Scorecard", "Sensitivity Status"), "Category Scorecard.Sensitivity Status"),
    ]}}
    write_visual(key, data_visual(key, i, "tableEx", evidence_table, 660, 132, 590, 380, "Evidence gates and sensitivity status")); i += 1

    limitations = ("What this analysis measures\n"
                   "Observed favorite-display movement among eligible repeatedly tracked listings in a sampled 20-day window. Exact displays are primary; compact/rounded displays appear only in sensitivity analysis.\n\n"
                   "What it does NOT establish\n"
                   "Sales or revenue growth • orders or conversion • customer demand • platform-wide category growth or market share • campaign effectiveness • future performance.\n\n"
                   "Sampling limits\n"
                   "Only a minority of products repeat; daily sampling is uneven; 10 categories have insufficient evidence and remain N/A/unranked.")
    write_visual(key, textbox(key, i, limitations, 28, 534, 830, 155, 12, COLORS["ink"])); i += 1
    write_visual(key, card(key, i, "Insufficient Broad Product Category Count", 885, 540, 165, 105, "N/A Categories")); i += 1
    write_visual(key, card(key, i, "Publishable Broad Product Category Count", 1070, 540, 180, 105, "Published Categories")); i += 1
    write_visual(key, textbox(key, i, "Tier gates: HIGH = 20 dates, n≥100, Wilson width≤20pp. MODERATE = ≥15 dates, n≥30, width≤35pp. Otherwise INSUFFICIENT.", 875, 655, 375, 40, 10, COLORS["muted"]))


def m_csv(path: Path, columns: list[tuple[str, str]]) -> list[str]:
    # Power Query M does not use backslash as a string escape character.
    source = str(path)
    types = ", ".join(f'{{"{name}", {kind}}}' for name, kind in columns)
    return [
        "let",
        f'    Source = Csv.Document(File.Contents("{source}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
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
        model_measure("Positive Favorite-Movement Breadth", "IF(HASONEVALUE('Category Scorecard'[Broad Product Category]), SELECTEDVALUE('Category Scorecard'[Positive Favorite-Movement Breadth Value]), BLANK())", "0.0\"%\""),
        model_measure("Median Daily Favorite Movement per Product", "IF(HASONEVALUE('Category Scorecard'[Broad Product Category]), SELECTEDVALUE('Category Scorecard'[Median Daily Favorite Movement Value]), BLANK())", "0.000"),
        model_measure("Observed Dates", "SELECTEDVALUE('Category Scorecard'[Observed Date Count])", "0"),
        model_measure("Breadth Wilson 95% Lower", "SELECTEDVALUE('Category Scorecard'[Breadth Wilson 95% Lower Value])", "0.0\"%\""),
        model_measure("Breadth Wilson 95% Upper", "SELECTEDVALUE('Category Scorecard'[Breadth Wilson 95% Upper Value])", "0.0\"%\""),
        model_measure("Breadth Wilson 95% Width", "SELECTEDVALUE('Category Scorecard'[Breadth Wilson 95% Width Value])", "0.0\" pp\""),
        model_measure("Broad Product Category Count", "DISTINCTCOUNT('Category Scorecard'[Broad Product Category])", "0"),
        model_measure("Publishable Broad Product Category Count", "CALCULATE(DISTINCTCOUNT('Category Scorecard'[Broad Product Category]), 'Category Scorecard'[Evidence Sufficiency Tier] <> \"INSUFFICIENT\")", "0"),
        model_measure("Insufficient Broad Product Category Count", "CALCULATE(DISTINCTCOUNT('Category Scorecard'[Broad Product Category]), 'Category Scorecard'[Evidence Sufficiency Tier] = \"INSUFFICIENT\")", "0"),
        model_measure("Positive Favorite-Movement Breadth Display", "VAR v=[Positive Favorite-Movement Breadth] RETURN IF(ISBLANK(v), \"N/A — insufficient evidence\", FORMAT(v/100, \"0.0%\"))"),
        model_measure("Median Daily Favorite Movement Display", "VAR v=[Median Daily Favorite Movement per Product] RETURN IF(ISBLANK(v), \"N/A — insufficient evidence\", FORMAT(v, \"0.000\"))"),
        model_measure("Eligible Favorite-Movement Product Count Display", "FORMAT([Eligible Favorite-Movement Product Count], \"#,0\")"),
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
        })


def build_manifest() -> None:
    files = sorted(p for p in DASHBOARD.rglob("*") if p.is_file())
    manifest = {
        "phase": 9,
        "analysis_version": "1.0.0",
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
