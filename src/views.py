import json


from src.utils import (
    get_card_data,
    get_currency,
    get_greeting,
    get_stock_price,
    get_time_pr,
    read_excel_file_period,
    transactions_5_top,
)

from src.logging_config import setup_logging

views_logger = setup_logging("views")


def main_page(date_string: str) -> str:
    """
    Принимает на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS и возвращает JSON-ответ.
    """
    try:
        views_logger.info("получение и формирование json-ответа")
        greeting = get_greeting()
        time_pr = get_time_pr(date_string)
        srt_prd_date = read_excel_file_period("./data/operations.xlsx", time_pr)
        cards_data = get_card_data(srt_prd_date)
        top_transactions = transactions_5_top(srt_prd_date)
        currency_rates = get_currency()
        stock_prices = get_stock_price()

        data = {
            "greeting": greeting,
            "cards": cards_data,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }
        json_data = json.dumps(data, ensure_ascii=False, indent=4)

        views_logger.info("успешно сформирован ответ")
        return json_data


    except Exception as e:

        views_logger.error(f"Произошла ошибка формирования JSON: {e}")

        return "ошибка формирования ответа"
