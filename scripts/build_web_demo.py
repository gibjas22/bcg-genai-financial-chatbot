"""
Build the browser demo of the GFC Financial Chatbot.

Exports the chatbot's knowledge (keyword dictionaries, context notes, verdicts)
and the Task 1 dataset straight from the Python code, then inlines them with
web/chatbot.js into one self-contained page: web/gfc_chatbot_demo.html.

Run from the project folder:
    python scripts/build_web_demo.py
"""

import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from chatbot import financial_chatbot as fc  # noqa: E402


def knowledge() -> dict:
    return {
        "COMPANY_ALIASES": fc.COMPANY_ALIASES,
        "OUT_OF_SCOPE_COMPANIES": fc.OUT_OF_SCOPE_COMPANIES,
        "METRICS": fc.METRICS,
        "CONTEXT_NOTES": {f"{c}|{m}|{'None' if y is None else y}": note for (c, m, y), note in fc.CONTEXT_NOTES.items()},
        "CHART_FILES": fc.CHART_FILES,
        "HEALTH_VERDICTS": fc.HEALTH_VERDICTS,
        "INTENT_KEYWORDS": fc.INTENT_KEYWORDS,
    }


def data_rows() -> list[dict]:
    df = pd.read_csv(fc.DATA_PATH)
    rows = df.to_dict(orient="records")
    for r in rows:
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                r[k] = None
        r["Fiscal Year"] = int(r["Fiscal Year"])
    return rows


def write_payload(path: Path) -> None:
    path.write_text(json.dumps({"knowledge": knowledge(), "rows": data_rows()}), encoding="utf-8")


def build_page() -> Path:
    template = (ROOT / "web" / "template.html").read_text(encoding="utf-8")
    engine = (ROOT / "web" / "chatbot.js").read_text(encoding="utf-8")
    payload = json.dumps({"knowledge": knowledge(), "rows": data_rows()})
    page = template.replace("/*__ENGINE__*/", engine).replace('"__PAYLOAD__"', payload)
    out = ROOT / "web" / "gfc_chatbot_demo.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--payload":
        write_payload(Path(sys.argv[2]))
    else:
        print("Built", build_page().relative_to(ROOT))
