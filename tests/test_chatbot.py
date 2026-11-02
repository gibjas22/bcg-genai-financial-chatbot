"""
Automated tests for the GFC Financial Chatbot.

These check GFC's accuracy requirement: every answer must match the verified
10-K dataset, and the bot must decline rather than guess when it cannot answer.

Run with:  pytest -q
"""

import pandas as pd
import pytest

from chatbot.financial_chatbot import DATA_PATH, FinancialChatbot, format_money, simple_chatbot


@pytest.fixture
def bot():
    return FinancialChatbot()


@pytest.fixture(scope="module")
def data():
    return pd.read_csv(DATA_PATH)


# ---------- the dataset itself ----------

def test_dataset_covers_three_companies_and_three_years(data):
    assert sorted(data["Company"].unique()) == ["Apple", "Microsoft", "Tesla"]
    assert sorted(data["Fiscal Year"].unique()) == [2023, 2024, 2025]
    assert len(data) == 9


def test_formatting_in_billions():
    assert format_money(281724) == "$281.7bn"
    assert format_money(3794) == "$3.8bn"
    assert format_money(950) == "$950m"


# ---------- accuracy: values match the 10-K data ----------

@pytest.mark.parametrize("question, expected", [
    ("What was Apple's revenue in 2025?", "$416.2bn"),
    ("What was Microsoft's net income in FY2024?", "$88.1bn"),
    ("Tesla total assets 2025", "$137.8bn"),
    ("What are Apple's total liabilities in 2023?", "$290.4bn"),
    ("Microsoft operating cash flow 2025", "$136.2bn"),
    ("What is Tesla's net margin?", "4.0%"),
    ("What is Microsoft's shareholders equity?", "$343.5bn"),
])
def test_value_answers_match_dataset(bot, question, expected):
    assert expected in bot.respond(question)


def test_change_over_last_year_uses_latest_year(bot):
    reply = bot.respond("How has Tesla's net income changed over the last year?")
    assert "fell 46.5%" in reply and "FY2025" in reply


def test_change_for_first_year_is_declined(bot):
    assert "first year in my data" in bot.respond("How did Apple's revenue change in 2023?")


def test_trend_shows_all_three_years(bot):
    reply = bot.respond("Show Microsoft's revenue trend")
    assert all(f"FY{y}" in reply for y in (2023, 2024, 2025))
    assert "+15.3% a year" in reply


# ---------- comparisons ----------

def test_highest_net_margin_is_microsoft(bot):
    reply = bot.respond("Which company has the highest net margin?")
    assert reply.splitlines()[1].strip().startswith("1. Microsoft")


def test_least_leveraged_is_tesla(bot):
    reply = bot.respond("Which company is least leveraged?")
    assert reply.splitlines()[1].strip().startswith("1. Tesla")


def test_largest_revenue_is_apple(bot):
    reply = bot.respond("Which company had the most revenue in 2023?")
    assert reply.splitlines()[1].strip().startswith("1. Apple")


# ---------- conversation memory ----------

def test_follow_up_switches_company(bot):
    bot.respond("How has Tesla's net income changed over the last year?")
    reply = bot.respond("What about Microsoft?")
    assert reply.startswith("Microsoft's net income rose 15.5%")


def test_follow_up_switches_year(bot):
    bot.respond("What was Apple's revenue in 2025?")
    assert "FY2024" in bot.respond("And in 2024?")


def test_complete_question_is_not_treated_as_follow_up(bot):
    bot.respond("How has Tesla's net income changed over the last year?")
    reply = bot.respond("What is Apple's leverage?")
    assert reply.startswith("Apple's liabilities-to-assets ratio in FY2025 was 79.5%")


# ---------- context for one-off items ----------

def test_apple_tax_charge_is_explained(bot):
    assert "one-time income tax charge" in bot.respond("Apple net income 2024")


def test_tesla_tax_benefit_is_explained(bot):
    assert "one-off tax benefit" in bot.respond("Tesla net income trend")


# ---------- honesty: decline rather than guess ----------

def test_unknown_company_is_declined(bot):
    assert "don't have data for Amazon" in bot.respond("What is Amazon's revenue?")


def test_year_outside_data_is_declined(bot):
    assert "can't answer for 2019" in bot.respond("Microsoft revenue in 2019")


def test_off_topic_question_is_not_answered(bot):
    assert bot.respond("What is the weather?").startswith("Sorry, I didn't understand")


def test_empty_message(bot):
    assert "type a question" in bot.respond("   ")


# ---------- usability ----------

def test_help_lists_examples(bot):
    reply = bot.respond("help")
    assert "Try asking" in reply and "not investment advice" in reply


def test_health_summary_has_verdict(bot):
    reply = bot.respond("How healthy is Tesla?")
    assert "Verdict" in reply and "net margin of 4.0%" in reply


# ---------- version 1: predefined queries ----------

def test_simple_chatbot_predefined_queries():
    assert "$281.7bn" in simple_chatbot("What is the total revenue?")
    assert "rose 15.5%" in simple_chatbot("How has net income changed over the last year?")
    assert "predefined queries" in simple_chatbot("Something else")


# ---------- communicating insights: visuals and suggested follow-ups ----------

def test_chart_request_draws_text_bars(bot):
    reply = bot.respond("Show a chart of revenue")
    assert "█" in reply and "charts/revenue_trend.png" in reply
    assert "Apple up, Microsoft up, Tesla down" in reply


def test_answers_suggest_follow_up_questions(bot):
    assert "You could also ask" in bot.respond("What was Apple's revenue in 2025?")


def test_suggestions_follow_the_ranking_leader(bot):
    assert '"How healthy is Microsoft?"' in bot.respond("Which company has the highest net margin?")


def test_suggestions_can_be_switched_off():
    quiet = FinancialChatbot(suggestions=False)
    assert "You could also ask" not in quiet.respond("What was Apple's revenue in 2025?")
