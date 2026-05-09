import os

from src.reports import spending_by_category
from src.services import search_by_numbers
from src.utils import read_excel_file, read_excel_file_df
from src.views import main_page

path_excel = os.path.join(os.path.dirname(__file__), "../data/operations.xlsx")

list_operations = read_excel_file(path_excel)

if __name__ == "__main__":
    print(main_page("2021-12-03 08:16:00"))
    print(search_by_numbers("Колхоз", list_operations))
    transactions_three_months = read_excel_file_df(path_excel)
    spending_by_category(transactions_three_months, "Аптеки", "2021-12-30 08:16:00")
