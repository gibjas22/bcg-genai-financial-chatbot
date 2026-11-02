"""
GFC Financial Chatbot
=====================

A rule-based conversational assistant that answers plain-English questions about
the financial performance of Microsoft, Tesla and Apple (fiscal years 2023 to 2025),
using the dataset prepared in Task 1 (data/financial_analysis.csv).

How it works (a simple NLP pipeline):
    1. Normalise the user's message (lower case, tidy spacing and punctuation).
    2. Extract entities: which company, which fiscal year, which financial metric.
    3. Classify the intent: a value, a change, a trend, a comparison, a summary or help.
    4. Fill gaps from conversation memory, so follow-ups like "what about Tesla?" work.
    5. Look the answer up in the verified dataset and reply in plain English,
       adding context where a one-off item would otherwise mislead.

Design principles (from GFC's requirements):
    - Accuracy: answers come only from the verified 10-K dataset. If the bot cannot
      answer, it says so rather than guessing.
    - User-friendly: plain English, figures in billions, ratios explained.
    - Efficiency: instant answers instead of reading a 100-page filing.
    - Scalability: add companies or years as rows in the CSV; no code changes needed.

Author: Gibson Nyendwa
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "financial_analysis.csv"

# --------------------------------------------------------------------------
# Knowledge the bot uses to understand questions
# --------------------------------------------------------------------------

COMPANY_ALIASES = {
    "Microsoft": ["microsoft", "msft"],
    "Tesla": ["tesla", "tsla"],
    "Apple": ["apple", "aapl"],
}

# Companies people may ask about that are not in the dataset
OUT_OF_SCOPE_COMPANIES = [
    "amazon", "google", "alphabet", "meta", "facebook", "nvidia", "netflix",
    "ibm", "intel", "oracle", "samsung", "toyota", "ford", "byd",
]

# Each metric: dataset column, growth column, how to display it, and the words
# people use for it. Longer phrases are matched first, so "liabilities to assets"
# wins over "liabilities", and "operating cash flow" wins over "cash".
METRICS = {
    "revenue": {
        "column": "Total Revenue", "growth": "Revenue Growth (%)",
        "label": "total revenue", "kind": "money", "higher_is_better": True,
        "keywords": ["total revenue", "revenue", "revenues", "sales", "turnover", "top line"],
    },
    "net_income": {
        "column": "Net Income", "growth": "Net Income Growth (%)",
        "label": "net income", "kind": "money", "higher_is_better": True,
        "keywords": ["net income", "net profit", "profit", "profits", "earnings", "earn", "earned", "earns", "bottom line"],
    },
    "assets": {
        "column": "Total Assets", "growth": "Assets Growth (%)",
        "label": "total assets", "kind": "money", "higher_is_better": True,
        "keywords": ["total assets", "assets"],
    },
    "liabilities": {
        "column": "Total Liabilities", "growth": "Liabilities Growth (%)",
        "label": "total liabilities", "kind": "money", "higher_is_better": False,
        "keywords": ["total liabilities", "liabilities", "debt", "debts", "obligations"],
    },
    "operating_cash_flow": {
        "column": "Cash Flow from Operating Activities", "growth": "Operating Cash Flow Growth (%)",
        "label": "operating cash flow", "kind": "money", "higher_is_better": True,
        "keywords": ["cash flow from operating activities", "operating cash flow",
                     "cash from operations", "cash flow", "operating cash", "ocf", "cash generation"],
    },
    "net_margin": {
        "column": "Net Margin (%)", "growth": None,
        "label": "net profit margin", "kind": "percent", "higher_is_better": True,
        "keywords": ["net profit margin", "profit margin", "net margin", "margin", "margins", "profitability",
                     "profitable", "more profitable", "most profitable"],
        "meaning": "the share of each dollar of revenue kept as profit",
    },
    "leverage": {
        "column": "Liabilities to Assets (%)", "growth": None,
        "label": "liabilities-to-assets ratio", "kind": "percent", "higher_is_better": False,
        "keywords": ["liabilities to assets", "debt ratio", "leverage", "leveraged", "gearing", "geared", "indebted"],
        "meaning": "the share of the company's assets funded by liabilities; lower means less leveraged",
    },
    "equity": {
        "column": "Shareholders Equity", "growth": None,
        "label": "shareholders' equity", "kind": "money", "higher_is_better": True,
        "keywords": ["shareholders equity", "shareholders' equity", "equity", "net worth", "book value"],
        "meaning": "total assets minus total liabilities",
    },
}

# One-off items that would mislead a user who only saw the percentage change.
# Taken from each company's 10-K MD&A and results releases.
CONTEXT_NOTES = {
    ("Tesla", "net_income", 2023): "FY2023 profit was boosted by a one-off tax benefit from releasing a valuation allowance on deferred tax assets, which makes later years look weaker by comparison.",
    ("Tesla", "net_income", 2024): "FY2023 included a one-off tax benefit, so part of this fall reflects an unusually high starting point rather than the business alone.",
    ("Tesla", "net_income", 2025): "Tesla linked the fall to lower vehicle deliveries and regulatory credit revenue, tariffs, and higher spending on AI and R&D.",
    ("Apple", "net_income", 2024): "FY2024 included a one-time income tax charge of about $10.2bn linked to the European Commission State Aid decision. Without it, net income would have been around $104bn.",
    ("Apple", "net_income", 2025): "The FY2024 comparison figure was reduced by a one-time tax charge of about $10.2bn, which flatters this year's growth rate.",
    ("Microsoft", "assets", 2024): "The jump largely reflects the Activision Blizzard acquisition, which added significant goodwill to the balance sheet.",
    ("Apple", "leverage", None): "Apple's high ratio is a deliberate choice: it returns large amounts of cash to shareholders through buybacks and dividends, which keeps equity low. It is not a sign of distress.",
}

# Saved chart images from the Task 1 notebook, referenced when a user asks for a visual
CHART_FILES = {
    "revenue": "charts/revenue_trend.png",
    "net_income": "charts/net_income_trend.png",
    "net_margin": "charts/net_margin_trend.png",
    "operating_cash_flow": "charts/operating_cash_flow_trend.png",
}

HEALTH_VERDICTS = {
    "Microsoft": "Strong and improving: the fastest growth, highest margins and falling leverage of the three.",
    "Apple": "Strong, with growth returning: record net income in FY2025 after a one-off tax charge in FY2024.",
    "Tesla": "Sound balance sheet but weakening profitability: revenue fell in FY2025 and net income dropped sharply, though cash flow held steady.",
}

INTENT_KEYWORDS = {
    "advice": ["should i buy", "should i sell", "should i invest", "worth buying", "worth investing",
               "good investment", "buy shares", "sell shares", "buy the stock", "share price", "stock price",
               "price target", "invest in", "recommend buying", "recommend selling"],
    "help": ["help", "what can you", "what can i ask", "how do i use", "examples", "options", "menu"],
    "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
    "thanks": ["thank", "thanks", "cheers"],
    "goodbye": ["bye", "goodbye", "exit", "quit"],
    "compare": ["compare", "comparison", "which company", "which has", "which had", "highest", "lowest",
                "biggest", "largest", "smallest", "best", "worst", "most", "least", "rank", "versus", " vs ",
                "who has", "who had", "all three", "all companies", " than ", "fastest", "slowest",
                "quickest"],
    "summary": ["summary", "summarise", "summarize", "overview", "health", "healthy", "how is", "how's", "how are",
                "doing", "performance", "tell me about", "overall"],
    "chart": ["chart", "graph", "plot", "visual", "visualise", "visualize", "visualisation",
              "visualization", "draw", "picture"],
    "trend": ["trend", "over time", "over the years", "over the last three", "three years", "3 years",
              "history", "since 2023", "2023 to 2025", "each year"],
    "change": ["change", "changed", "growth", "grow", "grew", "increase", "increased", "decrease",
               "decreased", "rise", "rose", "fall", "fell", "drop", "dropped", "up or down", "improve",
               "decline", "declined", "year on year", "year over year", "yoy"],
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _contains(text: str, phrase: str) -> bool:
    """Whole-word / whole-phrase match, so 'hi' does not match 'this'."""
    phrase = phrase.strip()
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def format_money(millions: float) -> str:
    """US$ millions -> '$281.7bn' (or '$950m' for small values)."""
    if abs(millions) >= 1000:
        return f"${millions / 1000:,.1f}bn"
    return f"${millions:,.0f}m"


def format_value(value: float, kind: str) -> str:
    return format_money(value) if kind == "money" else f"{value:.1f}%"


def describe_change(pct: float) -> str:
    if abs(pct) < 0.05:
        return "was unchanged"
    return f"{'rose' if pct > 0 else 'fell'} {abs(pct):.1f}%"


@dataclass
class Memory:
    """What the conversation is currently about, so follow-ups make sense."""
    companies: list[str] = field(default_factory=list)
    metric: str | None = None
    year: int | None = None
    intent: str | None = None


# --------------------------------------------------------------------------
# The chatbot
# --------------------------------------------------------------------------

class FinancialChatbot:
    def __init__(self, data_path: Path | str = DATA_PATH, suggestions: bool = True):
        self.suggestions = suggestions
        self.df = pd.read_csv(data_path).sort_values(["Company", "Fiscal Year"]).reset_index(drop=True)
        self.companies = sorted(self.df["Company"].unique())
        self.years = sorted(int(y) for y in self.df["Fiscal Year"].unique())
        self.latest_year = self.years[-1]
        self.memory = Memory()

    # ---------------- understanding the question ----------------

    def _find_companies(self, text: str) -> list[str]:
        found = [name for name, aliases in COMPANY_ALIASES.items()
                 if name in self.companies and any(_contains(text, a) for a in aliases)]
        if not found and any(_contains(text, p) for p in ["all three", "all companies", "each company", "every company"]):
            found = list(self.companies)
        return found

    def _find_out_of_scope_company(self, text: str) -> str | None:
        for name in OUT_OF_SCOPE_COMPANIES:
            if _contains(text, name):
                return name.title() if name not in {"ibm", "byd"} else name.upper()
        return None

    def _find_metric(self, text: str) -> str | None:
        candidates = [(len(k), key) for key, m in METRICS.items() for k in m["keywords"] if _contains(text, k)]
        return max(candidates)[1] if candidates else None

    def _find_year(self, text: str) -> int | None | str:
        match = re.search(r"\b(?:fy\s?)?(20\d{2})\b", text) or re.search(r"\bfy\s?(\d{2})\b", text)
        if match:
            year = int(match.group(1))
            year = year + 2000 if year < 100 else year
            return year if year in self.years else f"out_of_range:{year}"
        # "Last year" / "past year" = the most recent completed fiscal year in the data
        if any(_contains(text, p) for p in ["latest", "most recent", "this year", "current", "recent",
                                            "now", "last year", "past year", "last fiscal year"]):
            return self.latest_year
        if any(_contains(text, p) for p in ["previous year", "prior year", "year before"]):
            return self.latest_year - 1
        return None

    def _find_intent(self, text: str) -> str | None:
        for intent in ["advice", "help", "goodbye", "thanks", "chart", "compare", "trend", "change", "summary", "greeting"]:
            if any(_contains(text, k) if k.strip() == k else k in f" {text} " for k in INTENT_KEYWORDS[intent]):
                return intent
        return None

    # ---------------- looking up the data ----------------

    def _row(self, company: str, year: int) -> pd.Series:
        return self.df[(self.df["Company"] == company) & (self.df["Fiscal Year"] == year)].iloc[0]

    def _note(self, company: str, metric: str, year: int | None) -> str:
        note = CONTEXT_NOTES.get((company, metric, year)) or CONTEXT_NOTES.get((company, metric, None))
        return f"\n  Context: {note}" if note else ""

    # ---------------- building answers ----------------

    def _answer_value(self, company: str, metric: str, year: int) -> str:
        m = METRICS[metric]
        row = self._row(company, year)
        verb = "were" if m["label"].startswith("total") and m["label"].endswith("s") else "was"
        text = f"{company}'s {m['label']} in FY{year} {verb} {format_value(row[m['column']], m['kind'])}"
        if m["growth"] and pd.notna(row[m["growth"]]):
            text += f", which {describe_change(row[m['growth']])} on FY{year - 1}"
        text += "."
        if "meaning" in m:
            text += f" This measures {m['meaning']}."
        return text + self._note(company, metric, year)

    def _answer_change(self, company: str, metric: str, year: int) -> str:
        m = METRICS[metric]
        if year == self.years[0]:
            return (f"FY{year} is the first year in my data, so I can't calculate a change for it. "
                    f"Try asking about FY{year + 1} or FY{self.latest_year}.")
        now, before = self._row(company, year), self._row(company, year - 1)
        new, old = now[m["column"]], before[m["column"]]
        if m["kind"] == "percent":
            diff = new - old
            direction = "rose" if diff > 0 else "fell"
            text = (f"{company}'s {m['label']} {direction} from {old:.1f}% in FY{year - 1} "
                    f"to {new:.1f}% in FY{year}, a change of {diff:+.1f} percentage points.")
        else:
            pct = (new / old - 1) * 100
            text = (f"{company}'s {m['label']} {describe_change(pct)} in FY{year}, "
                    f"from {format_money(old)} to {format_money(new)}.")
        return text + self._note(company, metric, year)

    def _answer_trend(self, company: str, metric: str) -> str:
        m = METRICS[metric]
        data = self.df[self.df["Company"] == company]
        path = " → ".join(f"FY{int(r['Fiscal Year'])} {format_value(r[m['column']], m['kind'])}"
                          for _, r in data.iterrows())
        first, last = data[m["column"]].iloc[0], data[m["column"]].iloc[-1]
        if m["kind"] == "money":
            periods = len(data) - 1
            cagr = ((last / first) ** (1 / periods) - 1) * 100
            summary = f"That is an average change of {cagr:+.1f}% a year."
        else:
            summary = f"Overall, a change of {last - first:+.1f} percentage points."
        # One context note per company is enough for a trend: use the earliest relevant one
        notes = next((self._note(company, metric, int(y)) for y in data["Fiscal Year"]
                      if (company, metric, int(y)) in CONTEXT_NOTES), "")
        return f"{company}'s {m['label']}: {path}. {summary}" + (notes or self._note(company, metric, None))

    def _answer_growth_ranking(self, companies: list[str], metric: str, text: str) -> str:
        """'Which company grew revenue fastest?': rank by average annual growth, not size."""
        m = METRICS[metric]
        companies = companies if len(companies) >= 2 else list(self.companies)
        periods = len(self.years) - 1
        rows = []
        for c in companies:
            series = self.df[self.df["Company"] == c][m["column"]]
            cagr = ((series.iloc[-1] / series.iloc[0]) ** (1 / periods) - 1) * 100
            latest = self._row(c, self.latest_year)[m["growth"]]
            rows.append((c, cagr, latest))
        slowest = any(_contains(text, w) for w in ["slowest", "least", "lowest", "worst"])
        rows.sort(key=lambda r: r[1], reverse=not slowest)
        lines = [f"Average annual growth in {m['label']}, FY{self.years[0]} to FY{self.latest_year} "
                 f"({'slowest' if slowest else 'fastest'} first):"]
        lines += [f"  {i}. {c}: {g:+.1f}% a year (FY{self.latest_year}: {l:+.1f}%)"
                  for i, (c, g, l) in enumerate(rows, start=1)]
        top, top_growth = rows[0][0], rows[0][1]
        if slowest and top_growth < 0:
            lines.append(f"{top} performed weakest: its {m['label']} shrank over the period.")
        else:
            lines.append(f"{top} grew {'slowest' if slowest else 'fastest'}.")
        return "\n".join(lines)

    def _answer_compare(self, companies: list[str], metric: str, year: int, text: str) -> str:
        m = METRICS[metric]
        companies = companies if len(companies) >= 2 else list(self.companies)
        data = self.df[(self.df["Fiscal Year"] == year) & (self.df["Company"].isin(companies))]
        wants_low = any(_contains(text, w) for w in ["lowest", "smallest", "least", "worst"])
        ascending = wants_low if m["higher_is_better"] else not any(
            _contains(text, w) for w in ["highest", "most", "largest", "biggest"])
        ranked = data.sort_values(m["column"], ascending=ascending)
        lines = [f"  {i}. {r['Company']}: {format_value(r[m['column']], m['kind'])}"
                 for i, (_, r) in enumerate(ranked.iterrows(), start=1)]
        lead = ranked.iloc[0]["Company"]
        order = "lowest first" if ascending else "highest first"
        header = f"{m['label'].capitalize()} in FY{year} ({order}):"
        footer = f"{lead} has the {'lowest' if ascending else 'highest'} {m['label']}."
        if "meaning" in m:
            footer += f" ({m['label'].capitalize()} measures {m['meaning']}.)"
        elif not m["higher_is_better"]:
            footer += f" For {m['label']}, lower generally means a stronger position."
        return "\n".join([header, *lines, footer])

    def _answer_summary(self, company: str) -> str:
        latest = self._row(company, self.latest_year)
        first = self._row(company, self.years[0])
        periods = len(self.years) - 1
        rev_cagr = ((latest["Total Revenue"] / first["Total Revenue"]) ** (1 / periods) - 1) * 100
        lines = [
            f"{company}: financial health summary (FY{self.years[0]} to FY{self.latest_year})",
            f"  Verdict: {HEALTH_VERDICTS.get(company, 'See the figures below.')}",
            f"  Revenue: {format_money(latest['Total Revenue'])} in FY{self.latest_year} "
            f"(average change {rev_cagr:+.1f}% a year).",
            f"  Net income: {format_money(latest['Net Income'])}, a net margin of {latest['Net Margin (%)']:.1f}%.",
            f"  Operating cash flow: {format_money(latest['Cash Flow from Operating Activities'])} "
            f"({latest['OCF to Net Income (x)']:.1f}x net income).",
            f"  Leverage: liabilities fund {latest['Liabilities to Assets (%)']:.1f}% of assets.",
        ]
        return "\n".join(lines)

    def _answer_chart(self, companies: list[str], metric: str) -> str:
        """A text bar chart, so the visual works in any chat window, plus a pointer to the full chart."""
        m = METRICS[metric]
        companies = companies or list(self.companies)
        data = self.df[self.df["Company"].isin(companies)]
        peak = data[m["column"]].abs().max()
        width = 30
        lines = [f"{m['label'].capitalize()} by fiscal year (each block is about "
                 f"{format_value(peak / width, m['kind'])}):"]
        for company in companies:
            lines.append(f"  {company}")
            for _, r in data[data["Company"] == company].iterrows():
                value = r[m["column"]]
                bar = "█" * max(1, round(abs(value) / peak * width))
                lines.append(f"    FY{int(r['Fiscal Year'])} {bar} {format_value(value, m['kind'])}")
        first_last = []
        for company in companies:
            series = data[data["Company"] == company][m["column"]]
            direction = "up" if series.iloc[-1] > series.iloc[0] else "down"
            first_last.append(f"{company} {direction}")
        lines.append(f"Reading the chart: longer bars mean higher values. Over three years: {', '.join(first_last)}.")
        if metric in CHART_FILES:
            lines.append(f"A full line chart of this is saved in the project at {CHART_FILES[metric]}.")
        return "\n".join(lines)

    def _suggest(self, intent: str, companies: list[str], metric: str | None) -> str:
        """Suggest two natural next questions, to keep the conversation going."""
        company = companies[0] if companies else "Microsoft"
        other = next(c for c in self.companies if c != company)
        label = METRICS[metric]["label"] if metric else "net income"
        ideas = {
            "value": [f"How has {company}'s {label} changed?", f"Which company has the highest {label}?"],
            "change": [f"Show {company}'s {label} trend", f"What about {other}?"],
            "trend": [f"Show a chart of {label}", f"How healthy is {company}?"],
            "compare": [f"How healthy is {company}?", f"Show a chart of {label}"],
            "summary": [f"Show {company}'s net income trend", "Which company has the highest net margin?"],
            "chart": [f"Which company has the highest {label}?", f"How healthy is {company}?"],
        }.get(intent)
        return f"\n  You could also ask: \"{ideas[0]}\" or \"{ideas[1]}\"" if ideas else ""

    def _help(self) -> str:
        return (
            "I can answer questions about Microsoft, Tesla and Apple, using their 10-K filings "
            f"for FY{self.years[0]} to FY{self.latest_year}.\n"
            "  Metrics: revenue, net income, total assets, total liabilities, operating cash flow, "
            "net margin, leverage and shareholders' equity.\n"
            "  Try asking:\n"
            "  - What was Apple's revenue in 2025?\n"
            "  - How has Tesla's net income changed over the last year?\n"
            "  - Show Microsoft's operating cash flow trend\n"
            "  - Which company has the highest net margin?\n"
            "  - How healthy is Tesla?\n"
            "  - Show a chart of revenue\n"
            "  - What about Microsoft?  (follow-ups remember what we were discussing)\n"
            "  Note: I report figures from company filings. This is not investment advice."
        )

    # ---------------- main entry point ----------------

    def respond(self, message: str) -> str:
        text = " ".join(re.sub(r"[^\w\s'%-]", " ", message.lower()).split())
        if not text:
            return "Please type a question, or type 'help' to see what I can do."

        outside = self._find_out_of_scope_company(text)
        companies = self._find_companies(text)
        metric = self._find_metric(text)
        year = self._find_year(text)
        intent = self._find_intent(text)

        if intent == "help":
            return self._help()
        if intent == "advice":
            reply = ("I can't give investment advice or comment on share prices. I report historical figures "
                     "from company 10-K filings, which you may find useful alongside advice from a qualified "
                     "financial adviser.")
            if companies:
                reply += f"\n\nHere are the facts for {companies[0]}:\n" + self._answer_summary(companies[0])
                self.memory = Memory(companies=companies[:1], metric=None, year=self.latest_year, intent="summary")
            return reply
        if intent == "goodbye":
            return "Goodbye! Thanks for using the GFC Financial Chatbot."
        if intent == "thanks" and not (companies or metric):
            return "You're welcome. Ask me anything else about Microsoft, Tesla or Apple."
        if intent == "greeting" and not (companies or metric):
            return "Hello! I'm the GFC Financial Chatbot. Ask me about Microsoft, Tesla or Apple, or type 'help'."
        if outside and not companies:
            return (f"I don't have data for {outside}. I currently cover Microsoft, Tesla and Apple "
                    f"for FY{self.years[0]} to FY{self.latest_year}.")
        if isinstance(year, str):
            asked = year.split(":")[1]
            return (f"My data covers FY{self.years[0]} to FY{self.latest_year}, so I can't answer for {asked}. "
                    "I won't guess figures I haven't verified.")

        if intent in {"greeting", "thanks"}:
            intent = None

        # Nothing recognisable at all: say so rather than guess
        if not (companies or metric or year or intent):
            return ("Sorry, I didn't understand that. I answer questions about the financial performance "
                    "of Microsoft, Tesla and Apple. Type 'help' for examples.")

        # Follow-ups: a partial question ("what about Tesla?", "and in 2024?") borrows
        # whatever is missing from the previous turn. A complete question stands alone.
        follow_up_cue = any(text.startswith(c) for c in ["what about", "how about", "and ", "what of", "same for"])
        partial = not (companies and metric)
        is_follow_up = bool(self.memory.intent) and intent is None and (follow_up_cue or partial)

        if not companies and self.memory.companies and (is_follow_up or intent in {"change", "trend", "value"}):
            companies = self.memory.companies
        if not metric and intent != "summary" and (is_follow_up or intent):
            metric = self.memory.metric
        if year is None:
            year = self.memory.year if is_follow_up and self.memory.year else self.latest_year
        if intent is None:
            intent = self.memory.intent if is_follow_up else ("value" if metric else None)

        # Decide what to answer
        if intent == "summary" and companies and not (metric and not _contains(text, "health")):
            answer = "\n\n".join(self._answer_summary(c) for c in companies)
        elif intent == "summary" and not companies:
            answer = "\n\n".join(self._answer_summary(c) for c in self.companies)
        elif not metric:
            return ("I'm not sure which figure you mean. I can tell you about revenue, net income, assets, "
                    "liabilities, operating cash flow, net margin, leverage or equity. Type 'help' for examples.")
        elif intent == "chart":
            answer = self._answer_chart(companies, metric)
        elif intent in {"change", "trend"} and not companies:
            companies = list(self.companies)
            answer = "\n\n".join(self._answer_change(c, metric, year) if intent == "change"
                                  else self._answer_trend(c, metric) for c in companies)
        elif intent == "compare" and METRICS[metric]["growth"] and any(
                _contains(text, w) for w in ["grew", "grow", "growth", "fastest", "slowest", "quickest", "growing"]):
            answer = self._answer_growth_ranking(companies, metric, text)
        elif intent == "compare" or (len(companies) >= 2 and intent in {None, "value"}) or not companies:
            answer = self._answer_compare(companies, metric, year, text)
            intent = "compare"
        elif intent == "trend":
            answer = "\n\n".join(self._answer_trend(c, metric) for c in companies)
        elif intent == "change":
            answer = "\n\n".join(self._answer_change(c, metric, year) for c in companies)
        else:
            answer = "\n\n".join(self._answer_value(c, metric, year) for c in companies)
            intent = "value"

        self.memory = Memory(companies=companies, metric=metric, year=year, intent=intent)
        if self.suggestions:
            lead = self._leading_company(answer, companies)
            answer += self._suggest(intent, [lead] if lead else companies, metric)
        return answer

    def _leading_company(self, answer: str, companies: list[str]) -> str | None:
        """For rankings, suggest a follow-up about the company that came first."""
        match = re.search(r"\n  1\. (\w+):", answer)
        return match.group(1) if match else (companies[0] if companies else None)


# --------------------------------------------------------------------------
# Version 1: the simple predefined-query chatbot (Forage's baseline approach)
# --------------------------------------------------------------------------

def simple_chatbot(user_query: str, df: pd.DataFrame | None = None, company: str = "Microsoft") -> str:
    """
    The minimal rule-based approach: exact predefined questions mapped to answers
    with if/else logic. Kept to show where the project started; FinancialChatbot
    above is the improved version.
    """
    df = pd.read_csv(DATA_PATH) if df is None else df
    data = df[df["Company"] == company].sort_values("Fiscal Year")
    latest, previous = data.iloc[-1], data.iloc[-2]

    if user_query == "What is the total revenue?":
        return f"{company}'s total revenue in FY{latest['Fiscal Year']} was {format_money(latest['Total Revenue'])}."
    elif user_query == "How has net income changed over the last year?":
        change = (latest["Net Income"] / previous["Net Income"] - 1) * 100
        return f"{company}'s net income {describe_change(change)} in FY{latest['Fiscal Year']}."
    elif user_query == "What are the total assets?":
        return f"{company}'s total assets were {format_money(latest['Total Assets'])} at the end of FY{latest['Fiscal Year']}."
    elif user_query == "What are the total liabilities?":
        return f"{company}'s total liabilities were {format_money(latest['Total Liabilities'])} at the end of FY{latest['Fiscal Year']}."
    elif user_query == "What is the cash flow from operating activities?":
        return (f"{company}'s cash flow from operating activities in FY{latest['Fiscal Year']} was "
                f"{format_money(latest['Cash Flow from Operating Activities'])}.")
    else:
        return "Sorry, I can only provide information on predefined queries."


# --------------------------------------------------------------------------
# Command-line interface
# --------------------------------------------------------------------------

def main() -> None:
    bot = FinancialChatbot()
    print("GFC Financial Chatbot | Microsoft, Tesla and Apple | FY2023 to FY2025")
    print("Type 'help' for examples, or 'quit' to exit.\n")
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        reply = bot.respond(message)
        print(f"Bot: {reply}\n")
        if reply.startswith("Goodbye"):
            break


if __name__ == "__main__":
    main()
