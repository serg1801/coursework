import json


from src.logging_config import setup_logging

services_logger = setup_logging("services")


def search_by_numbers(search_bar: str, list_operations: list[dict]) -> str:
    """
     Принимает строку для поиска и список словарей, возвращает JSON-ответ со всеми транзакциями,
    содержащими запрос поиска в поле 'Категория' и 'Описание'.
    """
    services_logger.info("Начало обработки списка словарей")

    search_bar_f = search_bar.strip().lower()
    result = [
        data
        for data in list_operations
        if (isinstance(data.get("Категория", ""), str) and search_bar_f in data.get("Категория", "").strip().lower())
        or (isinstance(data.get("Описание", ""), str) and search_bar_f in data.get("Описание", "").strip().lower())
    ]
    services_logger.info(f"Новый список по запросу: '{search_bar}' создан")

    return json.dumps(result, ensure_ascii=False, indent=4)


# list_operations_ = read_excel_file(path_excel)
# print(search_by_numbers("колхоз", list_operations))
