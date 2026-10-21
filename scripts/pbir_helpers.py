from pathlib import Path
import json
BASE="https://developer.microsoft.com/json-schemas/fabric/"
INK="#172638"
REPORT=None

def configure(report):
    global REPORT
    REPORT=Path(report)

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def literal(value):
    if isinstance(value, bool):
        value = "true" if value else "false"
    elif isinstance(value, (int, float)):
        value = str(value) + "D"
    else:
        value = "'" + str(value).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": value}}}


def color(value):
    return {"solid": {"color": literal(value)}}


def field(table, name, measure=False):
    return {("Measure" if measure else "Column"): {
        "Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def projection(table, name, measure=False, display=None):
    value = {"field": field(table, name, measure), "queryRef": table + "." + name,
             "nativeQueryRef": name}
    if display:
        value["displayName"] = display
    return value


def container(title, background="#FFFFFF"):
    return {
        "title": [{"properties": {"show": literal(bool(title)), "text": literal(title),
            "fontColor": color(INK), "fontSize": literal(12), "bold": literal(True),
            "fontFamily": literal("Segoe UI")}}],
        "background": [{"properties": {"show": literal(True), "color": color(background), "transparency": literal(0)}}],
        "border": [{"properties": {"show": literal(True), "color": color("#DCE5EB"), "radius": literal(8)}}],
    }


def visual(page, name, kind, x, y, w, h, title="", roles=None, sort=None, objects=None):
    content = {"visualType": kind, "visualContainerObjects": container(title)}
    if roles:
        content["query"] = {"queryState": {role: {"projections": values} for role, values in roles.items()}}
        if sort:
            content["query"]["sortDefinition"] = {"sort": [{"field": sort[0], "direction": sort[1]}],
                                                   "isDefaultSort": False}
    if objects:
        content["objects"] = objects
    value = {"$schema": BASE + "item/report/definition/visualContainer/2.4.0/schema.json",
        "name": name, "position": {"x": x, "y": y, "z": y, "width": w, "height": h, "tabOrder": y},
        "visual": content}
    write(REPORT / "definition/pages" / page / "visuals" / name / "visual.json", value)


def textbox(page, name, text, x, y, w, h, size=12, foreground=INK, background="#FFFFFF"):
    visual(page, name, "textbox", x, y, w, h, objects={
        "general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": line, "textStyle": {"fontFamily": "Segoe UI",
                "fontSize": str(size) + "pt", "color": foreground}}]} for line in text.split("\n")
        ]}}]})
    path = REPORT / "definition/pages" / page / "visuals" / name / "visual.json"
    value = json.loads(path.read_text())
    value["visual"]["visualContainerObjects"] = container("", background)
    write(path, value)
