"""Validated, transactional cleaning operations. Inputs are never mutated."""
import operator
import re

import pandas as pd
from pandas.api.types import is_bool_dtype

from .data import kind, iqr_bounds, MAX_COLUMNS

METHODS = {
    "Missing values": ["drop rows", "mean", "median", "mode", "custom", "forward-fill"],
    "Duplicates": ["keep first", "keep last", "remove all"],
    "Convert type": ["string", "number", "date"],
    "String cleaning": ["trim", "lowercase", "uppercase", "remove special", "regex replace"],
    "Dates": ["standardize", "extract year/month/day"],
    "Outliers": ["cap", "remove", "flag"],
    "Columns": ["rename", "drop", "reorder", "split", "merge"],
    "Filter rows": ["==", "!=", ">", ">=", "<", "<=", "contains", "is missing", "not missing"],
}


def new_name(frame, name):
    if not name.strip():
        raise ValueError("กรุณาระบุชื่อคอลัมน์ใหม่")
    if name.casefold() in {c.casefold() for c in frame.columns}:
        raise ValueError(f"มีคอลัมน์ชื่อ {name} อยู่แล้ว")


def parsed_date(series, fmt="mixed"):
    try:
        return pd.to_datetime(series, format=fmt or "mixed", errors="raise", utc=True).dt.tz_localize(None)
    except (ValueError, TypeError) as exc:
        raise ValueError("มีค่าที่แปลงเป็นวันที่ไม่ได้ ระบุ format เช่น %d/%m/%Y หรือใช้ mixed") from exc


def clean(frame: pd.DataFrame, action: str, column: str = "", *, method: str = "", value: str = "",
          replacement: str = "", columns: list[str] | None = None) -> pd.DataFrame:
    if action not in METHODS:
        raise ValueError("ไม่รู้จักคำสั่ง cleaning")
    method = method or METHODS[action][0]
    if method not in METHODS[action]:
        raise ValueError("วิธีที่เลือกไม่ตรงกับคำสั่ง")
    result = frame.copy(deep=True)
    cols = list(columns or [])
    if any(c not in result for c in cols) or len(set(cols)) != len(cols):
        raise ValueError("รายการคอลัมน์ไม่ถูกต้องหรือซ้ำกัน")
    needs_column = action not in ("Duplicates",) and not (action == "Columns" and method in ("merge", "reorder"))
    if needs_column and column not in result:
        raise ValueError("กรุณาเลือกคอลัมน์")
    series = result[column] if column in result else None
    try:
        if action == "Missing values":
            if method == "drop rows":
                result = result.dropna(subset=[column])
            elif method in ("mean", "median"):
                if kind(series) != "numeric":
                    raise ValueError("Mean และ median ใช้ได้เฉพาะคอลัมน์ตัวเลข")
                fill = getattr(series, method)()
                if pd.isna(fill):
                    raise ValueError("คอลัมน์นี้ว่างทั้งหมด ไม่มีค่าที่ใช้คำนวณ")
                result[column] = series.astype(float).fillna(fill)
            elif method == "mode":
                modes = series.mode()
                if modes.empty:
                    raise ValueError("คอลัมน์นี้ว่างทั้งหมด ไม่มี mode")
                result[column] = series.fillna(modes.iloc[0])
            elif method == "custom":
                fill = float(value) if kind(series) == "numeric" else pd.Timestamp(value) if kind(series) == "datetime" else value
                result[column] = series.fillna(fill)
            else:
                result[column] = series.ffill()
        elif action == "Duplicates":
            keep = {"keep first": "first", "keep last": "last", "remove all": False}[method]
            result = result.drop_duplicates(subset=cols or None, keep=keep)
        elif action == "Convert type":
            if method == "string":
                result[column] = series.astype("string")
            elif method == "number":
                result[column] = pd.to_numeric(series, errors="raise")
            else:
                result[column] = parsed_date(series, value)
        elif action == "String cleaning":
            if kind(series) != "categorical":
                raise ValueError("กรุณาเลือกคอลัมน์ข้อความ หรือแปลงเป็น string ก่อน")
            strings = series.astype("string")
            if method == "trim":
                result[column] = strings.str.strip()
            elif method == "lowercase":
                result[column] = strings.str.lower()
            elif method == "uppercase":
                result[column] = strings.str.upper()
            elif method == "remove special":
                result[column] = strings.str.replace(r"[^\w\s]", "", regex=True)
            else:
                if not value or len(value) > 200:
                    raise ValueError("Regex ต้องมีความยาว 1–200 ตัวอักษร")
                re.compile(value)
                result[column] = strings.str.replace(value, replacement, regex=True)
        elif action == "Dates":
            result[column] = parsed_date(series, value)
            if method == "extract year/month/day":
                for part in ("year", "month", "day"):
                    target = f"{column}_{part}"
                    new_name(result, target)
                    result[target] = getattr(result[column].dt, part).astype("Int64")
        elif action == "Outliers":
            low, high = iqr_bounds(series)
            if pd.isna(low):
                raise ValueError("ไม่มีตัวเลขสำหรับคำนวณขอบเขต IQR")
            mask = ((series < low) | (series > high)).fillna(False)
            if method == "cap":
                result[column] = series.astype(float).clip(low, high)
            elif method == "remove":
                result = result[~mask]
            else:
                target = f"{column}_outlier"
                new_name(result, target)
                result[target] = mask
        elif action == "Columns":
            if method == "rename":
                new_name(result, value)
                result = result.rename(columns={column: value})
            elif method == "drop":
                if len(result.columns) == 1:
                    raise ValueError("ต้องเหลืออย่างน้อยหนึ่งคอลัมน์")
                result = result.drop(columns=[column])
            elif method == "reorder":
                if set(cols) != set(result.columns):
                    raise ValueError("เลือกทุกคอลัมน์หนึ่งครั้งตามลำดับที่ต้องการ")
                result = result[cols]
            elif method == "split":
                if not value:
                    raise ValueError("ระบุตัวคั่นสำหรับ split เช่น ช่องว่าง หรือ ,")
                parts = series.astype("string").str.split(value, n=9, expand=True, regex=False)
                for i in range(parts.shape[1]):
                    target = f"{column}_{i + 1}"
                    new_name(result, target)
                    result[target] = parts[i]
            else:
                if len(cols) < 2:
                    raise ValueError("เลือกอย่างน้อย 2 คอลัมน์เพื่อ merge")
                new_name(result, value)
                result[value] = result[cols].astype("string").fillna("").agg(replacement.join, axis=1)
        elif action == "Filter rows":
            if method == "is missing":
                mask = series.isna()
            elif method == "not missing":
                mask = series.notna()
            elif method == "contains":
                mask = series.astype("string").str.contains(value, regex=False, na=False)
            else:
                if is_bool_dtype(series):
                    if value.strip().lower() not in ("true", "false", "1", "0"):
                        raise ValueError("คอลัมน์ boolean ใช้ค่า true / false หรือ 1 / 0")
                    typed = value.strip().lower() in ("true", "1")
                else:
                    typed = float(value) if kind(series) == "numeric" else pd.Timestamp(value) if kind(series) == "datetime" else value
                operations = {"==": operator.eq, "!=": operator.ne, ">": operator.gt,
                              ">=": operator.ge, "<": operator.lt, "<=": operator.le}
                mask = operations[method](series, typed) & series.notna()
            result = result[mask.fillna(False)]
    except (TypeError, re.error, OverflowError) as exc:
        raise ValueError("ค่าหรือรูปแบบที่ระบุใช้กับคอลัมน์นี้ไม่ได้ กรุณาตรวจสอบอีกครั้ง") from exc
    if len(result.columns) > MAX_COLUMNS:
        raise ValueError("ผลลัพธ์มีคอลัมน์เกิน 150 คอลัมน์")
    return result.reset_index(drop=True)
