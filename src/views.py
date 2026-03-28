import json

import os

from src.utils import (
    get_greeting,
    get_time_pr,
    read_excel_file_period,
    get_card_data,
    transactions_5_top,
    get_currency,
    get_stock_price,
)


def main_page(date_string: str) -> str:
    """
    Принимает на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS и возвращает JSON-ответ.
    """

    # Получаем приветствие в зависимости от времени суток
    greeting = get_greeting()
    time_pr = get_time_pr(date_string)
    srt_prd_date = read_excel_file_period("./data/operations.xlsx", time_pr)

    # Логика для получения данных по картам и транзакциям
    cards_data = get_card_data(srt_prd_date)  # Вызов функции для обработки карт
    top_transactions = transactions_5_top(srt_prd_date)  # Вызов функции для получения топ-5 транзакций
    currency_rates = get_currency()  # Вызов функции для получения курса валют
    stock_prices = get_stock_price()  # Вызов функции для получения стоимости акций

    # Формируем JSON-ответ
    data = {
        "greeting": greeting,
        "cards": cards_data,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }
    json_data = json.dumps(data, ensure_ascii=False, indent=4)

    return json_data
