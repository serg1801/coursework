import os

import json

from datetime import datetime

from typing import Any, Hashable

import pandas as pd

import requests

from dotenv import load_dotenv
from pandas import DataFrame

from src.logging_config import setup_logging

utils_logger = setup_logging("utils")

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_ = os.getenv("API_KEY_")


def read_excel_file_period(path_excel_, time_period_):
    """
     Функция для считывания финансовых операций из Excel-файла за период. Принимает путь к файлу Excel, список из даты
    начала и окончания периода обработки данных. Возвращает список словарей.
    """
    utils_logger.info("Начало чтения файла Excel.")
    try:
        df_exl = pd.read_excel(path_excel_)
        df_exl["Дата операции"] = pd.to_datetime(df_exl["Дата операции"], dayfirst=True)
        start_date = datetime.strptime(time_period_[0], "%d.%m.%Y %H:%M:%S")
        end_date = datetime.strptime(time_period_[1], "%d.%m.%Y %H:%M:%S")
        flt_df_exl = df_exl[(df_exl["Дата операции"] >= start_date) & (df_exl["Дата операции"] <= end_date)]
        srt_df_exl = flt_df_exl.sort_values(by="Дата операции", ascending=True)
        srt_df_exl_lst = srt_df_exl.to_dict(orient="records")
        utils_logger.info("Список операций успешно создан.")
    except ValueError as e:
        utils_logger.error(f"Ошибка при чтении файла Excel: {e}")
        raise ValueError(f"Ошибка при чтении файла Excel: {e}")
    return srt_df_exl_lst


def get_greeting() -> str:
    """
     Функция для определения времени суток, принимает аргумент, который должен быть объектом datetime,
    содержащим текущее время. Возвращает строку с определением времени суток.
    """
    current_time_ = datetime.now().hour
    if 5 <= current_time_ < 12:
        greeting = "Доброе утро"
    elif 12 <= current_time_ < 18:
        greeting = "Добрый день"
    elif 18 <= current_time_ < 22:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"
    utils_logger.info(f"Определено время суток: {greeting}")
    return greeting


def get_time_pr(date_string: str, date_frm: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """
    Принимает строку с датой и форматом преобразования строки. Возвращает список строк из начала и конца периода
    """
    dt = datetime.strptime(date_string, date_frm)
    beginning_of_period = dt.replace(day=1, hour=0, minute=0, second=0)
    period = [beginning_of_period.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]
    utils_logger.info(f"Период времени получен: {period}")
    return period


def get_card_data(transaction_lst):
    """
      Принимает список словарей, и отдает список словарей с данными транзакций из карт,
     по типу: "cards":
     [{"last_digits": "5814",
     "total_spent": 1262.00,
     "cashback": 12.62}]
    "cashback" == кешбэк (1 рубль на каждые 100 рублей)
    """
    utils_logger.info("Начало обработки транзакций.")
    # Создаем DataFrame из списка транзакций
    df = pd.DataFrame(transaction_lst)
    # Убираем записи с некорректными номерами карт
    df = df[df["Номер карты"].notna()]

    # Добавляем столбец с последними 4 цифрами карты
    df["last_digits"] = df["Номер карты"].apply(lambda x: str(x)[-4:])

    # Преобразуем "Сумма операции" в числовой формат, убираем строки с некорректными значениями
    df["Сумма операции"] = pd.to_numeric(df["Сумма операции"], errors="coerce")
    df = df.dropna(subset=["Сумма операции"])

    # Фильтруем только успешные транзакции
    df = df[df["Статус"] == "OK"]

    # Создаем словарь для хранения данных по картам
    card_spent = {}
    for ind, row in df.iterrows():
        if row["last_digits"] not in card_spent:
            card_spent[row["last_digits"]] = {"total_spent": 0, "cashback": 0}

        # Считаем total_spent и cashback
        total_spent = row["Сумма операции"]
        cashback = total_spent / 100

        # Обновляем данные в словаре
        card_spent[row["last_digits"]]["total_spent"] += total_spent
        card_spent[row["last_digits"]]["cashback"] += cashback

    # Преобразуем результат в список словарей
    cards = [
        {"last_digits": card, "total_spent": round(values["total_spent"], 2), "cashback": round(values["cashback"], 2)}
        for card, values in card_spent.items()
    ]
    utils_logger.info("Обработка транзакций завершена.")
    return cards


def transactions_5_top(transaction_lst_: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
     Принимает список словарей транзакций. Формирует список Топ-5 транзакций по сумме платежа.
    Отдает данные по типу:
             [{"date": "21.12.2021",
            "amount": 1198.23,
         "category": "Переводы",
     "description": "Перевод Кредитная карта. ТП 10.2 RUR"}]
    """
    utils_logger.info("Начало обработки транзакций для топ-5.")
    df = pd.DataFrame(transaction_lst_)
    df = df.dropna(subset="Номер карты")
    transaction_sorted = df[
        ["Дата платежа", "Сумма платежа", "Категория", "Описание", "Сумма операции с округлением"]
    ].sort_values(by="Сумма операции с округлением", ascending=False)
    transaction_top_5 = transaction_sorted.nlargest(5, "Сумма операции с округлением")
    transaction_top_5_ = transaction_top_5[["Дата платежа", "Сумма платежа", "Категория", "Описание"]]
    transaction_top_5_ = transaction_top_5_.rename(
        columns={"Дата платежа": "date", "Сумма платежа": "amount", "Категория": "category", "Описание": "description"}
    )
    top_transactions = transaction_top_5_.to_dict("records")  # type: ignore[assignment]
    utils_logger.info("Топ-5 транзакций успешно обработаны.")
    return top_transactions


def get_currency() -> list[dict] | str:  # type: ignore[return]
    """Получает из файла формата json список валют USD и EUR, и формирует список словарей по типу:
    [{"currency": "USD",
    "rate": 82.00
    }]"""
    utils_logger.info("Начало получения курсов валют.")
    response = None
    currency_rate = []
    file_path = "user_settings.json"
    with open(file_path, "r", encoding="utf-8") as file:
        dictionary_ = json.load(file)
        currency_lst = dictionary_["user_currencies"]
        try:
            for currency in currency_lst:
                from_ = currency
                url = f"https://api.apilayer.com/exchangerates_data/convert?to=RUB&from={from_}&amount=1"

                headers = {"apikey": API_KEY}

                response = requests.get(url, headers=headers)
                response.raise_for_status()
                result = response.json()
                if response is None or result is None:
                    utils_logger.error("Нет информации о курсе валют.")
                    return "No response received"

                else:
                    rate = result["info"]["rate"]
                    data = {"currency": currency, "rate": round(rate, 2)}
                    currency_rate.append(data)

        except requests.exceptions.HTTPError:

            utils_logger.error("Ошибка HTTP при получении курсов валют.", exc_info=True)

            if response is None:
                return "No response received"

            if 500 <= response.status_code < 600:

                return "Server Error"

            elif 400 <= response.status_code < 500:

                return f"Client Error: {response.status_code}"

            else:
                utils_logger.error("Нет ответа от сервера при запросе курсов валют.")
                return "No response received"

    return currency_rate


def get_stock_price() -> list[dict] | str:
    """
      Получает список компаний: ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"] и формирует список по типу:
     [
        {"stock": "AAPL", "price": 150.12},
        {"stock": "AMZN", "price": 3400.00},
        {"stock": "GOOGL", "price": 2800.50},
        {"stock": "MSFT", "price": 299.99},
        {"stock": "TSLA", "price": 720.50}
    ]
    """
    utils_logger.info("Начало получения цен акций.")
    price_stock = []
    file_path = "user_settings.json"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            dictionary_st = json.load(file)
            companies_lst = dictionary_st["user_stocks"]
            for company in companies_lst:
                url = (
                    f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={company}&apikey={API_KEY_}"
                )
                response = requests.get(url)
                response.raise_for_status()
                result = response.json()
                latest_date = result["Meta Data"]["3. Last Refreshed"]
                closing_price = result["Time Series (Daily)"][latest_date]["4. close"]
                data_ = {"stock": company, "price": round(float(closing_price), 2)}
                price_stock.append(data_)
        utils_logger.info("Цены акций успешно получены и обработаны.")
        return price_stock

    except requests.exceptions.HTTPError as e:

        utils_logger.error("Ошибка HTTP при получении цен акций.", exc_info=True)

        if response.status_code == 500:
            return "Server Error"

        return f"Client Error: {response.status_code}"


def read_excel_file(path_excel: str) -> list[dict[Hashable, Any]]:
    """
     Функция для считывания финансовых операций из Excel. Принимает путь к файлу Excel, в качестве аргумента,
    и выдает список словарей с транзакциями.
    """
    utils_logger.info("Начало чтения файла Excel.")
    try:
        df_exl = pd.read_excel(path_excel)
        transactions_exl_list = df_exl.to_dict(orient="records")
        utils_logger.info("Список транзакций успешно создан.")
    except ValueError as e:
        utils_logger.error(f"Ошибка при чтении файла Excel: {e}")
        raise ValueError(f"Ошибка при чтении файла Excel: {e}")
    return transactions_exl_list


def read_excel_file_df(path_excel: str) -> DataFrame:
    """
    Функция для считывания финансовых операций из Excel. Принимает путь к файлу Excel, выдает DataFrame
    """
    utils_logger.info("Начало чтения файла Excel.")
    try:
        df_exl_ = pd.read_excel(path_excel)
        utils_logger.info("DataFrame успешно создан.")
    except ValueError as e:
        utils_logger.error(f"Ошибка при чтении файла Excel: {e}")
        raise ValueError(f"Ошибка при чтении файла Excel: {e}")
    return df_exl_
