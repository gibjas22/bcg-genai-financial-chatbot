# Financial Data Analysis Report: Microsoft, Tesla and Apple

**Project:** AI-powered financial chatbot for Global Finance Corp. (GFC)
**To:** Aisha, Senior Data Scientist, GenAI Consulting Team
**From:** Gibson Nyendwa, Junior Data Scientist
**Task:** 1 of 2, Data extraction and initial analysis
**Source data:** Form 10-K filings, FY2022 to FY2024 (US$ millions unless stated)

---

## 1. Executive summary

I extracted five core financial metrics from the 10-K filings of Microsoft, Tesla and Apple for fiscal years 2022 to 2024, checked the data for quality, and analysed growth, profitability, leverage and cash generation. The cleaned dataset is ready for the chatbot.

**Headline view of financial health:**

| Company | Overall health | Direction | One-line verdict |
|---|---|---|---|
| **Microsoft** | Strong | Improving | Fastest growth, highest margins and falling leverage |
| **Apple** | Strong | Flat | Very large and highly cash-generative, but revenue and profit have plateaued |
| **Tesla** | Stable balance sheet, weaker profitability | Deteriorating | Growth stalled in FY2024 and net income more than halved, though cash flow held up |

**Three findings GFC's clients would care about most:**

1. **Microsoft is the standout performer.** Revenue grew 11.2% a year on average and net income jumped 21.8% in FY2024, while liabilities fell to 47.6% of assets.
2. **Apple's scale hides a growth problem.** At about $391bn, Apple's revenue is the largest of the three, but it is now 0.4% a year *lower* than in FY2022, and net income has fallen in each of the last two years.
3. **Tesla's profit fall is partly an accounting effect.** Net income dropped 52.7% in FY2024, but FY2023 included a one-off tax benefit of about $6.5bn. Operating cash flow actually rose 12.6% in FY2024.

---

## 2. Scope and method

**Companies:** Microsoft, Tesla and Apple. Together they cover three different business models: software and cloud, electric vehicles and energy, and consumer hardware and services.

**Metrics extracted:**

| Metric | Financial statement | Why it matters |
|---|---|---|
| Total Revenue | Income statement | Size and growth of the business |
| Net Income | Income statement | Bottom-line profitability |
| Total Assets | Balance sheet | Scale of resources |
| Total Liabilities | Balance sheet | Obligations and leverage |
| Cash Flow from Operating Activities | Cash flow statement | Whether profit turns into cash |

**Ratios calculated:**
- **Net margin** = Net Income ÷ Total Revenue (profitability)
- **Liabilities to assets** = Total Liabilities ÷ Total Assets (leverage)
- **Operating cash flow to net income** = Operating Cash Flow ÷ Net Income (earnings quality; above 1.0 means profit is backed by cash)

**Method:**
1. Figures were taken from each company's consolidated statements in its 10-K on SEC EDGAR and cross-checked against company investor releases.
2. Data was stored in a tidy table (one row per company per fiscal year) so it can be queried directly by the chatbot.
3. Quality checks were run before any analysis: no missing values, three years per company, and liabilities below assets in every row. All checks passed.
4. Growth rates, ratios and three-year compound annual growth rates (CAGR) were calculated in Python (pandas). The full workings are in `notebooks/01_financial_analysis.ipynb`.

**Note on fiscal years:** Microsoft's year ends on 30 June, Apple's in late September and Tesla's on 31 December. Comparisons are by each company's fiscal year, not by calendar year.

---

## 3. Findings by company

### 3.1 Microsoft: strong and improving

| Metric | FY2022 | FY2023 | FY2024 | FY2024 change |
|---|---:|---:|---:|---:|
| Total Revenue | 198,270 | 211,915 | 245,122 | +15.7% |
| Net Income | 72,738 | 72,361 | 88,136 | +21.8% |
| Total Assets | 364,840 | 411,976 | 512,163 | +24.3% |
| Total Liabilities | 198,298 | 205,753 | 243,686 | +18.4% |
| Operating Cash Flow | 89,035 | 87,582 | 118,548 | +35.4% |
| Net Margin | 36.7% | 34.1% | 36.0% | |
| Liabilities to Assets | 54.4% | 49.9% | 47.6% | |

- **Growth is accelerating.** Revenue growth rose from 6.9% in FY2023 to 15.7% in FY2024, giving a three-year CAGR of 11.2%.
- **Profitability is the best of the three.** Net margin averaged 35.6%. After a flat FY2023, net income jumped 21.8% in FY2024.
- **The balance sheet expanded sharply but stayed conservative.** Total assets grew 24.3% in FY2024, mainly because of the Activision Blizzard acquisition (goodwill rose from $67.9bn to $119.2bn). Even so, liabilities fell as a share of assets in every year.
- **Profit is well backed by cash.** Operating cash flow was 1.35 times net income in FY2024 and grew 35.4%.

**Health assessment:** Strong and improving on every dimension measured.

### 3.2 Apple: strong but plateauing

| Metric | FY2022 | FY2023 | FY2024 | FY2024 change |
|---|---:|---:|---:|---:|
| Total Revenue | 394,328 | 383,285 | 391,035 | +2.0% |
| Net Income | 99,803 | 96,995 | 93,736 | −3.4% |
| Total Assets | 352,755 | 352,583 | 364,980 | +3.5% |
| Total Liabilities | 302,083 | 290,437 | 308,030 | +6.1% |
| Operating Cash Flow | 122,151 | 110,543 | 118,254 | +7.0% |
| Net Margin | 25.3% | 25.3% | 24.0% | |
| Liabilities to Assets | 85.6% | 82.4% | 84.4% | |

- **Revenue has stalled.** Revenue fell 2.8% in FY2023 and recovered only 2.0% in FY2024. Over three years it is down slightly (CAGR −0.4%).
- **Profit is drifting down.** Net income fell in both years, and net margin slipped from 25.3% to 24.0%, although it remains healthy.
- **Leverage looks high but is a deliberate choice.** Liabilities fund around 84% of assets, the highest of the three. This reflects Apple returning large amounts of cash to shareholders through buybacks and dividends, which shrinks equity, rather than financial distress.
- **Cash generation remains excellent.** Operating cash flow of $118.3bn was 1.26 times net income in FY2024.

**Health assessment:** Strong, with exceptional cash generation, but growth has plateaued.

### 3.3 Tesla: stable balance sheet, weakening profitability

| Metric | FY2022 | FY2023 | FY2024 | FY2024 change |
|---|---:|---:|---:|---:|
| Total Revenue | 81,462 | 96,773 | 97,690 | +0.9% |
| Net Income | 12,556 | 14,997 | 7,091 | −52.7% |
| Total Assets | 82,338 | 106,618 | 122,070 | +14.5% |
| Total Liabilities | 36,440 | 43,009 | 48,390 | +12.5% |
| Operating Cash Flow | 14,724 | 13,256 | 14,923 | +12.6% |
| Net Margin | 15.4% | 15.5% | 7.3% | |
| Liabilities to Assets | 44.3% | 40.3% | 39.6% | |

- **Growth has stalled.** Revenue rose 18.8% in FY2023 but only 0.9% in FY2024.
- **Net income more than halved.** It fell from $15.0bn to $7.1bn and net margin dropped from 15.5% to 7.3%. Two factors drive this: FY2023 profit was boosted by a one-off tax benefit of about $6.5bn (the release of a valuation allowance on deferred tax assets), and lower vehicle prices squeezed margins in FY2024.
- **Cash flow tells a better story than profit.** Operating cash flow rose 12.6% to $14.9bn, more than twice net income (2.1x). The underlying business is still generating cash.
- **Lowest leverage of the three.** Liabilities funded only 39.6% of assets in FY2024, down from 44.3% in FY2022.

**Health assessment:** The balance sheet is solid and cash generation is steady, but profitability has weakened and growth has stalled. This is the company to watch.

---

## 4. Comparative view

| Measure (FY2022 to FY2024) | Microsoft | Apple | Tesla |
|---|---:|---:|---:|
| Revenue CAGR | **11.2%** | −0.4% | 9.5% |
| Net income CAGR | **10.1%** | −3.1% | −24.8% |
| Average net margin | **35.6%** | 24.9% | 12.7% |
| Latest liabilities to assets | 47.6% | 84.4% | **39.6%** |
| Average operating cash flow ÷ net income | 1.26x | 1.21x | **1.39x** |

**Bold** = strongest of the three on that measure.

![Revenue trend](../charts/revenue_trend.png)
![Net income trend](../charts/net_income_trend.png)
![Net margin trend](../charts/net_margin_trend.png)

**Key takeaways:**
- **Growth:** Microsoft leads clearly. Tesla's three-year figure looks healthy, but it came almost entirely in FY2023.
- **Profitability:** Microsoft keeps more than a third of every dollar of revenue as profit. Tesla now keeps about seven cents.
- **Financial position:** Tesla is the least leveraged and Apple the most, though Apple's leverage is a choice made possible by its very strong cash flow.
- **Earnings quality:** All three generate more operating cash than reported profit on average, which is a positive sign for each.

---

## 5. Implications for the GFC chatbot

1. **The data is ready to use.** It is complete, consistent and stored in a tidy format, so the chatbot can look up any metric by company and year and compare it with the prior year.
2. **Ratios make the answers more useful.** Raw numbers favour the largest company. Including margin, leverage and cash quality lets the chatbot compare companies of very different sizes fairly.
3. **Context matters for accuracy.** Tesla's FY2024 profit fall shows why the chatbot should add context to its answers rather than only report numbers. A user who sees "net income fell 52.7%" without the one-off tax benefit explained could draw the wrong conclusion.
4. **Plain-English explanations meet GFC's usability requirement.** Each ratio has a simple one-line meaning (for example, "profit kept from each dollar of sales") that the chatbot can include in its answers.

---

## 6. Limitations and next steps

**Limitations:**
- Three years of annual data show direction, but not seasonality or quarter-to-quarter changes.
- Figures were extracted by hand, which works at this scale but would not scale to hundreds of companies.
- The analysis uses headline totals only, not segment or product-level detail.

**Recommended next steps:**
1. Automate extraction through the SEC EDGAR XBRL API, so new filings flow in without manual work (supports GFC's scalability requirement).
2. Add quarterly 10-Q data for more timely insights.
3. Add segment data (for example, Microsoft Cloud, iPhone, Tesla Energy) so the chatbot can explain *why* results changed.
4. Build the chatbot (Task 2) on top of this dataset.

---

**Supporting files**

| File | Contents |
|---|---|
| `data/financial_data.csv` | Raw extracted figures |
| `data/financial_analysis.csv` | Figures plus growth rates and ratios (chatbot input) |
| `data/BCG_GenAI_Task1_Financial_Analysis.xlsx` | Four-sheet workbook: raw data, growth, ratios, summary |
| `notebooks/01_financial_analysis.ipynb` | Full Python workings |
| `docs/DATA_DICTIONARY.md` | Column definitions, formulas and quality rules |
