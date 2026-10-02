"""Data behind every IELTS Academic Writing Task 1 visual (rendered by `chart_renderer`).

The same data is passed to the AI examiner as text, so it can check whether the candidate
reported the figures accurately (Task Achievement).
"""

from __future__ import annotations

from typing import Any

# Prompt overrides where the original wording described something impractical to draw.
TASK1_PROMPT_OVERRIDES: dict[str, str] = {
    "IELTS-MOCK-02": (
        "The line graph below compares the average daily number of passengers using the metro, "
        "electric buses and private cars in Tashkent between 2010 and 2025. Summarise the information "
        "by selecting and reporting the main features, and make comparisons where relevant. "
        "(Write at least 150 words.)"
    ),
}

TASK1_CHARTS: dict[str, dict[str, Any]] = {
    "IELTS-MOCK-01": {
        "type": "panels",
        "title": "Households with fibre-optic internet and solar energy, 2015 and 2025 (%)",
        "panels": [
            {
                "type": "bar",
                "title": "Fibre-optic internet access",
                "y_label": "% of households",
                "categories": ["South Korea", "Germany", "Uzbekistan", "Brazil"],
                "series": [
                    {"name": "2015", "values": [82, 68, 24, 41]},
                    {"name": "2025", "values": [97, 89, 78, 70]},
                ],
            },
            {
                "type": "bar",
                "title": "Solar energy use",
                "y_label": "% of households",
                "categories": ["South Korea", "Germany", "Uzbekistan", "Brazil"],
                "series": [
                    {"name": "2015", "values": [6, 18, 3, 5]},
                    {"name": "2025", "values": [21, 46, 39, 27]},
                ],
            },
        ],
    },
    "IELTS-MOCK-02": {
        "type": "line",
        "title": "Average daily passengers in Tashkent, 2010–2025 (thousands)",
        "y_label": "thousand passengers per day",
        "x": ["2010", "2013", "2016", "2019", "2022", "2025"],
        "series": [
            {"name": "Metro", "values": [180, 210, 260, 330, 450, 620]},
            {"name": "Electric buses", "values": [0, 5, 30, 90, 210, 340]},
            {"name": "Private cars", "values": [520, 610, 700, 760, 740, 690]},
        ],
    },
    "IELTS-MOCK-03": {
        "type": "pie",
        "title": "Electricity generation by source (%)",
        "pies": [
            {"title": "2015", "slices": [
                {"label": "Natural gas", "value": 70}, {"label": "Hydro", "value": 13},
                {"label": "Coal", "value": 12}, {"label": "Wind", "value": 3}, {"label": "Solar", "value": 2},
            ]},
            {"title": "2030 (projected)", "slices": [
                {"label": "Natural gas", "value": 38}, {"label": "Hydro", "value": 15},
                {"label": "Coal", "value": 4}, {"label": "Wind", "value": 15}, {"label": "Solar", "value": 28},
            ]},
        ],
    },
    "IELTS-MOCK-04": {
        "type": "table",
        "title": "Average weekly hours by age group, 2024",
        "columns": ["Age group", "Physical exercise", "Screen-based leisure", "Sleep"],
        "rows": [
            ["16–24", "5.5", "28", "52"],
            ["25–39", "3.2", "21", "47"],
            ["40–59", "2.8", "17", "46"],
            ["60+", "4.1", "24", "53"],
        ],
    },
    "IELTS-MOCK-05": {
        "type": "process",
        "title": "How a satellite-based irrigation system works",
        "steps": [
            "Soil sensors measure moisture every hour",
            "Data is sent by radio to a farm gateway",
            "Gateway uploads the data to a satellite",
            "Satellite relays the data to a control centre",
            "Computer compares moisture with crop needs and the weather forecast",
            "Irrigation command is sent back via satellite",
            "Valves open and drip irrigation starts",
            "Sensors confirm the new moisture level (cycle repeats)",
        ],
    },
    "IELTS-MOCK-06": {
        "type": "bar",
        "title": "University graduates employed by sector, 2015 and 2025 (%)",
        "y_label": "% of graduates",
        "categories": ["IT", "Education", "Finance", "Engineering", "Healthcare"],
        "series": [
            {"name": "2015", "values": [12, 28, 18, 22, 20]},
            {"name": "2025", "values": [31, 19, 15, 17, 18]},
        ],
    },
    "IELTS-MOCK-07": {
        "type": "map",
        "title": "Historic city square, 1995 and 2025",
        "maps": [
            {"title": "1995", "items": [
                {"label": "Main road", "x": 0, "y": 0, "w": 100, "h": 14, "kind": "road"},
                {"label": "Madrasa", "x": 4, "y": 22, "w": 22, "h": 56, "kind": "building"},
                {"label": "Car park", "x": 32, "y": 26, "w": 36, "h": 40, "kind": "open"},
                {"label": "Bus station", "x": 74, "y": 22, "w": 22, "h": 34, "kind": "building"},
                {"label": "Shops", "x": 74, "y": 60, "w": 22, "h": 18, "kind": "building"},
                {"label": "Market stalls", "x": 30, "y": 72, "w": 40, "h": 22, "kind": "open"},
            ]},
            {"title": "2025", "items": [
                {"label": "Pedestrian street", "x": 0, "y": 0, "w": 100, "h": 14, "kind": "open"},
                {"label": "Madrasa", "x": 4, "y": 22, "w": 22, "h": 40, "kind": "building"},
                {"label": "Tourist info", "x": 4, "y": 66, "w": 22, "h": 12, "kind": "building"},
                {"label": "Square & fountain", "x": 32, "y": 26, "w": 36, "h": 40, "kind": "open"},
                {"label": "Crafts museum", "x": 74, "y": 22, "w": 22, "h": 34, "kind": "building"},
                {"label": "Hotel", "x": 74, "y": 60, "w": 22, "h": 18, "kind": "building"},
                {"label": "Cafés & souvenirs", "x": 30, "y": 72, "w": 40, "h": 22, "kind": "building"},
                {"label": "Trees", "x": 28, "y": 18, "w": 44, "h": 5, "kind": "trees"},
            ]},
        ],
    },
    "IELTS-MOCK-08": {
        "type": "line",
        "title": "Public library loans and downloads, 2016–2025 (thousands)",
        "y_label": "thousands",
        "x": ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"],
        "series": [
            {"name": "Printed books", "values": [410, 395, 380, 350, 300, 290, 275, 260, 250, 240]},
            {"name": "E-books", "values": [40, 55, 75, 110, 190, 220, 245, 265, 285, 300]},
            {"name": "Audiobooks", "values": [5, 8, 12, 20, 45, 70, 95, 120, 150, 175]},
        ],
    },
    "IELTS-MOCK-09": {
        "type": "table",
        "title": "International university students and average tuition fees",
        "columns": ["Country", "Students 2018 (thousands)", "Students 2025 (thousands)", "Average annual tuition (USD)"],
        "rows": [
            ["UK", "458", "680", "26,000"],
            ["Germany", "282", "380", "1,500"],
            ["South Korea", "142", "210", "7,500"],
            ["Australia", "420", "390", "24,000"],
        ],
    },
    "IELTS-MOCK-10": {
        "type": "panels",
        "title": "Crop yields and drip-irrigation use in Uzbekistan, 2015–2025",
        "panels": [
            {
                "type": "line",
                "title": "Yield (tonnes per hectare)",
                "y_label": "tonnes / ha",
                "x": ["2015", "2017", "2019", "2021", "2023", "2025"],
                "series": [
                    {"name": "Wheat", "values": [4.8, 4.9, 5.1, 5.4, 5.6, 5.9]},
                    {"name": "Fruit", "values": [9.5, 10.2, 11.4, 13.0, 14.8, 16.5]},
                ],
            },
            {
                "type": "bar",
                "title": "Farmland using drip irrigation (%)",
                "y_label": "%",
                "categories": ["2015", "2017", "2019", "2021", "2023", "2025"],
                "series": [{"name": "Drip irrigation", "values": [3, 6, 11, 19, 28, 37]}],
            },
        ],
    },
}


def chart_to_text(spec: dict[str, Any]) -> str:
    """Plain-text rendering of the chart data for the AI examiner prompt."""
    kind = spec.get("type")
    lines: list[str] = [str(spec.get("title", ""))]
    if kind == "panels":
        for panel in spec["panels"]:
            lines.append(chart_to_text(panel))
    elif kind == "bar":
        for s in spec["series"]:
            pairs = ", ".join(f"{c}: {v}" for c, v in zip(spec["categories"], s["values"]))
            lines.append(f"{s['name']} — {pairs}")
    elif kind == "line":
        for s in spec["series"]:
            pairs = ", ".join(f"{x}: {v}" for x, v in zip(spec["x"], s["values"]))
            lines.append(f"{s['name']} — {pairs}")
    elif kind == "pie":
        for pie in spec["pies"]:
            parts = ", ".join(f"{sl['label']} {sl['value']}%" for sl in pie["slices"])
            lines.append(f"{pie['title']}: {parts}")
    elif kind == "table":
        lines.append(" | ".join(spec["columns"]))
        lines.extend(" | ".join(row) for row in spec["rows"])
    elif kind == "process":
        lines.extend(f"Stage {i}: {step}" for i, step in enumerate(spec["steps"], start=1))
    elif kind == "map":
        for m in spec["maps"]:
            lines.append(f"{m['title']}: " + ", ".join(item["label"] for item in m["items"]))
    return "\n".join(line for line in lines if line)
