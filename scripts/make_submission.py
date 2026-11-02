"""
Build the Task 2 submission zip for Forage.

Runs the tests, records a demo conversation, and packages the chatbot script,
data, tests, test results and documentation into a single zip file.

Run from the project folder:
    python scripts/make_submission.py
"""

import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from chatbot.financial_chatbot import FinancialChatbot, simple_chatbot  # noqa: E402

NAME = "BCG_GenAI_Task2_Gibson_Nyendwa"
OUT_DIR = ROOT / "submission"
STAGE = OUT_DIR / NAME

FILES = {
    "chatbot/__init__.py": "chatbot/__init__.py",
    "chatbot/financial_chatbot.py": "chatbot/financial_chatbot.py",
    "chatbot/app.py": "chatbot/app.py",
    "data/financial_analysis.csv": "data/financial_analysis.csv",
    "tests/__init__.py": "tests/__init__.py",
    "tests/test_chatbot.py": "tests/test_chatbot.py",
    "notebooks/02_financial_chatbot.ipynb": "notebook/02_financial_chatbot.ipynb",
    "notebooks/BCG_GenAI_Task2_Gibson_Nyendwa.html": "notebook/BCG_GenAI_Task2_Gibson_Nyendwa.html",
    "requirements.txt": "requirements.txt",
    "pytest.ini": "pytest.ini",
    "docs/CHATBOT_DOCUMENTATION.md": "README.md",
}

DEMO_V1 = [
    "What is the total revenue?",
    "How has net income changed over the last year?",
    "What are the total assets?",
    "What are the total liabilities?",
    "What is the cash flow from operating activities?",
    "What was Tesla's revenue?",
]

DEMO_V2 = [
    "Hello",
    "What was Apple's revenue in 2025?",
    "How has Tesla's net income changed over the last year?",
    "What about Microsoft?",
    "And in 2024?",
    "Which company has the highest net margin?",
    "Which company is least leveraged?",
    "Show a chart of revenue",
    "How healthy is Tesla?",
    "Apple net income 2024",
    "What is Amazon's revenue?",
    "What was Microsoft's revenue in 2019?",
    "What is the weather today?",
    "bye",
]


def run_tests() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--color=no", "-p", "no:cacheprovider", "tests"],
        cwd=ROOT, capture_output=True, text=True)
    header = (f"GFC Financial Chatbot: test results\n"
              f"Run on {datetime.now():%d %B %Y at %H:%M}\n"
              f"Command: pytest -v tests\n{'=' * 70}\n")
    return header + result.stdout


def demo_conversation() -> str:
    lines = ["GFC Financial Chatbot: demo conversation", "=" * 70, "",
             "VERSION 1: predefined queries (if/else, Microsoft, latest fiscal year)", "-" * 70]
    for q in DEMO_V1:
        lines += [f"You: {q}", f"Bot: {simple_chatbot(q)}", ""]
    lines += ["", "VERSION 2: FinancialChatbot (rule-based understanding with conversation memory)", "-" * 70]
    bot = FinancialChatbot()
    for q in DEMO_V2:
        lines += [f"You: {q}", f"Bot: {bot.respond(q)}", ""]
    return "\n".join(lines)


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    for src, dest in FILES.items():
        target = STAGE / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / src, target)

    results = run_tests()
    (STAGE / "test_results.txt").write_text(results, encoding="utf-8")
    (STAGE / "demo_conversation.txt").write_text(demo_conversation(), encoding="utf-8")
    (OUT_DIR / "test_results.txt").write_text(results, encoding="utf-8")
    (OUT_DIR / "demo_conversation.txt").write_text(demo_conversation(), encoding="utf-8")

    zip_path = OUT_DIR / f"{NAME}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(STAGE.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(OUT_DIR))
    shutil.rmtree(STAGE)

    summary = [line for line in results.splitlines() if "passed" in line or "failed" in line][-1]
    print(f"Created {zip_path.relative_to(ROOT)}  |  tests: {summary.strip('= ')}")


if __name__ == "__main__":
    main()
