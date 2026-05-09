import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
import functools


from src.logging_config import setup_logging

reports_logger = setup_logging("reports")


def log(filename=None):
    """
    Записывает в файл результат, который возвращает функция, формирующая отчет.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            # Определяем имя файла
            if filename is None:
                date_str = datetime.now().strftime("%Y%m-%d")
                file_name = f"{func.__name__}_{date_str}.csv"
            else:
                file_name = filename

            # Сохраняем результат в файл
            result.to_csv(file_name, index=False, encoding="utf-8")
            reports_logger.info(f"Результаты сохранены в файл: {file_name}")
            print(f"Отчет сохранён в {file_name}")

            return result

        return wrapper

    return decorator


@log()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
       Принимает на вход датафрейм с транзакциями, название категории, опциональную дату.
     Если дата не передана, то берется текущая дата.
    Возвращает траты по заданной категории за последние три месяца (от переданной даты).
    """
    reports_logger.debug("Начало выполнения функции spending_by_category")
    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], dayfirst=True)
    if date is None:
        date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    # Приводим дату к datetime
    reference_date = pd.to_datetime(date, dayfirst=False)

    # Фильтруем транзакции за последние 3 месяца
    three_months_ago = reference_date - timedelta(days=90)
    filtered = transactions[
        (transactions["Дата операции"] >= three_months_ago)
        & (transactions["Дата операции"] <= reference_date)
        & (transactions["Категория"] == category)
    ]
    reports_logger.info(f"Количество отфильтрованных транзакций: {len(filtered)}")
    return filtered
