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

**Period:** FY2022 to FY2024, the three most recent fiscal years with full 10-K filings at the time I collected the data.

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
3. Entered them into a tidy table: one row per company per year, one column per metric (`data/financial_data.csv`).
4. Cross-checked figures against the companies' own investor relations releases.

**Decisions and judgement calls:**
- **Different fiscal year ends.** Microsoft's year ends in June, Apple's in September and Tesla's in December. I kept a `Fiscal Year End` column so nobody mistakes these for calendar-year comparisons.
- **Tesla net income.** I used *net income attributable to common stockholders*, the headline figure in Tesla's 10-K, and noted this in the notebook.
- **Tidy ("long") format.** One row per company-year makes it trivial to filter, group and look up values, both for pandas and for the chatbot later.

---

## Step 2: Analysis in Python (Task 1)

Notebook: `notebooks/01_financial_analysis.ipynb`

1. **Data quality checks:** no missing values, three years per company, liabilities below assets in every row. Checking before analysing is a habit worth showing.
2. **Year-on-year growth:** `groupby("Company")` with `pct_change()` so each company's growth is calculated only against its own prior year.
3. **Ratios:**
   - Net profit margin (profitability)
   - Liabilities to assets (leverage)
   - Operating cash flow to net income (earnings quality)
4. **Three-year summary:** compound annual growth rate (CAGR) plus average ratios, one comparable row per company.
5. **Charts:** revenue, net income and net margin trends saved to `charts/`.
6. **Deliverable report:** `docs/Task1_Data_Analysis_Report.md`, written for Aisha as requested in her briefing email: executive summary, findings by company, comparative view, a financial health verdict for each company, implications for the chatbot, and limitations.
7. **Exports:** `data/financial_analysis.csv` for the chatbot and a four-sheet Excel workbook for business readers.

**Headline findings:**
- **Microsoft** has the strongest momentum: revenue up about 11% a year, net income up 21.8% in FY2024, highest margins (34 to 37%) and falling leverage.
- **Apple** is the largest by revenue but growth is flat and margins eased slightly. High liabilities reflect its buyback and dividend programme.
- **Tesla's** growth stalled in FY2024 (+0.9%) and net income halved, partly because FY2023 included a one-off tax benefit. Cash generation held up much better than reported profit.

---

## Step 3: Chatbot (Task 2)

*To be completed in the next stage.*

---

## Talking points for the interview

- **Why start with data quality?** In consulting, a confident wrong answer is worse than no answer. Validating the dataset first protects the client and the chatbot's credibility.
- **Why tidy data?** It decouples the data from the chatbot logic. Adding a fourth company or a new year means adding rows, not rewriting code.
- **Why ratios as well as raw numbers?** Raw figures favour big companies. Ratios such as margin and leverage let you compare Apple and Tesla fairly.
- **What would I do with more time?** Automate extraction through the SEC EDGAR XBRL API instead of manual entry, add quarterly 10-Q data, and add segment-level revenue.
