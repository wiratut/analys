"""Strict CSV ingestion and in-memory DuckDB profiling."""
import csv
import io
import math

import duckdb
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype, is_bool_dtype

MAX_BYTES = 25 * 1024 * 1024
MAX_ROWS = 200_000
MAX_COLUMNS = 150
# The default csv limit is only 128 KiB per field; uploads are already bounded.
csv.field_size_limit(MAX_BYTES)


def quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def number(value):
    return float(value) if value is not None and math.isfinite(float(value)) else None


ENCODINGS = {
    "Auto": None, "UTF-8": "utf-8-sig", "UTF-16": "utf-16",
    "UTF-16 LE": "utf-16-le", "UTF-16 BE": "utf-16-be",
    "Thai (Windows-874 / TIS-620)": "cp874", "Windows-1252": "cp1252",
}
DELIMITERS = {"Auto": None, "Comma (,)": ",", "Semicolon (;)": ";", "Tab": "\t", "Pipe (|)": "|"}


def _decode_csv(payload: bytes, encoding: str) -> tuple[str, str]:
    if encoding not in ENCODINGS:
        raise ValueError("กรุณาเลือก encoding ที่รองรับ")
    if encoding != "Auto":
        candidates = [ENCODINGS[encoding]]
    elif payload.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
        candidates = ["utf-32"]
    elif payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        candidates = ["utf-16"]
    else:
        candidates = ["utf-8-sig", "cp874"]
    for codec in candidates:
        try:
            return payload.decode(codec).removeprefix("\ufeff"), codec
        except UnicodeError:
            continue
    raise ValueError("อ่าน encoding ไม่ได้ กรุณาเลือก encoding ของไฟล์ในหน้า Upload หรือบันทึกใหม่เป็น CSV UTF-8")


def _detect_delimiter(text: str) -> str:
    # Detect from the header first: a malformed data row must not cause the
    # entire file to be silently reinterpreted as one column.
    candidates = []
    for separator in ",;\t|":
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=separator, strict=True)
        try:
            header = next(row for row in reader if row)
        except (csv.Error, StopIteration):
            continue
        if len(header) > 1:
            matches = seen = 0
            try:
                for row in reader:
                    if row:
                        seen += 1
                        matches += len(row) == len(header)
                    if seen >= 30:
                        break
            except csv.Error:
                pass
            candidates.append((matches / max(seen, 1), len(header), separator))
    return max(candidates, key=lambda item: item[:2])[2] if candidates else ","


def read_csv(payload: bytes, filename: str, *, encoding: str = "Auto", delimiter: str = "Auto") -> pd.DataFrame:
    if not filename.lower().endswith(".csv"):
        raise ValueError("กรุณาเลือกไฟล์นามสกุล .csv")
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError("ไฟล์ต้องไม่ว่างและมีขนาดไม่เกิน 25 MB")
    if delimiter not in DELIMITERS:
        raise ValueError("กรุณาเลือกตัวคั่นที่รองรับ")
    text, codec = _decode_csv(payload, encoding)
    if "\x00" in text:
        raise ValueError("ไฟล์มีข้อมูลไบนารี หรือเป็น UTF-16 ที่ไม่มี BOM กรุณาเลือก encoding ให้ตรงกับไฟล์")
    source = io.StringIO(text, newline="")
    first_line = source.readline().rstrip("\r\n")
    offset = 0
    declared = None
    if len(first_line) == 5 and first_line[:4].lower() == "sep=" and first_line[4] in ",;\t|":
        declared = first_line[4]
        text = source.read()
        offset = 1
    separator = DELIMITERS[delimiter] or declared or _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=separator, strict=True)
    # Re-serialize validated records so pandas sees precisely the same rows,
    # including quoted multiline fields and whitespace-only values.
    normalized = io.StringIO(newline="")
    writer = csv.writer(normalized)
    header = None
    count = 0
    while True:
        start_line = reader.line_num + offset + 1
        try:
            row = next(reader)
        except StopIteration:
            break
        except csv.Error as exc:
            end_line = reader.line_num + offset
            raise ValueError(
                f"อ่าน CSV ไม่ได้ที่บรรทัด {start_line}–{end_line}: เครื่องหมายคำพูดไม่ถูกต้อง "
                'ตรวจว่าเปิดและปิดด้วย " ครบคู่ และใช้ "" เมื่อต้องการใส่เครื่องหมายคำพูดในข้อความ'
            ) from exc
        if not row:
            continue
        if header is None:
            header = row
            if any(not c.strip() for c in header):
                raise ValueError(f"บรรทัด {start_line}: ทุกคอลัมน์ต้องมีชื่อในหัวตาราง")
            if len({c.casefold() for c in header}) != len(header):
                raise ValueError("ชื่อคอลัมน์ต้องไม่ซ้ำกันแม้ใช้ตัวพิมพ์ใหญ่/เล็กต่างกัน")
            if len(header) > MAX_COLUMNS:
                raise ValueError("รองรับสูงสุด 150 คอลัมน์")
        else:
            if len(row) != len(header):
                label = "Tab" if separator == "\t" else separator
                raise ValueError(
                    f"บรรทัด {start_line}: พบ {len(row)} ช่อง แต่หัวตารางมี {len(header)} ช่อง "
                    f"(ตัวคั่น {label}) กรุณาตรวจตัวคั่นและเครื่องหมายคำพูด หรือเลือกตัวคั่นเองในหน้า Upload"
                )
            count += 1
            if count > MAX_ROWS:
                raise ValueError("รองรับสูงสุด 200,000 แถวต่อ session")
        writer.writerow(row)
    if header is None:
        raise ValueError("ไฟล์ไม่มีหัวตารางหรือข้อมูล")
    if count == 0:
        raise ValueError("ไฟล์มีเฉพาะหัวตาราง ไม่มีข้อมูล")
    normalized.seek(0)
    frame = pd.read_csv(normalized, skip_blank_lines=False)
    frame.attrs["csv_encoding"] = codec
    frame.attrs["csv_delimiter"] = "Tab" if separator == "\t" else separator
    return frame

def kind(series: pd.Series) -> str:
    if is_datetime64_any_dtype(series):
        return "datetime"
    if is_numeric_dtype(series) and not is_bool_dtype(series):
        return "numeric"
    return "categorical"


def date_candidates(frame: pd.DataFrame) -> list[str]:
    result = []
    for col in frame:
        if kind(frame[col]) == "datetime":
            result.append(col)
        elif kind(frame[col]) == "categorical":
            sample = frame[col].dropna().astype(str).head(500)
            if len(sample) and sample.str.match(r"^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}").mean() >= .9:
                if pd.to_datetime(sample, format="mixed", errors="coerce", utc=True).notna().mean() >= .9:
                    result.append(col)
    return result


def profile(frame: pd.DataFrame) -> dict:
    schema = []
    with duckdb.connect(":memory:") as con:
        con.register("source", frame)
        for col in frame:
            c = quote(col)
            missing, unique = con.execute(
                f"SELECT count(*) FILTER (WHERE {c} IS NULL), count(DISTINCT {c}) FROM source"
            ).fetchone()
            entry = dict(column=col, dtype=str(frame[col].dtype), kind=kind(frame[col]),
                         missing=int(missing), missing_pct=100 * missing / len(frame) if len(frame) else 0,
                         unique=int(unique), mean=None, median=None, min=None, max=None, std=None,
                         outliers=0)
            if kind(frame[col]) == "numeric":
                finite = f"CASE WHEN isfinite(CAST({c} AS DOUBLE)) THEN {c} END"
                stats = con.execute(f"SELECT avg({finite}), median({finite}), min({finite}), max({finite}), stddev_samp({finite}) FROM source").fetchone()
                entry.update({key: number(val) for key, val in zip(("mean", "median", "min", "max", "std"), stats)})
                low, high = iqr_bounds(frame[col])
                entry["outliers"] = int(((frame[col] < low) | (frame[col] > high)).sum())
            schema.append(entry)
    return dict(rows=len(frame), columns=len(frame.columns), duplicates=int(frame.duplicated().sum()),
                missing=int(frame.isna().sum().sum()), outliers=sum(c["outliers"] for c in schema), schema=schema)


def iqr_bounds(series: pd.Series) -> tuple[float, float]:
    if kind(series) != "numeric":
        raise ValueError("คำสั่งนี้ใช้ได้กับคอลัมน์ตัวเลขเท่านั้น")
    finite = series.replace([float("inf"), float("-inf")], float("nan")).dropna()
    if finite.empty:
        return float("nan"), float("nan")
    q1, q3 = finite.quantile([.25, .75])
    return float(q1 - 1.5 * (q3 - q1)), float(q3 + 1.5 * (q3 - q1))


def preview(frame: pd.DataFrame, limit: int = 30) -> list[list[str]]:
    return [["—" if pd.isna(v) else str(v) for v in row] for row in frame.head(limit).itertuples(index=False, name=None)]


def filter_frame(frame, category="", value="", date_column="", start="", end=""):
    result = frame.copy(deep=True)
    if category and value:
        if category not in result:
            raise ValueError("ไม่พบคอลัมน์ที่ใช้กรอง")
        result = result[result[category].astype("string") == value]
    if date_column and (start or end):
        dates = pd.to_datetime(result[date_column], format="mixed", errors="coerce", utc=True)
        begin = pd.to_datetime(start, utc=True) if start else None
        finish = pd.to_datetime(end, utc=True) if end else None
        if begin is not None and finish is not None and begin > finish:
            raise ValueError("วันที่เริ่มต้นต้องไม่อยู่หลังวันที่สิ้นสุด")
        if begin is not None:
            result = result[dates >= begin]
            dates = dates.loc[result.index]
        if finish is not None:
            result = result[dates.dt.normalize() <= finish.normalize()]
    return result.copy()
