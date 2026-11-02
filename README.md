# BCG GenAI Financial Chatbot

An AI-powered financial chatbot built for the **BCG GenAI Job Simulation on Forage**. It analyses 10-K data for Microsoft, Tesla and Apple and answers financial questions in plain English.

**Author:** Gibson Nyendwa, Junior Data Scientist (simulated role), BCG GenAI Consulting team

## The client problem

Global Finance Corp. (GFC) needs to analyse corporate financial performance faster than its traditional methods allow. It asked BCG for an AI-powered chatbot that reads 10-K and 10-Q data and explains it conversationally, built to four requirements: **efficiency, accuracy, a user-friendly interface and scalability**. See the [build log](docs/BUILD_LOG.md#how-the-build-meets-gfcs-requirements) for how each one is met.

## Project status

| Stage | What it covers | Status |
|---|---|---|
| Task 1 | Extract 10-K data and analyse trends in Python | Complete |
| Task 2 | Build the financial chatbot | In progress |

## Repository structure

```
bcg-genai-chatbot/
├── data/
│   ├── financial_data.csv                     # Raw figures extracted from 10-K filings
│   ├── financial_analysis.csv                 # Data with growth rates and ratios (chatbot input)
│   └── BCG_GenAI_Task1_Financial_Analysis.xlsx
├── notebooks/
│   └── 01_financial_analysis.ipynb            # Task 1 analysis
├── charts/                                    # Trend charts produced by the notebook
├── docs/
│   ├── BUILD_LOG.md                           # Step-by-step build process and decisions
│   └── DATA_DICTIONARY.md                     # Column definitions, formulas and data quality rules
└── requirements.txt
```

## Data

- **Source:** Form 10-K filings on SEC EDGAR
- **Companies:** Microsoft, Tesla, Apple
- **Years:** FY2022 to FY2024
- **Metrics:** Total Revenue, Net Income, Total Assets, Total Liabilities, Cash Flow from Operating Activities
- **Units:** US$ millions

## Run it yourself

```bash
pip install -r requirements.txt
jupyter notebook notebooks/01_financial_analysis.ipynb
```

## Key findings (Task 1)

- **Microsoft:** strongest growth (revenue CAGR about 11%) and the highest net margins, with leverage falling each year.
- **Apple:** largest revenue base, but flat growth and slightly lower margins.
- **Tesla:** revenue growth stalled in FY2024 and net income fell 52.7%, though operating cash flow held up.

See [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md) for the full build process.

## Disclaimer

Created as part of a Forage job simulation. Not an employment relationship with BCG, and not financial advice.
