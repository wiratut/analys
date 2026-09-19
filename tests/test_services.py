from io import BytesIO

import pandas as pd
import pytest

from analyst_studio.services.data import read_csv, profile, filter_frame
from analyst_studio.services.cleaning import clean


@pytest.fixture
def dirty():
    return pd.DataFrame({"name": [" Alice ", "BOB", "BOB", None],
                         "amount": [10., 20., 20., None],
                         "date": ["2025-01-01", "2025/01/02", "2025/01/02", None]})


def test_csv_and_profile(dirty):
    result = profile(dirty)
    assert result["rows"] == 4
    assert result["duplicates"] == 1
    amount = next(c for c in result["schema"] if c["column"] == "amount")
    assert amount["missing_pct"] == 25
    assert amount["unique"] == 2
    assert amount["mean"] == pytest.approx(50 / 3)
    assert amount["median"] == 20
    assert read_csv(dirty.to_csv(index=False).encode(), "test.csv").shape == (4, 3)


@pytest.mark.parametrize("payload,name", [(b"", "a.csv"), (b"a,b\n1,2", "a.exe"),
    (b"a,b\n1,2,3", "bad.csv"), (b"a,a\n1,2", "duplicate.csv")])
def test_reject_bad_csv(payload, name):
    with pytest.raises(ValueError):
        read_csv(payload, name)


@pytest.mark.parametrize("method,expected", [("mean", 50 / 3), ("median", 20),
    ("mode", 20), ("custom", 99), ("forward-fill", 20)])
def test_missing(dirty, method, expected):
    result = clean(dirty, "Missing values", "amount", method=method, value="99")
    assert result.amount.iloc[-1] == pytest.approx(expected)
    assert pd.isna(dirty.amount.iloc[-1])


def test_drop_and_duplicates(dirty):
    assert len(clean(dirty, "Missing values", "amount", method="drop rows")) == 3
    assert len(clean(dirty, "Duplicates", "", columns=[])) == 3
    assert len(clean(dirty, "Duplicates", "", columns=["amount"])) == 3


def test_type_string_date(dirty):
    trimmed = clean(dirty, "String cleaning", "name", method="trim")
    assert trimmed.name.iloc[0] == "Alice"
    assert clean(dirty, "String cleaning", "name", method="lowercase").name.iloc[1] == "bob"
    assert clean(dirty, "String cleaning", "name", method="uppercase").name.iloc[0] == " ALICE "
    assert clean(dirty, "String cleaning", "name", method="regex replace", value="BOB", replacement="Tom").name.iloc[1] == "Tom"
    assert clean(pd.DataFrame({"x": ["a@b!"]}), "String cleaning", "x", method="remove special").x.iloc[0] == "ab"
    parsed = clean(dirty, "Dates", "date", method="extract year/month/day", value="mixed")
    assert parsed.date_year.iloc[0] == 2025
    assert pd.api.types.is_datetime64_any_dtype(parsed.date)
    converted = clean(pd.DataFrame({"x": ["1", "2"]}), "Convert type", "x", method="number")
    assert converted.x.sum() == 3
    assert str(clean(converted, "Convert type", "x", method="string").x.dtype) == "string"
    with pytest.raises(ValueError):
        clean(dirty, "Convert type", "name", method="number")


def test_outliers():
    frame = pd.DataFrame({"x": [1., 2, 3, 4, 100]})
    assert profile(frame)["outliers"] == 1
    assert clean(frame, "Outliers", "x", method="cap").x.max() == 7
    assert len(clean(frame, "Outliers", "x", method="remove")) == 4
    assert clean(frame, "Outliers", "x", method="flag").x_outlier.sum() == 1


def test_columns(dirty):
    assert "person" in clean(dirty, "Columns", "name", method="rename", value="person")
    assert "name" not in clean(dirty, "Columns", "name", method="drop")
    assert list(clean(dirty, "Columns", "", method="reorder", columns=["date", "name", "amount"])) == ["date", "name", "amount"]
    split = clean(pd.DataFrame({"name": ["Ada Lovelace"]}), "Columns", "name", method="split", value=" ")
    assert split.name_2.iloc[0] == "Lovelace"
    merged = clean(dirty, "Columns", "", method="merge", columns=["name", "amount"], value="combined", replacement=" / ")
    assert "BOB / 20.0" == merged.combined.iloc[1]
    with pytest.raises(ValueError):
        clean(dirty, "Columns", "name", method="rename", value="amount")


def test_filters(dirty):
    assert len(clean(dirty, "Filter rows", "amount", method=">", value="15")) == 2
    assert len(clean(dirty, "Filter rows", "name", method="contains", value="BO")) == 2
    dated = dirty.copy()
    dated.date = pd.to_datetime(dated.date, format="mixed")
    assert len(filter_frame(dated, "name", "BOB", "date", "2025-01-02", "2025-01-02")) == 2
    with pytest.raises(ValueError):
        filter_frame(dated, "", "", "date", "2025-02-01", "2025-01-01")


def test_sql_identifier_escaping():
    result = profile(pd.DataFrame({'a"; DROP TABLE source; --': [1, 2, None]}))
    assert result["schema"][0]["mean"] == 1.5


def test_nonfinite_numbers_do_not_break_profile():
    frame = read_csv(b"x\ninf\n-inf\n1\n", "numbers.csv")
    stats = profile(frame)
    assert stats["rows"] == 3
    assert stats["schema"][0]["mean"] == 1


def test_filter_boolean_outlier_flags():
    frame = clean(pd.DataFrame({"x": [1, 2, 3, 4, 100]}), "Outliers", "x", method="flag")
    flagged = clean(frame, "Filter rows", "x_outlier", method="==", value="true")
    assert flagged.x.tolist() == [100]
