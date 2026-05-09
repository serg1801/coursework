import pytest
from unittest.mock import patch
import pandas as pd
from datetime import datetime

from src.reports import spending_by_category


@patch("datetime.datetime")
@pytest.mark.parametrize(
    "transactions, category, date, expected_count",
    [
        (
            pd.DataFrame({"Дата операции": ["2023-01-01", "2023-02-01"], "Категория": ["Food", "Food"]}),
            "Food",
            "2023-03-01",
            2,
        ),
        (
            pd.DataFrame({"Дата операции": ["2023-01-01", "2023-02-01"], "Категория": ["Transport", "Food"]}),
            "Transport",
            "2023-03-01",
            1,
        ),
    ],
)
def test_spending_by_category(mock_datetime, transactions, category, date, expected_count):
    mock_datetime.now.return_value = datetime.strptime("2023-03-01", "%Y-%m-%d")
    result = spending_by_category(transactions, category, date)
    assert len(result) == expected_count
