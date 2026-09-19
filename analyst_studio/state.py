"""Server-only dataset state with transactional previews and complete undo."""
import asyncio
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import reflex as rx

from .services.data import read_csv, profile, preview, filter_frame, date_candidates, kind, MAX_BYTES
from .services.cleaning import METHODS, clean
from .services.analytics import Chart, auto_charts, custom_chart, insight_summary
from .services.export import csv_bytes, excel_bytes, pdf_bytes
from .services.insights import generate_insight


class StudioState(rx.State):
    _df: pd.DataFrame | None = None
    _pending_df: pd.DataFrame | None = None
    _snapshots: list[pd.DataFrame] = []
    _chart_specs: list[Chart] = []
    _filtered: pd.DataFrame | None = None
    _revision: int = 0
    _pending_label: str = ""

    step: str = "Upload"
    loaded: bool = False
    filename: str = ""
    csv_encoding: str = "Auto"
    csv_delimiter: str = "Auto"
    busy: bool = False
    error: str = ""
    notice: str = ""
    columns: list[str] = []
    numeric_columns: list[str] = []
    category_columns: list[str] = []
    date_columns: list[str] = []
    table_rows: list[list[str]] = []
    schema_rows: list[list[str]] = []
    total_rows: str = "0"
    total_columns: str = "0"
    missing_cells: str = "0"
    duplicate_rows: str = "0"
    outlier_cells: str = "0"
    completeness: str = "100"

    action: str = "Missing values"
    method: str = "drop rows"
    column: str = ""
    value: str = ""
    replacement: str = ""
    selected_columns: list[str] = []
    pending: bool = False
    before_columns: list[str] = []
    after_columns: list[str] = []
    before_rows: list[list[str]] = []
    after_rows: list[list[str]] = []
    impact: str = ""
    history: list[dict[str, str]] = []

    category_filter: str = ""
    category_value: str = ""
    date_filter: str = ""
    date_start: str = ""
    date_end: str = ""
    filter_description: str = "All rows · ไม่ใช้ตัวกรอง"
    dashboard_rows: str = "0"
    dashboard_missing: str = "0"
    kpi_column: str = ""
    kpi_total: str = "—"
    figures: list[go.Figure] = []
    dashboard_ready: bool = False
    chart_type: str = "Bar"
    chart_x: str = ""
    chart_y: str = ""
    custom_figure: go.Figure = go.Figure()
    has_custom: bool = False
    insight: str = ""
    insight_ok: bool = False
    insight_busy: bool = False

    @rx.var
    def methods(self) -> list[str]:
        return METHODS.get(self.action, [])

    @rx.var
    def category_values(self) -> list[str]:
        if self._df is None or self.category_filter not in self._df:
            return []
        return sorted(self._df[self.category_filter].dropna().astype(str).unique().tolist())

    @rx.var
    def help_text(self) -> str:
        if self.action == "Duplicates":
            return "เลือกคอลัมน์ด้านล่างเพื่อใช้เป็น key หรือไม่เลือกเพื่อเทียบทั้งแถว"
        if self.action == "Columns":
            return {"rename": "Value = ชื่อคอลัมน์ใหม่", "drop": "ลบคอลัมน์ที่เลือก (ย้อนกลับได้ด้วย Undo)",
                    "reorder": "คลิกเลือกทุกคอลัมน์ด้านล่างตามลำดับที่ต้องการ", "split": "Value = ตัวคั่น เช่น ช่องว่าง หรือ , (แยกสูงสุด 10 ส่วน)",
                    "merge": "เลือกอย่างน้อย 2 คอลัมน์ตามลำดับ • Value = ชื่อใหม่ • Replacement = ตัวคั่น"}[self.method]
        if self.action == "Dates" or (self.action == "Convert type" and self.method == "date"):
            return "Value = format เช่น %d/%m/%Y หรือ mixed • ผลลัพธ์เป็น datetime มาตรฐาน UTC • ค่าว่างคงเดิม"
        if self.action == "String cleaning" and self.method == "regex replace":
            return "Value = regex pattern • Replacement = ข้อความแทนที่ (ปล่อยว่างเพื่อลบ)"
        if self.action == "Outliers":
            return "ใช้ขอบเขต Q1 − 1.5 × IQR ถึง Q3 + 1.5 × IQR • ค่าว่างไม่ถูกนับเป็น outlier"
        return "เลือกคอลัมน์และวิธีที่ต้องการ • ใส่ Value เมื่อใช้ custom หรือเปรียบเทียบค่า"

    def _clear_preview(self):
        self._pending_df = None
        self.pending = False
        self.before_rows = []
        self.after_rows = []
        self.impact = ""

    def _invalidate_dashboard(self):
        self.dashboard_ready = False
        self.figures = []
        self._chart_specs = []
        self._filtered = None
        self.has_custom = False
        self.custom_figure = go.Figure()
        self.insight = ""
        self.insight_ok = False
        self._revision += 1

    def _refresh(self, stats: dict | None = None):
        stats = stats if stats is not None else profile(self._df)
        self.columns = list(self._df.columns)
        self.numeric_columns = [c for c in self.columns if kind(self._df[c]) == "numeric"]
        self.date_columns = date_candidates(self._df)
        self.category_columns = [c for c in self.columns if kind(self._df[c]) == "categorical" and c not in self.date_columns]
        self.table_rows = preview(self._df)
        self.total_rows = f"{stats['rows']:,}"
        self.total_columns = str(stats["columns"])
        self.missing_cells = f"{stats['missing']:,}"
        self.duplicate_rows = f"{stats['duplicates']:,}"
        self.outlier_cells = f"{stats['outliers']:,}"
        cells = stats["rows"] * stats["columns"]
        self.completeness = f"{100 * (1 - stats['missing'] / cells) if cells else 100:.1f}"
        self.schema_rows = [[c["column"], c["dtype"], f"{c['missing_pct']:.1f}%", str(c["unique"]),
            *["—" if c[k] is None else f"{c[k]:,.3f}" for k in ("mean", "median", "min", "max", "std")],
            str(c["outliers"])] for c in stats["schema"]]
        if self.column not in self.columns:
            self.column = self.columns[0] if self.columns else ""
        self.selected_columns = [c for c in self.selected_columns if c in self.columns]
        if self.kpi_column not in self.numeric_columns:
            self.kpi_column = self.numeric_columns[0] if self.numeric_columns else ""
        if self.chart_x not in self.columns:
            self.chart_x = self.columns[0] if self.columns else ""
        if self.chart_y not in self.numeric_columns:
            self.chart_y = self.numeric_columns[0] if self.numeric_columns else ""

    def _load(self, frame: pd.DataFrame, filename: str):
        # Validate the replacement before changing any existing session data.
        stats = profile(frame)
        self._df = frame.copy(deep=True)
        self.filename = Path(filename).name
        self.loaded = True
        self.history = []
        self._snapshots = []
        self._clear_preview()
        self._invalidate_dashboard()
        self.category_filter = self.category_value = self.date_filter = self.date_start = self.date_end = ""
        self.action, self.method = "Missing values", "drop rows"
        self.value = self.replacement = ""
        self.selected_columns = []
        self.error = ""
        self._refresh(stats)
        self.notice = "โหลดข้อมูลแล้ว • ตรวจ schema, missing, duplicate และ outlier อัตโนมัติแล้ว"
        if "csv_encoding" in frame.attrs:
            self.notice += f" • encoding: {frame.attrs['csv_encoding']} • ตัวคั่น: {frame.attrs['csv_delimiter']} (หากตัวอักษรไม่ถูกต้อง ให้เลือก encoding เองแล้วอัปโหลดใหม่)"
        self.step = "Profile"

    @rx.event
    async def upload(self, files: list[rx.UploadFile]):
        self.busy, self.error, self.notice = True, "", ""
        yield
        try:
            if len(files) != 1:
                raise ValueError("กรุณาเลือก CSV ครั้งละหนึ่งไฟล์")
            content = await files[0].read(MAX_BYTES + 1)
            filename = files[0].filename or "upload.csv"
            frame = await asyncio.to_thread(read_csv, content, filename,
                                            encoding=self.csv_encoding, delimiter=self.csv_delimiter)
            self._load(frame, filename)
        except Exception as exc:
            self.error = str(exc) if isinstance(exc, ValueError) else "อ่านไฟล์ไม่ได้ กรุณาตรวจสอบไฟล์ CSV แล้วลองใหม่"
        finally:
            self.busy = False
        yield rx.clear_selected_files("csv-upload")

    @rx.event
    async def load_sample(self):
        self.busy, self.error = True, ""
        yield
        try:
            path = Path(__file__).parent / "data" / "sample_sales.csv"
            self._load(await asyncio.to_thread(read_csv, path.read_bytes(), path.name), path.name)
        except Exception:
            self.error = "โหลด sample dataset ไม่สำเร็จ"
        finally:
            self.busy = False

    @rx.event
    async def go_step(self, step: str):
        if step != "Upload" and not self.loaded:
            self.error = "อัปโหลด CSV หรือเลือก sample dataset ก่อนเริ่ม"
            return
        self.step = step
        self.error = ""
        if step in ("Dashboard", "Export") and not self.dashboard_ready:
            self.busy = True
            yield
            try:
                self._build_dashboard()
            except Exception:
                self.error = "สร้าง dashboard ไม่สำเร็จ กรุณาตรวจชนิดข้อมูลหรือล้างตัวกรอง"
            finally:
                self.busy = False

    @rx.event
    def set_action(self, value: str):
        if value in METHODS:
            self.action, self.method = value, METHODS[value][0]
            self.value = self.replacement = ""
            self.selected_columns = []
            self._clear_preview()

    @rx.event
    def set_method(self, value: str):
        self.method = value
        self._clear_preview()

    @rx.event
    def set_column(self, value: str):
        self.column = value
        self._clear_preview()

    @rx.event
    def set_value(self, value: str):
        self.value = value
        self._clear_preview()

    @rx.event
    def set_replacement(self, value: str):
        self.replacement = value
        self._clear_preview()

    @rx.event
    def toggle_column(self, value: str):
        if value in self.selected_columns:
            self.selected_columns = [c for c in self.selected_columns if c != value]
        else:
            self.selected_columns = [*self.selected_columns, value]
        self._clear_preview()

    def _prepare_preview(self):
        if self._df is None:
            raise ValueError("กรุณาโหลดข้อมูลก่อน")
        self._clear_preview()
        candidate = clean(self._df, self.action, self.column, method=self.method, value=self.value,
                          replacement=self.replacement, columns=self.selected_columns)
        self._pending_df = candidate
        self.before_columns, self.after_columns = list(self._df.columns), list(candidate.columns)
        self.before_rows, self.after_rows = preview(self._df), preview(candidate)
        self.impact = f"{len(self._df):,} → {len(candidate):,} แถว · {len(self._df.columns)} → {len(candidate.columns)} คอลัมน์ · missing {int(self._df.isna().sum().sum()):,} → {int(candidate.isna().sum().sum()):,}"
        target = ", ".join(self.selected_columns) or self.column
        self._pending_label = f"{self.action} / {self.method} · {target}"
        if self.value:
            self._pending_label += f" · value={self.value}"
        if self.replacement:
            self._pending_label += f" · replacement={self.replacement}"
        self.pending = True

    @rx.event
    async def preview_action(self):
        self.busy, self.error, self.notice = True, "", ""
        yield
        try:
            self._prepare_preview()
        except Exception as exc:
            self.error = str(exc) if isinstance(exc, ValueError) else "คำสั่งนี้ใช้กับข้อมูลไม่ได้ กรุณาตรวจสอบค่าที่เลือก"
        finally:
            self.busy = False

    @rx.event
    def apply_preview(self):
        if self._pending_df is None or not self.pending:
            self.error = "ดูตัวอย่างก่อน apply ทุกครั้ง"
            return
        size = sum(int(f.memory_usage(deep=True).sum()) for f in [*self._snapshots, self._df, self._pending_df])
        if size > 512 * 1024 * 1024:
            self.error = "ข้อมูลและประวัติใช้หน่วยความจำเกิน 512 MB กรุณาส่งออกข้อมูลแล้วเริ่ม session ใหม่"
            return
        try:
            stats = profile(self._pending_df)
        except Exception:
            self.error = "ตรวจผลลัพธ์ไม่สำเร็จ ข้อมูลเดิมยังอยู่ กรุณาปรับคำสั่งแล้วลองใหม่"
            return
        self._snapshots = [*self._snapshots, self._df.copy(deep=True)]
        self.history = [*self.history, {"label": self._pending_label, "time": datetime.now().strftime("%H:%M:%S"), "impact": self.impact}]
        self._df = self._pending_df.copy(deep=True)
        self._clear_preview()
        self._invalidate_dashboard()
        self.category_filter = self.category_value = self.date_filter = self.date_start = self.date_end = ""
        self._refresh(stats)
        self.error, self.notice = "", "ใช้คำสั่งเรียบร้อย • สามารถ Undo ขั้นตอนล่าสุดได้"

    @rx.event
    def undo(self):
        if not self._snapshots:
            return
        self._df = self._snapshots[-1].copy(deep=True)
        self._snapshots = self._snapshots[:-1]
        self.history = self.history[:-1]
        self._clear_preview()
        self._invalidate_dashboard()
        self.category_filter = self.category_value = self.date_filter = self.date_start = self.date_end = ""
        self._refresh()
        self.error, self.notice = "", "ย้อนกลับขั้นตอนล่าสุดแล้ว"

    def _build_dashboard(self):
        if self._df is None:
            return
        filtered = filter_frame(self._df, self.category_filter, self.category_value,
                                self.date_filter, self.date_start, self.date_end)
        charts = auto_charts(filtered)
        descriptions = []
        if self.category_filter and self.category_value:
            descriptions.append(f"{self.category_filter} = {self.category_value}")
        if self.date_filter and (self.date_start or self.date_end):
            descriptions.append(f"{self.date_filter}: {self.date_start or '…'} → {self.date_end or '…'}")
        self.filter_description = " · ".join(descriptions) or "All rows · ไม่ใช้ตัวกรอง"
        self._filtered = filtered
        self._chart_specs = charts
        self.figures = [chart.figure() for chart in charts]
        self.dashboard_rows = f"{len(filtered):,}"
        self.dashboard_missing = f"{int(filtered.isna().sum().sum()):,}"
        self.kpi_total = f"{filtered[self.kpi_column].sum(min_count=1):,.2f}" if self.kpi_column in filtered else "—"
        self.dashboard_ready = True

    @rx.event
    def set_category_filter(self, value: str):
        self.category_filter, self.category_value = value, ""

    @rx.event
    def set_category_value(self, value: str):
        self.category_value = value

    @rx.event
    def set_date_filter(self, value: str):
        self.date_filter = value

    @rx.event
    def set_date_start(self, value: str):
        self.date_start = value

    @rx.event
    def set_date_end(self, value: str):
        self.date_end = value

    @rx.event
    def set_kpi_column(self, value: str):
        self.kpi_column = value
        if self._filtered is not None and value in self._filtered:
            self.kpi_total = f"{self._filtered[value].sum(min_count=1):,.2f}"

    @rx.event
    async def apply_filters(self):
        self.busy, self.error = True, ""
        yield
        try:
            self._build_dashboard()
            self.insight, self.insight_ok, self.has_custom = "", False, False
            self._revision += 1
        except Exception as exc:
            self.error = str(exc) if isinstance(exc, ValueError) else "ใช้ตัวกรองไม่ได้ กรุณาตรวจสอบค่าที่เลือก"
        finally:
            self.busy = False

    @rx.event
    async def clear_filters(self):
        self.category_filter = self.category_value = self.date_filter = self.date_start = self.date_end = ""
        async for event in self.apply_filters():
            yield event

    @rx.event
    def set_chart_type(self, value: str):
        self.chart_type = value

    @rx.event
    def set_chart_x(self, value: str):
        self.chart_x = value

    @rx.event
    def set_chart_y(self, value: str):
        self.chart_y = value

    @rx.event
    def build_custom(self):
        self.error = ""
        try:
            if self._filtered is None:
                self._build_dashboard()
            chart = custom_chart(self._filtered, self.chart_type, self.chart_x, self.chart_y)
            self.custom_figure = chart.figure()
            # A single custom chart is tracked separately from automatic charts.
            self.has_custom = True
        except ValueError as exc:
            self.error = str(exc)

    @rx.event(background=True)
    async def request_insight(self):
        async with self:
            if self.insight_busy or self._filtered is None or self._filtered.empty:
                return
            self.insight_busy = True
            revision = self._revision
            frame = self._filtered.copy(deep=True)
        try:
            summary = await asyncio.to_thread(insight_summary, frame)
            message, ok = await generate_insight(summary)
            async with self:
                if self._revision == revision:
                    self.insight, self.insight_ok = message, ok
        except Exception:
            async with self:
                if self._revision == revision:
                    self.insight = "ไม่สามารถสร้างสรุปได้ในขณะนี้ กรุณาลองใหม่ภายหลัง"
                    self.insight_ok = False
        finally:
            async with self:
                self.insight_busy = False

    @rx.event
    async def export_file(self, format: str):
        if self._df is None:
            return
        self.busy, self.error = True, ""
        yield
        try:
            name = Path(self.filename).stem
            if format == "csv":
                payload = await asyncio.to_thread(csv_bytes, self._df)
                target = f"{name}_clean.csv"
            elif format == "xlsx":
                payload = await asyncio.to_thread(excel_bytes, self._df)
                target = f"{name}_clean.xlsx"
            else:
                if not self.dashboard_ready:
                    self._build_dashboard()
                charts = list(self._chart_specs)
                if self.has_custom:
                    # Reconstruct from displayed figure to preserve exactly the
                    # built chart, even if builder controls subsequently change.
                    fig = self.custom_figure
                    trace = fig.data[0]
                    charts.insert(0, Chart(fig.layout.title.text,
                        "bar" if trace.type == "bar" else "scatter" if trace.mode == "markers" else "line",
                        list(trace.x), list(trace.y), xlabel=fig.layout.xaxis.title.text or "",
                        ylabel=fig.layout.yaxis.title.text or ""))
                payload = await asyncio.to_thread(pdf_bytes, self._filtered, charts,
                    [f"{h['label']} ({h['impact']})" for h in self.history],
                    self.insight if self.insight_ok else "", self.filename, self.filter_description)
                target = f"{name}_report.pdf"
            yield rx.download(data=payload, filename=target)
            self.notice = "เตรียมไฟล์ดาวน์โหลดเรียบร้อยแล้ว"
        except Exception:
            self.error = "สร้างไฟล์ไม่สำเร็จ กรุณาลองอีกครั้ง สำหรับ PDF โปรดตรวจว่าติดตั้ง WeasyPrint และ system libraries แล้ว"
        finally:
            self.busy = False
