# Build Log: How I Built the BCG GenAI Financial Chatbot

This log records each step of the project, the decisions I made and why. It is written so an interview panel can follow my thinking from raw 10-K filings to a working chatbot.

---

## Step 0: Understanding the brief

**My role.** Junior data scientist in BCG's GenAI Consulting team, working under Aisha (Senior Data Scientist and team lead).

**The client.** Global Finance Corp. (GFC), a leading global financial institution. Its traditional financial analysis is reliable but slow, and it struggles to keep pace with growing data volumes and fast-moving markets. GFC wants an AI-driven tool that quickly analyses and interprets 10-K and 10-Q reports, and it plans to roll the solution out in the upcoming financial quarter.

**The deliverable.** An AI-powered chatbot that analyses corporate financial performance from 10-K and 10-Q filings and explains it through conversation, so that GFC's clients can get insights regardless of their financial expertise.

**Two tasks:**
1. Extract and analyse key financial data from 10-K and 10-Q filings.
2. Use that analysis to build the financial chatbot.

**How I framed it.** A chatbot is only as reliable as the data behind it. So I treated Task 1 as building a trustworthy, well-structured "single source of truth", and Task 2 as the conversational layer on top.

### How the build meets GFC's requirements

| GFC requirement | What it means | How this project meets it |
|---|---|---|
| **Efficiency** | Cut the time taken to analyse financial documents | Figures are extracted once into a structured dataset. Growth rates and ratios are calculated automatically in seconds, and the chatbot returns an answer instantly instead of an analyst reading a 100-page filing. |
| **Accuracy** | Precise, reliable insights backed by thorough analysis | Every figure is traced to a named 10-K statement and cross-checked against company releases. The notebook runs data quality checks before any analysis. The chatbot answers only from verified data and says so when it does not know, rather than guessing. |
| **User-friendly interface** | Intuitive for clients of any financial expertise | Plain-English questions in, plain-English answers out. Ratios come with a one-line explanation of what they mean, so a non-specialist can follow the insight. |
| **Scalability** | Handle more documents and more queries | Tidy data format (one row per company per year) means adding a company, a year or quarterly 10-Q data is a matter of adding rows, not rewriting code. The extraction step can later be automated through the SEC EDGAR XBRL API. |

---

## Step 1: Data extraction (Task 1)

**Companies:** Microsoft, Tesla, Apple. Three very different business models (software and cloud, electric vehicles and energy, consumer hardware and services) give the chatbot a useful range of stories to tell.

**Period:** FY2023 to FY2025, as specified in the Forage task instructions.

> **Course correction.** My first version used FY2022 to FY2024, because I built it before reading the full task instructions. When the instructions specified 2023 to 2025, I extracted the FY2025 figures, dropped FY2022 and re-ran the whole analysis. The tidy data structure meant this took minutes and needed no code changes to the analysis logic, which is a practical demonstration of the scalability requirement.

**Metrics chosen and why:**

| Metric | Statement | Why it matters |
|---|---|---|
| Total Revenue | Income statement | Size and growth of the business |
| Net Income | Income statement | Bottom-line profitability |
| Total Assets | Balance sheet | Scale of resources owned |
| Total Liabilities | Balance sheet | Obligations and leverage |
| Cash Flow from Operating Activities | Cash flow statement | Whether profit turns into real cash |

These five cover all three core financial statements, so the chatbot can answer questions about growth, profitability, financial position and cash generation.

**Process:**
1. Located each company's 10-K on SEC EDGAR.
2. Read the figures from the consolidated statements (US$ millions).
3. Compiled them into an Excel spreadsheet (`data/financial_data.xlsx`), as the task instructions specify, in a tidy layout: one row per company per year, one column per metric.
4. Converted the spreadsheet to CSV (`data/financial_data.csv`) inside the notebook, then loaded it with pandas.
5. Cross-checked FY2025 figures against primary sources: Tesla's Q4 2025 results exhibit filed with the SEC, Apple's FY2025 consolidated statements and Microsoft's FY2025 investor relations statements.

**Decisions and judgement calls:**
- **Different fiscal year ends.** Microsoft's year ends in June, Apple's in September and Tesla's in December. I kept a `Fiscal Year End` column so nobody mistakes these for calendar-year comparisons.
- **Tesla net income.** I used *net income attributable to common stockholders*, the headline figure in Tesla's 10-K, and noted this in the notebook.
- **Tidy ("long") format.** One row per company-year makes it trivial to filter, group and look up values, both for pandas and for the chatbot later.

---

## Step 2: Analysis in Python (Task 1)

Notebook: `notebooks/01_financial_analysis.ipynb`

1. **Data quality checks:** no missing values, no duplicates, numeric data types, three years per company, liabilities below assets in every row. Checking before analysing is a habit worth showing.
2. **Year-on-year growth:** `groupby('Company')` with `pct_change()`, using the exact column names from the task instructions (`Revenue Growth (%)`, `Net Income Growth (%)`), so each company's growth is calculated only against its own prior year.
3. **Aggregates:** averages by company, totals by fiscal year, pivot tables, and each company's share of combined net income, to look at the data along different dimensions as the instructions suggest.
4. **Ratios:**
   - Net profit margin (profitability)
   - Liabilities to assets (leverage)
   - Operating cash flow to net income (earnings quality)
   - Shareholders' equity (assets minus liabilities)
5. **Three-year summary:** compound annual growth rate (CAGR) plus average ratios, one comparable row per company.
6. **Charts:** revenue, net income, net margin and operating cash flow trends saved to `charts/`.
7. **AI-ready preprocessing:** duplicate and data type checks, lag features (prior-year values) for time-series work, one-hot encoding of the company name, and a documented decision to keep nominal US$ figures for traceability. Exported as `data/financial_features_ml.csv`.
8. **Findings in the notebook:** markdown cells document the methodology, observations after each step, and conclusions, as the submission instructions require.
9. **Deliverable report:** `docs/Task1_Data_Analysis_Report.md`, written for Aisha as requested in her briefing email: executive summary, findings by company, comparative view, a financial health verdict for each company, implications for the chatbot, and limitations.
10. **Exports:** `data/financial_analysis.csv` for the chatbot and a four-sheet Excel workbook for business readers.
11. **Submission:** the notebook exported as HTML (`notebooks/BCG_GenAI_Task1_Gibson_Nyendwa.html`) for upload to Forage.

**Headline findings:**
- **Microsoft** is the strongest performer: revenue up 15.3% a year, net income up 18.6% a year to $101.8bn, the highest margins (36.1% in FY2025) and falling leverage.
- **Apple** is the largest by revenue and growth has returned (+6.4% in FY2025). Its FY2024 profit dip came from a one-time tax charge of about $10.2bn, and net income hit a record $112.0bn in FY2025.
- **Tesla's** revenue fell 2.9% in FY2025 and net income dropped from $15.0bn to $3.8bn over two years (FY2023 was flattered by a one-off tax benefit). Operating cash flow held steady at about $14.7bn, nearly four times FY2025 profit.

### Reflection: comparing my work with BCG's example answer

After submitting, Forage showed a model answer. It loads the spreadsheet, calculates revenue and net income growth with `groupby` and `pct_change`, fills missing values with `fillna(0)`, and averages growth by company.

**What I did differently, and why:**
- **I did not fill first-year growth with 0.** Each company's first year has no prior year, so its growth is genuinely unknown. Filling it with 0% adds a fake "no growth" year that drags averages down: Microsoft's average revenue growth would show about 10.2% instead of 15.3%. Leaving the cells as NaN lets pandas skip them, so the averages stay correct.
- **I sorted by company and year before `pct_change`.** The example only works if rows happen to be in year order. Sorting first makes the calculation reliable whatever order the data arrives in.
- **I checked data quality first** and analysed all five metrics, ratios and three-year CAGR, not just two growth rates.

**What I would take from the example:** it is short and answers the question in a few lines. In a client setting, I would lead with the three headline findings and keep the detailed workings in an appendix.

---

## Step 3: Chatbot (Task 2)

**Forage brief:** develop an AI chatbot that analyses financial data and provides insights, integrate the Task 1 data, and test that it communicates performance insights and comparisons effectively.

### Version 1: predefined queries
I started with the simplest possible approach: exact questions mapped to answers with `if`/`elif` logic (`simple_chatbot` in `chatbot/financial_chatbot.py`). It answers five fixed questions about one company and the latest year.

**What I learned from it:** it works, but "What was Tesla's revenue?" fails because the wording is not an exact match. For GFC's diverse client base, that is not user-friendly enough.

### Version 2: the GFC Financial Chatbot
A rule-based natural language understanding pipeline (`FinancialChatbot`):
1. **Normalise** the message (lower case, strip punctuation).
2. **Extract entities**: company (including tickers such as MSFT), fiscal year (including "FY25", "latest", "last year") and metric (synonym dictionaries, longest phrase wins, so "liabilities to assets" beats "liabilities").
3. **Classify intent**: value, change, trend, comparison, health summary, help.
4. **Conversation memory**: a partial question ("What about Microsoft?", "And in 2024?") borrows what is missing from the previous turn. A complete new question stands alone.
5. **Answer** from the verified dataset in plain English, with figures in billions, ratios explained, and context notes for one-off items (Tesla's FY2023 tax benefit, Apple's FY2024 tax charge, Microsoft's Activision acquisition).

**Communicating insights** (added after reading Forage's guidance on this):
- **Simplification:** figures in billions, one-line plain-English meanings for ratios, and health summaries with a verdict.
- **Interactive dialogue:** every answer suggests two related follow-up questions; after a ranking, the suggestion is about the company that came first.
- **Visual aids:** "Show a chart of revenue" draws a text bar chart in the chat, explains how to read it, and points to the saved line chart.

**Data integration:** the bot reads `data/financial_analysis.csv` from Task 1 directly. Companies and years come from the file, so new data needs no code changes.

### Testing
- 31 automated tests (`tests/test_chatbot.py`, run with `pytest -q`) check values against the dataset, changes, trends, comparisons, follow-ups, context notes, and that the bot declines questions it cannot answer.
- **Bugs the tests and trial conversations caught before release:**
  - "Over the last year" was first read as FY2024 instead of the latest year.
  - "Least leveraged" was not recognised until I added "leveraged" as a keyword.
  - An off-topic question reused the previous topic instead of saying it did not understand.
  - A complete new question was wrongly treated as a follow-up.
  - Trend answers repeated context notes; now limited to one per company.

### Demonstration
`notebooks/02_financial_chatbot.ipynb` (exported as `BCG_GenAI_Task2_Gibson_Nyendwa.html`) walks through both versions, a sample client conversation, refusals, the help text, the test results, limitations and next steps.

### Talking points
- **Why rule-based rather than an LLM?** For a financial client, accuracy comes first. A rule-based bot can only state verified figures. The recommended next step is an LLM layer for flexible phrasing, grounded in the same verified data (retrieval-augmented generation), so it cannot invent numbers.
- **Why decline rather than guess?** A confident wrong figure would damage GFC's trust with its clients. "I don't have data for that" is the safer answer.
- **Why context notes?** "Tesla's net income fell 52.7%" without the one-off tax benefit explained could lead a client to the wrong conclusion.

---

## Talking points for the interview

- **Why start with data quality?** In consulting, a confident wrong answer is worse than no answer. Validating the dataset first protects the client and the chatbot's credibility.
- **Why tidy data?** It decouples the data from the chatbot logic. Adding a fourth company or a new year means adding rows, not rewriting code.
- **Why ratios as well as raw numbers?** Raw figures favour big companies. Ratios such as margin and leverage let you compare Apple and Tesla fairly.
- **What would I do with more time?** Automate extraction through the SEC EDGAR XBRL API instead of manual entry, add quarterly 10-Q data, and add segment-level revenue.
