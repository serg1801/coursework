import json

from datetime import datetime

import requests

import pandas as pd

import pytest

from src.utils import (
    get_card_data,
    get_currency,
    get_greeting,
    get_stock_price,
    get_time_pr,
    read_excel_file_period,
    transactions_5_top,
)

from unittest.mock import Mock, patch


@patch("pandas.read_excel")
def test_read_excel_file_period(mock_read_excel, sample_data):
    mock_read_excel.return_value = sample_data

    # Вызов функции с фиктивными параметрами
    path_excel_ = "fake_path.xlsx"
    time_period_ = ["01.01.2021 00:00:00", "02.01.2021 23:59:59"]
    result = read_excel_file_period(path_excel_, time_period_)

    # Проверка результата
    assert len(result) == 2  # Проверка, что получено 2 записи
    assert result[0]["Сумма"] == 100
    assert result[1]["Сумма"] == 200


@pytest.mark.parametrize(
    "time_period_, expected_count",
    [
        (["01.01.2021 00:00:00", "02.01.2021 23:59:59"], 2),
        (["01.01.2021 00:00:00", "01.01.2021 23:59:59"], 1),
        (["03.01.2021 00:00:00", "03.01.2021 23:59:59"], 0),
    ],
)
@patch("pandas.read_excel")
def test_read_excel_file_period_parametrized(mock_read_excel, sample_data, time_period_, expected_count):
    mock_read_excel.return_value = sample_data
    path_excel_ = "fake_path.xlsx"
    result = read_excel_file_period(path_excel_, time_period_)
    assert len(result) == expected_count


@patch("pandas.read_excel")
def test_read_excel_valueerror(mock_read_excel):
    # Настраиваем mock так, чтобы read_excel выбрасывал ValueError
    mock_read_excel.side_effect = ValueError("Ошибка при чтении файла Excel")

    path_excel_ = "fake_path.xlsx"
    time_period_ = ["01.01.2021 00:00:00", "02.01.2021 23:59:59"]

    with pytest.raises(ValueError, match="Ошибка при чтении файла Excel"):
        read_excel_file_period(path_excel_, time_period_)


@pytest.mark.parametrize(
    "mock_now, expected_greeting",
    [
        (datetime(2023, 1, 1, 6, 0), "Доброе утро"),  # Утро
        (datetime(2023, 1, 1, 12, 0), "Добрый день"),  # День
        (datetime(2023, 1, 1, 18, 0), "Добрый вечер"),  # Вечер
        (datetime(2023, 1, 1, 22, 0), "Доброй ночи"),  # Ночь
    ],
)
@patch("src.utils.datetime")  # Замена datetime в модуле
def test_get_greeting(mock_datetime, mock_now, expected_greeting):
    mock_datetime.now.return_value = mock_now
    assert get_greeting() == expected_greeting


@pytest.mark.parametrize(
    "date_string, date_frm, expected, should_raise",
    [
        # Корректность преобразования дат
        ("2023-10-15 14:30:00", "%Y-%m-%d %H:%M:%S", ["01.10.2023 00:00:00", "15.10.2023 14:30:00"], False),
        ("2022-02-28 23:59:59", "%Y-%m-%d %H:%M:%S", ["01.02.2022 00:00:00", "28.02.2022 23:59:59"], False),
        # Обработка различных форматов дат
        ("15-10-2023", "%d-%m-%Y", ["01.10.2023 00:00:00", "15.10.2023 00:00:00"], False),
        ("10/15/2023 14:30:00", "%m/%d/%Y %H:%M:%S", ["01.10.2023 00:00:00", "15.10.2023 14:30:00"], False),
        # Проверка на ошибки
        ("invalid-date", "%Y-%m-%d %H:%M:%S", None, True),
        ("2023-15-10 14:30:00", "%Y-%m-%d %H:%M:%S", None, True),
    ],
)
def test_get_time_pr(date_string, date_frm, expected, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            get_time_pr(date_string, date_frm)
    else:
        assert get_time_pr(date_string, date_frm) == expected


# Тесты функции get_card_data
@pytest.mark.parametrize(
    "expected",
    [
        [
            {"last_digits": "5814", "total_spent": 500.0, "cashback": 5.0},
            {"last_digits": "4321", "total_spent": 2000.0, "cashback": 20.0},
        ]
    ],
)
def test_get_card_data_with_fixture(transactions_fixture, expected):
    result = get_card_data(transactions_fixture)
    assert result == expected


@patch("src.utils.utils_logger.info")
def test_logging(mock_logger, transactions):
    # Проверка логирования
    transactions_5_top(transactions)
    mock_logger.assert_any_call("Начало обработки транзакций для топ-5.")
    mock_logger.assert_any_call("Топ-5 транзакций успешно обработаны.")


def test_top5(transactions):
    # Проверка корректного формирования top-5
    result = transactions_5_top(transactions)
    assert len(result) == 2  # У нас всего 2 валидных транзакции
    assert result[0]["amount"] == 3000.00
    assert result[0]["category"] == "Переводы"


def test_filter_by_card_number(transactions):
    # Проверка фильтрации по "Номер карты"
    result = transactions_5_top(transactions)
    assert not any(t["date"] == "2021-12-22" and t["amount"] == 2000.00 for t in result)


# Тесты функции get_currency
@patch("requests.get")
def test_get_currency(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"info": {"rate": 82.00}}
    mock_get.return_value = mock_response

    result = get_currency()
    assert result == [{"currency": "USD", "rate": 82.00}, {"currency": "EUR", "rate": 82.00}]


@pytest.mark.parametrize(
    "status_code, expected", [(500, "Server Error"), (404, "Client Error: 404"), (None, "No response received")]
)
@patch("requests.get")
def test_get_currency_errors(mock_get, status_code, expected):
    mock_response = Mock()
    if status_code is not None:
        mock_response.status_code = status_code
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.json.return_value = {"info": {"rate": 82.00}}
        mock_get.return_value = mock_response
    else:
        mock_response = Mock()
        mock_response.status_code = None
        mock_response.json.return_value = None
        mock_get.return_value = mock_response

    result = get_currency()
    assert result == expected


# Тесты функции get_stock_price
# Пример успешного ответа
mock_response_success = {
    "Meta Data": {"3. Last Refreshed": "2023-10-10"},
    "Time Series (Daily)": {"2023-10-10": {"4. close": "150.12"}},
}


@patch("requests.get")
def test_get_stock_price_success(mock_get):
    # Настроим мокнуть так, чтобы он возвращал одинаковые данные для всех компаний
    mock_get.return_value.json.return_value = mock_response_success
    mock_get.return_value.status_code = 200
    result = get_stock_price()

    # Ожидаемый результат для всех компаний
    expected_result = [
        {"stock": "AAPL", "price": 150.12},
        {"stock": "AMZN", "price": 150.12},
        {"stock": "GOOGL", "price": 150.12},
        {"stock": "MSFT", "price": 150.12},
        {"stock": "TSLA", "price": 150.12},
    ]

    assert result == expected_result


@pytest.mark.parametrize("status_code, expected", [
    (500, "Server Error"),
    (404, "Client Error: 404"),
])
@patch("requests.get")
def test_get_stock_price_errors(mock_get, status_code, expected):
    # Настроим mock, чтобы он возвращал указанный статус
    mock_get.return_value.status_code = status_code
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError

    result = get_stock_price()

    # Проверяем, что функция возвращает ожидаемое значение
    assert result == expected
