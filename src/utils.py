import os

import json

from datetime import datetime

from typing import Any

import pandas as pd

import requests

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_ = os.getenv("API_KEY_")


def read_excel_file_period(path_excel_, time_period_):
    """
     Функция для считывания финансовых операций из Excel-файла за период. Принимает путь к файлу Excel, список из даты
    начала и окончания периода обработки данных. Возвращает список словарей.
    """
    try:
        df_exl = pd.read_excel(path_excel_)
        df_exl["Дата операции"] = pd.to_datetime(df_exl["Дата операции"], dayfirst=True)
        start_date = datetime.strptime(time_period_[0], "%d.%m.%Y %H:%M:%S")
        end_date = datetime.strptime(time_period_[1], "%d.%m.%Y %H:%M:%S")
        flt_df_exl = df_exl[(df_exl["Дата операции"] >= start_date) & (df_exl["Дата операции"] <= end_date)]
        srt_df_exl = flt_df_exl.sort_values(by="Дата операции", ascending=True)
        srt_df_exl_lst = srt_df_exl.to_dict(orient="records")
    except ValueError as e:
        raise ValueError(f"Ошибка при чтении файла Excel: {e}")
    return srt_df_exl_lst


def get_greeting() -> str:
    """
     Функция для определения времени суток, принимает аргумент, который должен быть объектом datetime,
    содержащим текущее время. Возвращает строку с определением времени суток.
    """
    current_time_ = datetime.now().hour
    if 5 <= current_time_ < 12:
        return "Доброе утро"
    elif 12 <= current_time_ < 18:
        return "Добрый день"
    elif 18 <= current_time_ < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_time_pr(date_string: str, date_frm: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """
    Принимает строку с датой и форматом преобразования строки. Возвращает список строк из начала и конца периода
    """
    dt = datetime.strptime(date_string, date_frm)
    beginning_of_period = dt.replace(day=1)
    return [beginning_of_period.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]


def get_card_data(transaction_lst: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
      Принимает список словарей, и отдает список словарей с данными транзакций из карт,
     по типу: "cards":
     [{"last_digits": "5814",
     "total_spent": 1262.00,
     "cashback": 12.62}]
    "cashback" == кешбэк (1 рубль на каждые 100 рублей)
    """
    df = pd.DataFrame(transaction_lst)
    df = df[df["Номер карты"].notna()]
    df["last_digits"] = df["Номер карты"].apply(lambda x: str(x)[-4:])
    df["Сумма операции"] = pd.to_numeric(df["Сумма операции"], errors="coerce")

    card_spent = {}
    df = df[df["Статус"] == "OK"]
    for ind, row in df.iterrows():
        if row["last_digits"] not in card_spent:
            card_spent[row["last_digits"]] = {"total_spent": 0, "cashback": 0}

        total_spent = abs(row["Сумма операции"])
        cashback = abs(total_spent) / 100

        card_spent[row["last_digits"]]["total_spent"] += total_spent
        card_spent[row["last_digits"]]["cashback"] += cashback

    cards = [
        {"last_digits": card, "total_spent": round(values["total_spent"], 2), "cashback": round(values["cashback"], 2)}
        for card, values in card_spent.items()
    ]

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
    df = pd.DataFrame(transaction_lst_)
    print(df.head(3))
    df = df.dropna(subset="Номер карты")
    # print(df)
    transaction_sorted = df[
        ["Дата платежа", "Сумма платежа", "Категория", "Описание", "Сумма операции с округлением"]
    ].sort_values(by="Сумма операции с округлением", ascending=False)
    transaction_top_5 = transaction_sorted.nlargest(5, "Сумма операции с округлением")
    transaction_top_5_ = transaction_top_5[["Дата платежа", "Сумма платежа", "Категория", "Описание"]]
    transaction_top_5_ = transaction_top_5_.rename(
        columns={"Дата платежа": "date", "Сумма платежа": "amount", "Категория": "category", "Описание": "description"}
    )
    top_transactions = transaction_top_5_.to_dict("records")  # type: ignore[assignment]

    return top_transactions


def get_currency() -> list[dict] | str:  # type: ignore[return]
    """Получает из файла формата json список валют USD и EUR, и формирует список словарей по типу:
    [{"currency": "USD",
    "rate": 82.00
    }]"""
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
                rate = result["info"]["rate"]
                data = {"currency": currency, "rate": round(rate, 2)}
                currency_rate.append(data)

            return currency_rate

        except requests.exceptions.HTTPError:

            if response:

                if 500 <= response.status_code < 600:

                    return "Server Error"

                elif 400 <= response.status_code < 500:

                    return f"Client Error: {response.status_code}"

            else:

                return "No response received"


def get_stock_price() -> list[dict] | str:
    """
      Получает список компаний и формирует список по типу:
     [{"stock": "AAPL",
    "price": 150.12}, ...]
    """
    response = None
    price_stock = []
    file_path = "user_settings.json"
    with open(file_path, "r", encoding="utf-8") as file:
        dictionary_st = json.load(file)
        companies_lst = dictionary_st["user_stocks"]
        try:
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

            return price_stock

        except requests.exceptions.HTTPError:

            if response:

                if 500 <= response.status_code < 600:

                    return "Server Error"

                elif 400 <= response.status_code < 500:

                    return f"Client Error: {response.status_code}"

            else:

                return "No response received"


# path_excel = "./data/operations.xlsx"
# time_period = get_time_pr("30.09.2018 00:00:00", "%d.%m.%Y %H:%M:%S")
# srt_df_exl_lst_ = read_excel_file_period(path_excel, time_period)
# # print(get_card_data(srt_df_exl_lst_))
# # print(transactions_5_top(srt_df_exl_lst_ ))
# # print(get_currency())
# print(srt_df_exl_lst_)

# sdf = get_stock_price()
# print(sdf)
#
