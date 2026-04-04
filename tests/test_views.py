from unittest.mock import patch

import json

import pytest

from src.views import main_page


@patch("src.views.get_greeting")
@patch("src.views.get_time_pr")
@patch("src.views.read_excel_file_period")
@patch("src.views.get_currency")
@patch("src.views.get_stock_price")
@patch("src.views.transactions_5_top")
@patch("src.views.get_card_data")
@pytest.mark.parametrize(
    "date_string, expected_greeting",
    [
        ("2023-09-05 11:30:32", "Hello"),
        ("2020-12-06 23:00:58", "Good evening"),
    ],
)
def test_main_page(
    mock_get_card_data,
    mock_transactions_5_top,
    mock_get_stock_price,
    mock_get_currency,
    mock_read_excel_file_period,
    mock_get_time_pr,
    mock_get_greeting,
    date_string,
    expected_greeting,
):
    mock_get_greeting.return_value = expected_greeting
    mock_get_time_pr.return_value = "some_time"
    mock_read_excel_file_period.return_value = "some_data"
    mock_get_card_data.return_value = "card_data"
    mock_transactions_5_top.return_value = "top_transactions"
    mock_get_currency.return_value = "currency_rates"
    mock_get_stock_price.return_value = "stock_prices"

    result = main_page(date_string)
    parsed_result = json.loads(result)

    assert expected_greeting in result
    assert "cards" in parsed_result
    assert parsed_result["cards"] == "card_data"
    assert "top_transactions" in result
    assert "currency_rates" in result
    assert "stock_prices" in result

    # Проверить конкретные значения:
    assert "cards" in parsed_result
    assert parsed_result["cards"] == "card_data"
    assert "top_transactions" in parsed_result
    assert parsed_result["top_transactions"] == "top_transactions"
    assert "currency_rates" in parsed_result
    assert parsed_result["currency_rates"] == "currency_rates"
    assert "stock_prices" in parsed_result
    assert parsed_result["stock_prices"] == "stock_prices"


@patch("src.views.get_greeting")
@patch("src.views.get_time_pr")
@patch("src.views.read_excel_file_period")
@patch("src.views.get_currency")
@patch("src.views.get_stock_price")
@patch("src.views.transactions_5_top")
@patch("src.views.get_card_data")
def test_main_page_exception_handling(
    mock_get_card_data,
    mock_transactions_5_top,
    mock_get_stock_price,
    mock_get_currency,
    mock_read_excel_file_period,
    mock_get_time_pr,
    mock_get_greeting,
):

    mock_get_card_data.side_effect = Exception("Test exception")

    result = main_page("2021-09-05 11:30:32")

    assert result == "ошибка формирования ответа"
