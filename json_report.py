import json

def write_json_report(page_data: dict, filename: str = "report.json") -> None:
    pages = sorted(page_data.values(), key=lambda p: p["url"])

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(pages, f, indent=2)
