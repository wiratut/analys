"""Shared chart data feeds both interactive Plotly and printable reports."""
from dataclasses import dataclass, field
import json

import duckdb
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .data import date_candidates, kind, profile, quote

ACCENT = "#0f766e"
PALETTE = [[0, "#9a3412"], [.5, "#f8fafc"], [1, ACCENT]]


@dataclass
class Chart:
    title: str
    kind: str
    x: list = field(default_factory=list)
    y: list = field(default_factory=list)
    z: list = field(default_factory=list)
    xlabel: str = ""
    ylabel: str = ""

    def figure(self) -> go.Figure:
        if self.kind == "heatmap":
            trace = go.Heatmap(x=self.x, y=self.y, z=self.z, zmin=-1, zmax=1,
                               colorscale=PALETTE, colorbar=dict(title="r"), hoverongaps=False)
        elif self.kind in ("histogram", "bar"):
            trace = go.Bar(x=self.x, y=self.y, marker_color=ACCENT,
                           hovertemplate="%{x}<br>%{y}<extra></extra>")
        else:
            trace = go.Scatter(x=self.x, y=self.y, mode="markers" if self.kind == "scatter" else "lines+markers",
                               line=dict(color=ACCENT, width=2), marker=dict(color=ACCENT, size=6))
        fig = go.Figure(trace)
        fig.update_layout(title=dict(text=self.title, font=dict(size=15)), template="plotly_white",
                          paper_bgcolor="white", plot_bgcolor="white", height=340,
                          margin=dict(l=50, r=24, t=60, b=65), font=dict(family="Inter, sans-serif", color="#475569", size=11),
                          xaxis_title=self.xlabel, yaxis_title=self.ylabel, showlegend=False,
                          xaxis=dict(gridcolor="#cbd5e1"), yaxis=dict(gridcolor="#cbd5e1"))
        return fig


def histogram(frame, col):
    values = pd.to_numeric(frame[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        return Chart(f"{col} · Distribution", "histogram", xlabel=col, ylabel="Rows")
    counts, edges = np.histogram(values, bins=min(24, max(1, int(np.sqrt(len(values))))))
    labels = [f"{a:,.3g}–{b:,.3g}" for a, b in zip(edges[:-1], edges[1:])]
    return Chart(f"{col} · Distribution", "histogram", labels, counts.tolist(), xlabel=col, ylabel="Rows")


def category_chart(frame, col):
    c = quote(col)
    with duckdb.connect(":memory:") as con:
        con.register("source", frame)
        data = con.execute(f"SELECT CAST({c} AS VARCHAR) AS label, count(*) AS n FROM source WHERE {c} IS NOT NULL GROUP BY 1 ORDER BY n DESC, label LIMIT 15").fetchall()
    return Chart(f"{col} · Top categories", "bar", [r[0] for r in data], [r[1] for r in data], xlabel=col, ylabel="Rows")


def date_chart(frame, col):
    dates = pd.to_datetime(frame[col], format="mixed", errors="coerce", utc=True)
    data = pd.DataFrame({"day": dates.dt.tz_localize(None).dt.normalize()}).dropna()
    with duckdb.connect(":memory:") as con:
        con.register("dates", data)
        rows = con.execute("SELECT day, count(*) FROM dates GROUP BY day ORDER BY day").fetchall()
    return Chart(f"{col} · Rows over time", "line", [str(r[0].date()) for r in rows], [r[1] for r in rows], xlabel="Day", ylabel="Rows")


def auto_charts(frame: pd.DataFrame) -> list[Chart]:
    if frame.empty:
        return []
    dates = date_candidates(frame)
    charts = []
    numeric = []
    for col in frame:
        if kind(frame[col]) == "numeric":
            charts.append(histogram(frame, col))
            numeric.append(col)
        elif col in dates:
            charts.append(date_chart(frame, col))
        else:
            charts.append(category_chart(frame, col))
    if len(numeric) >= 2:
        corr = frame[numeric].replace([np.inf, -np.inf], np.nan).corr()
        charts.append(Chart("Numeric relationships · Pearson r", "heatmap", numeric, numeric,
                            [[None if pd.isna(v) else float(v) for v in row] for row in corr.to_numpy()]))
    return charts


def custom_chart(frame: pd.DataFrame, chart_type: str, x: str, y: str) -> Chart:
    if frame.empty:
        raise ValueError("ไม่มีข้อมูลในตัวกรองนี้ กรุณาปรับตัวกรองก่อน")
    if x not in frame:
        raise ValueError("กรุณาเลือกแกน X")
    if chart_type == "Histogram":
        if kind(frame[x]) != "numeric":
            raise ValueError("Histogram ต้องใช้แกน X เป็นตัวเลข")
        return histogram(frame, x)
    if y not in frame or kind(frame[y]) != "numeric":
        raise ValueError("แกน Y ต้องเป็นคอลัมน์ตัวเลข")
    if chart_type == "Scatter":
        if kind(frame[x]) != "numeric":
            raise ValueError("Scatter ต้องใช้แกน X และ Y เป็นตัวเลข")
        values = frame[[x, y]].dropna().head(5000)
        return Chart(f"{x} × {y} · First 5,000 non-null rows", "scatter", values.iloc[:, 0].tolist(), values.iloc[:, 1].tolist(), xlabel=x, ylabel=y)
    if chart_type not in ("Bar", "Line"):
        raise ValueError("ไม่รู้จักชนิดกราฟ")
    data = frame[[x, y]].copy() if x != y else frame[[x]].copy()
    if x in date_candidates(frame):
        data[x] = pd.to_datetime(data[x], format="mixed", errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    with duckdb.connect(":memory:") as con:
        con.register("source", data)
        rows = con.execute(f"SELECT {quote(x)}, sum({quote(y)}) FROM source WHERE {quote(x)} IS NOT NULL GROUP BY 1 ORDER BY 1").fetchall()
    return Chart(f"{y} by {x} · Sum", chart_type.lower(), [str(r[0]) for r in rows],
                 [float(r[1]) if r[1] is not None else 0 for r in rows], xlabel=x, ylabel=f"Sum of {y}")


def insight_summary(frame: pd.DataFrame) -> str:
    stats = profile(frame)
    # Bound the payload without including source row samples.
    summary = {key: stats[key] for key in ("rows", "columns", "missing", "duplicates")}
    summary["column_statistics"] = stats["schema"][:30]
    summary["top_categories"] = {}
    nums = [c for c in frame if kind(frame[c]) == "numeric"][:20]
    for col in [c for c in frame if kind(frame[c]) == "categorical"][:6]:
        summary["top_categories"][col] = {str(k)[:100]: int(v) for k, v in frame[col].value_counts().head(5).items()}
    pairs = []
    if len(nums) > 1:
        corr = frame[nums].corr()
        for i, a in enumerate(nums):
            for b in nums[i + 1:]:
                r = corr.loc[a, b]
                if pd.notna(r) and abs(r) >= .5:
                    pairs.append({"columns": [a, b], "Pearson_r": round(float(r), 3),
                                  "paired_rows": int(frame[[a, b]].dropna().shape[0])})
    summary["correlations_not_significance_tests"] = pairs[:15]
    summary["trends"] = []
    for col in date_candidates(frame)[:2]:
        chart = date_chart(frame, col)
        if chart.y:
            first, last = chart.y[0], chart.y[-1]
            summary["trends"].append({"date_column": col, "metric": "row count per observed day",
                "first_day": chart.x[0], "last_day": chart.x[-1], "first_count": first, "last_count": last,
                "change_pct": round((last - first) / first * 100, 2) if first and len(chart.y) > 1 else None,
                "caveat": "First/last days may be partial; missing days are not zero-filled."})
    return json.dumps(summary, ensure_ascii=False, default=str)[:24000]
