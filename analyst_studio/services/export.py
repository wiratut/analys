"""In-memory downloads. PDF charts use the dashboard's prepared data."""
import base64
from datetime import datetime, timezone
from html import escape
from io import BytesIO
import os
import threading

import pandas as pd

from .analytics import ACCENT, Chart
from .data import profile

os.environ.setdefault("MPLCONFIGDIR", "/tmp/analyst-studio-matplotlib")
_render_lock = threading.Lock()


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


def excel_bytes(frame: pd.DataFrame) -> bytes:
    from openpyxl import Workbook
    from openpyxl.cell.cell import WriteOnlyCell
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Clean data")
    for row in [list(frame.columns)]:
        cells = []
        for v in row:
            cell = WriteOnlyCell(sheet, value=v)
            cell.data_type = "s"
            cells.append(cell)
        sheet.append(cells)
    for row in frame.itertuples(index=False, name=None):
        cells = []
        for v in row:
            value = None if pd.isna(v) else v
            if isinstance(value, float) and value in (float("inf"), float("-inf")):
                value = str(value)
            if isinstance(value, pd.Timestamp):
                value = value.to_pydatetime().replace(tzinfo=None)
            cell = WriteOnlyCell(sheet, value=value)
            if isinstance(value, str):
                cell.data_type = "s"
            cells.append(cell)
        sheet.append(cells)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def chart_png(chart: Chart) -> bytes:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib import font_manager
    import numpy as np
    with _render_lock:
        fig = Figure(figsize=(9, 3.8), layout="constrained")
        FigureCanvasAgg(fig)
        # Use a system Thai-capable font when installed, with an ordinary fallback.
        names = {font.name for font in font_manager.fontManager.ttflist}
        thai = next((n for n in ("Noto Sans Thai", "Garuda", "Loma") if n in names), None)
        family = ["DejaVu Sans", thai] if thai else ["DejaVu Sans"]
        ax = fig.add_subplot()
        if chart.kind == "heatmap":
            matrix = np.array([[np.nan if v is None else v for v in row] for row in chart.z], dtype=float)
            image = ax.imshow(matrix, cmap="Blues", vmin=-1, vmax=1, aspect="auto")
            fig.colorbar(image, ax=ax, label="Pearson r")
            ax.set_xticks(range(len(chart.x)), chart.x, rotation=35, ha="right", fontfamily=family)
            ax.set_yticks(range(len(chart.y)), chart.y, fontfamily=family)
        else:
            if chart.kind in ("bar", "histogram"):
                ax.bar(range(len(chart.x)), chart.y, color=ACCENT, width=.7)
            elif chart.kind == "scatter":
                ax.scatter(chart.x, chart.y, color=ACCENT, s=10, alpha=.6)
            else:
                ax.plot(range(len(chart.x)), chart.y, color=ACCENT, linewidth=2)
            if chart.kind != "scatter":
                step = max(1, len(chart.x) // 10)
                positions = list(range(0, len(chart.x), step))
                ax.set_xticks(positions, [str(chart.x[i])[:24] for i in positions], rotation=25, ha="right", fontfamily=family)
            ax.grid(axis="y", alpha=.15)
            ax.set_axisbelow(True)
        ax.set_title(chart.title, loc="left", fontsize=12, pad=16, fontfamily=family)
        ax.set_xlabel(chart.xlabel, fontfamily=family)
        ax.set_ylabel(chart.ylabel, fontfamily=family)
        ax.tick_params(labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        output = BytesIO()
        fig.savefig(output, format="png", dpi=135)
        return output.getvalue()


def pdf_bytes(frame: pd.DataFrame, charts: list[Chart], history: list[str], insight: str,
              filename: str, filter_description: str) -> bytes:
    from weasyprint import HTML
    stats = profile(frame)
    rows = ""
    for c in stats["schema"]:
        def fmt(v):
            return "—" if v is None else f"{v:,.3g}"
        rows += "<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in
            [c["column"], c["dtype"], f'{c["missing_pct"]:.1f}%', c["unique"],
             fmt(c["mean"]), fmt(c["median"]), fmt(c["min"]), fmt(c["max"]), fmt(c["std"])]) + "</tr>"
    # PDF includes up to eight principal charts, explicitly documented in report.
    selected = charts[:7]
    correlation = next((c for c in charts if c.kind == "heatmap"), None)
    if correlation and correlation not in selected:
        selected.append(correlation)
    else:
        selected = charts[:8]
    images = "".join('<div class="chart"><img src="data:image/png;base64,' +
                     base64.b64encode(chart_png(c)).decode() + '"></div>' for c in selected)
    pipeline = "".join(f"<li>{escape(item)}</li>" for item in history) or "<li>No cleaning actions applied.</li>"
    ai = f'<section class="ai"><h2>AI-assisted interpretation</h2><p>{escape(insight)}</p></section>' if insight else ""
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
    @page {{ size:A4; margin:18mm; @bottom-right {{ content:counter(page); font-size:9pt; color:#64748b; }} }}
    body {{ font-family: 'Noto Sans Thai', 'Garuda', sans-serif; color:#243348; font-size:9pt; }}
    h1 {{ font-size:25pt; color:{ACCENT}; margin-bottom:5px; }} h2 {{ font-size:14pt; margin-top:25px; }}
    .meta {{ color:#64748b; }} .kpis {{ padding:16px; background:#f0f5fc; margin:20px 0; }}
    table {{ border-collapse:collapse; width:100%; font-size:7pt; table-layout:fixed; overflow-wrap:anywhere; }}
    th,td {{ padding:6px 3px; border-bottom:1px solid #e2e8f0; text-align:left; }} th {{ background:#f1f5f9; }}
    .chart {{ break-inside:avoid; margin-top:20px; }} img {{ width:100%; }}
    .ai {{ background:#f0f5fc; border-left:3px solid {ACCENT}; padding:15px; }}
    .ai p {{ white-space:pre-wrap; }} li {{ margin-bottom:6px; }}
    </style></head><body><p class="meta">ANALYST STUDIO / DATA REPORT</p>
    <h1>Dataset overview</h1><p>{escape(filename)}</p>
    <p class="meta">Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · {escape(filter_description)}</p>
    <div class="kpis">Rows: {stats['rows']:,} &nbsp; | &nbsp; Columns: {stats['columns']} &nbsp; | &nbsp;
    Missing cells: {stats['missing']:,} &nbsp; | &nbsp; Duplicate rows: {stats['duplicates']:,}</div>
    <h2>Column statistics</h2><p class="meta">Numeric statistics exclude missing and infinite values.</p><table><thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Unique</th>
    <th>Mean</th><th>Median</th><th>Min</th><th>Max</th><th>Std</th></tr></thead><tbody>{rows}</tbody></table>
    <h2>Dashboard charts</h2><p class="meta">Showing {len(selected)} of {len(charts)} charts.
    Correlations describe association, not causation or statistical significance.</p>{images}
    <h2>Cleaning pipeline</h2><ol>{pipeline}</ol>{ai}</body></html>"""
    return HTML(string=html).write_pdf()
