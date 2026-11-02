"""
Parity test: proves the browser chatbot (web/chatbot.js) gives exactly the same
answers as the Python chatbot (chatbot/financial_chatbot.py).

Runs the same conversations through both and compares every reply, character
for character. Requires Node.js.

Run from the project folder:
    python scripts/parity_test.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from chatbot.financial_chatbot import FinancialChatbot  # noqa: E402
from scripts.build_web_demo import write_payload  # noqa: E402

COMPANIES = ["Microsoft", "Tesla", "Apple", "msft", "AAPL", "tsla"]
METRIC_WORDS = ["revenue", "sales", "net income", "profit", "earnings", "total assets", "liabilities", "debt",
                "operating cash flow", "cash flow", "net margin", "leverage", "equity", "bottom line"]
YEARS = ["2023", "2024", "2025", "fy24", "last year", "previous year", ""]

# Single questions, each asked to a fresh bot
SINGLE = []
for c in COMPANIES:
    for m in METRIC_WORDS:
        for y in YEARS:
            SINGLE.append(f"What was {c}'s {m} {('in ' + y) if y else ''}?")
            SINGLE.append(f"How has {c}'s {m} changed {y}")
        SINGLE.append(f"Show {c}'s {m} trend")
        SINGLE.append(f"Show a chart of {c} {m}")
        SINGLE.append(f"How healthy is {c}?")
        SINGLE.append(f"Should I buy {c} shares?")
for m in METRIC_WORDS:
    for w in ["highest", "lowest", "most", "least", "biggest", "smallest"]:
        SINGLE.append(f"Which company has the {w} {m}?")
    for w in ["fastest", "slowest"]:
        SINGLE.append(f"Which company grew {m} {w}?")
    SINGLE.append(f"Show a chart of {m}")
    SINGLE.append(f"Compare apple and tesla {m} in 2024")
SINGLE += ["hello", "help", "thanks", "bye", "", "   ", "asdfgh", "What is the weather?", "summary",
           "What is Amazon's revenue?", "nvidia profit", "Microsoft revenue in 2019", "tesla revenue 2022",
           "Is Apple more profitable than Tesla?", "how much did msft earn in fy24", "What's Apple's share price?",
           "tell me more about microsoft", "How did Apple's revenue change in 2023?", "all three companies revenue",
           "Microsoft vs Apple revenue", "What is the total revenue?", "how is tesla doing", "overview"]

# Multi-turn conversations, testing memory
CONVERSATIONS = [
    ["How has Tesla's net income changed over the last year?", "What about Microsoft?", "And in 2024?",
     "what about cash flow", "Which company is least leveraged?", "What is Apple's leverage?", "summary"],
    ["Which company had the most revenue in 2023?", "How did it change?", "Show the trend", "and tesla?"],
    ["how much did msft earn in fy24", "and tesla?", "what about apple", "Show a chart", "thanks", "bye"],
    ["Should I buy Tesla shares?", "what about revenue", "and in 2023?", "How healthy is Apple?", "and Microsoft"],
    ["What was Apple's revenue in 2025?", "And in 2024?", "how about profit", "What about Tesla?",
     "Which company grew it fastest?", "asdfgh", "What is the weather?"],
]

NODE_RUNNER = r"""
const fs = require('fs');
const { FinancialChatbot } = require(process.argv[2]);
const { knowledge, rows } = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const { single, conversations } = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const out = { single: single.map(q => new FinancialChatbot(knowledge, rows).respond(q)),
              conversations: conversations.map(conv => { const b = new FinancialChatbot(knowledge, rows); return conv.map(q => b.respond(q)); }) };
process.stdout.write(JSON.stringify(out));
"""


def python_answers() -> dict:
    return {"single": [FinancialChatbot().respond(q) for q in SINGLE],
            "conversations": [[bot.respond(q) for q in conv] for conv in CONVERSATIONS
                              for bot in [FinancialChatbot()]]}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        write_payload(tmp / "payload.json")
        (tmp / "questions.json").write_text(json.dumps({"single": SINGLE, "conversations": CONVERSATIONS}))
        (tmp / "runner.js").write_text(NODE_RUNNER)
        js = json.loads(subprocess.run(
            ["node", str(tmp / "runner.js"), str(ROOT / "web" / "chatbot.js"),
             str(tmp / "payload.json"), str(tmp / "questions.json")],
            capture_output=True, text=True, check=True).stdout)
    py = python_answers()

    mismatches = []
    for q, a, b in zip(SINGLE, py["single"], js["single"]):
        if a != b:
            mismatches.append((q, a, b))
    for conv, pa, ja in zip(CONVERSATIONS, py["conversations"], js["conversations"]):
        for q, a, b in zip(conv, pa, ja):
            if a != b:
                mismatches.append((f"[conversation] {q}", a, b))

    total = len(SINGLE) + sum(len(c) for c in CONVERSATIONS)
    for q, a, b in mismatches[:5]:
        print(f"MISMATCH: {q!r}\n  python: {a!r}\n  js:     {b!r}\n")
    print(f"Parity test: {total - len(mismatches)}/{total} answers identical "
          f"({len(SINGLE)} single questions, {len(CONVERSATIONS)} conversations).")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
