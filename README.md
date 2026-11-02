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
│   ├── financial_data.xlsx                    # Extracted 10-K figures (original spreadsheet)
│   ├── financial_data.csv                     # Raw figures extracted from 10-K filings
│   ├── financial_analysis.csv                 # Data with growth rates and ratios (chatbot input)
│   ├── financial_features_ml.csv              # Adds lag features and encoded company (ML ready)
│   └── BCG_GenAI_Task1_Financial_Analysis.xlsx  # Analysis workbook: raw data, growth, ratios, summary
├── notebooks/
│   ├── 01_financial_analysis.ipynb            # Task 1 analysis
│   └── BCG_GenAI_Task1_Gibson_Nyendwa.html    # Notebook exported for Forage submission
├── charts/                                    # Trend charts produced by the notebook
├── docs/
│   ├── Task1_Data_Analysis_Report.md          # Task 1 deliverable: findings and financial health summary
│   ├── BUILD_LOG.md                           # Step-by-step build process and decisions
│   └── DATA_DICTIONARY.md                     # Column definitions, formulas and data quality rules
└── requirements.txt
```

## Data

- **Source:** Form 10-K filings on SEC EDGAR
- **Companies:** Microsoft, Tesla, Apple
- **Years:** FY2023 to FY2025
- **Metrics:** Total Revenue, Net Income, Total Assets, Total Liabilities, Cash Flow from Operating Activities
- **Units:** US$ millions

## Run it yourself

```bash
pip install -r requirements.txt
jupyter notebook notebooks/01_financial_analysis.ipynb
```

## Key findings (Task 1)

- **Microsoft:** strongest performer, with revenue up 15.3% a year, net income up 18.6% a year and the highest margins, while leverage fell each year.
- **Apple:** largest revenue base, with growth returning and record net income of $112.0bn in FY2025 after a one-off tax charge in FY2024.
- **Tesla:** revenue fell in FY2025 and net income dropped from $15.0bn to $3.8bn over two years, though operating cash flow held steady.

Read the full **[Task 1 Data Analysis Report](docs/Task1_Data_Analysis_Report.md)** for findings and a financial health summary, and [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md) for the build process.

## Disclaimer

Created as part of a Forage job simulation. Not an employment relationship with BCG, and not financial advice.
