# GFC Financial Chatbot: Documentation

**BCG GenAI Job Simulation (Forage), Task 2**
**Author:** Gibson Nyendwa, Junior Data Scientist, GenAI Consulting Team
**Client:** Global Finance Corp. (GFC)

---

## 1. What it does

A prototype chatbot that answers questions about the financial performance of **Microsoft, Tesla and Apple** for **fiscal years 2023 to 2025**, using the figures extracted from their 10-K filings and analysed in Task 1 (`data/financial_analysis.csv`).

It comes in two versions:

| Version | Approach | Purpose |
|---|---|---|
| **v1: `simple_chatbot()`** | Exact predefined queries matched with `if`/`elif` statements, as in the task template | The required prototype |
| **v2: `FinancialChatbot`** | Rule-based understanding of company, year, metric and question type, with conversation memory | Shows how the same rule-based logic scales to natural questions |

Both read the same Task 1 dataset, so every answer comes from verified 10-K figures.

---

## 2. How it works

### Version 1: predefined queries
Each supported question is matched exactly and mapped to a response calculated from the data (the latest fiscal year for the chosen company, Microsoft by default):

| Predefined query | Response (Microsoft) |
|---|---|
| What is the total revenue? | Microsoft's total revenue in FY2025 was $281.7bn. |
| How has net income changed over the last year? | Microsoft's net income rose 15.5% in FY2025. |
| What are the total assets? | Microsoft's total assets were $619.0bn at the end of FY2025. |
| What are the total liabilities? | Microsoft's total liabilities were $275.5bn at the end of FY2025. |
| What is the cash flow from operating activities? | Microsoft's cash flow from operating activities in FY2025 was $136.2bn. |
| *Anything else* | Sorry, I can only provide information on predefined queries. |

Responses are calculated from the data rather than typed in, so they stay correct if the data is updated. Passing `company="Tesla"` or `company="Apple"` answers for another company.

### Version 2: rule-based pipeline
Every message passes through five steps:

1. **Normalise:** lower case, remove punctuation.
2. **Extract entities:** company (including tickers such as MSFT), fiscal year (including "FY25", "latest", "last year") and metric, using keyword dictionaries. "Profit", "earnings" and "bottom line" all map to net income.
3. **Classify intent:** value, change, trend, comparison, chart, health summary or help.
4. **State management:** a partial follow-up ("What about Tesla?", "And in 2024?") borrows what is missing from the previous question. A complete new question starts afresh.
5. **Respond:** retrieve the figure from the dataset, write a plain-English answer, add context for one-off items, and suggest two follow-up questions.

**Questions v2 can answer** (examples):

| Type | Example |
|---|---|
| Value | What was Apple's revenue in 2025? |
| Change | How has Tesla's net income changed over the last year? |
| Trend | Show Microsoft's operating cash flow trend |
| Comparison | Which company has the highest net margin? |
| Chart | Show a chart of revenue |
| Health summary | How healthy is Tesla? |
| Follow-up | What about Microsoft? / And in 2024? |
| Growth ranking | Which company grew revenue fastest? |
| Help | help |

**Metrics covered:** total revenue, net income, total assets, total liabilities, operating cash flow, net profit margin, liabilities-to-assets ratio and shareholders' equity.

**Error handling:** unrecognised questions get a polite message and a pointer to `help`. Companies or years outside the data are declined by name ("I don't have data for Amazon"), and the bot never guesses a figure.

---

## 3. How to run it

```bash
pip install -r requirements.txt

# Command line
python -m chatbot.financial_chatbot

# Web app (then open http://127.0.0.1:5000)
python -m chatbot.app

# Tests
pytest -q
```

---

## 4. Testing

- **37 automated tests** (`tests/test_chatbot.py`), all passing. Full output: `test_results.txt`.
- The tests cover: values against the 10-K data, changes, trends, comparisons, follow-up memory, context notes, refusals, help, charts, suggestions, all five v1 predefined queries, and the web app.
- A sample conversation is in `demo_conversation.txt`.
- **Live stress test:** 15 new, unscripted questions on a fresh copy from GitHub. Five weaknesses were found and fixed, each with a new test: "earn" as net income, "more profitable" as margin, "grew fastest" ranking by growth rather than size, and declining investment advice.
- **Bugs found and fixed during testing:** "over the last year" was first read as the wrong year; "least leveraged" was not recognised; an off-topic question reused the previous topic; a complete question was treated as a follow-up; trend answers repeated context notes.

---

## 5. Limitations

1. **v1 needs exact wording.** "What was Tesla's revenue?" is not a predefined query, so v1 declines it. v2 handles it.
2. **Keyword matching, not true language understanding.** Spelling mistakes, unusual phrasing or multi-part questions may not be understood. The bot says so rather than guessing.
3. **Limited data.** Three companies, three annual periods and eight metrics. No quarterly data, segments, share prices or forecasts.
4. **Context notes are hand-written** from the 10-K MD&A and results releases, and would need updating as new filings arrive.
5. **Prototype interface.** The web app is for demonstration only: no user accounts, and conversations are held in memory.
6. **Not investment advice.** It reports historical figures from company filings, and declines questions such as "Should I buy Tesla shares?", offering the facts instead.

---

## 6. Next steps

1. **NLP:** replace keyword dictionaries with a language model, keeping answers grounded in the verified data (retrieval-augmented generation).
2. **Machine learning:** log declined questions as training data to widen coverage.
3. **Data integration:** feed new 10-K and 10-Q filings automatically from the SEC EDGAR API.
4. **UX:** turn suggested follow-ups into buttons and chart requests into real charts.
