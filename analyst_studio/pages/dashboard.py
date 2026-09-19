import reflex as rx
from ..state import StudioState as S
from ..components.common import panel, section_title, stat, field, select, icon, next_button


def filters():
    return panel(
        rx.hstack(icon("list-filter", 17), rx.heading("Explore a slice", size="3"), rx.spacer(),
                  rx.button("Reset filters", on_click=S.clear_filters, variant="ghost", size="1", disabled=S.busy), align="center", class_name="mb-4"),
        rx.box(field("Category", select(S.category_columns, S.category_filter, S.set_category_filter, "ทุกหมวดหมู่")),
               field("Category value", select(S.category_values, S.category_value, S.set_category_value, "ทุกค่า")),
               field("Date column", select(S.date_columns, S.date_filter, S.set_date_filter, "ไม่กรองวันที่")),
               field("From", rx.input(type="date", value=S.date_start, on_change=S.set_date_start, size="3", width="100%", aria_label="From date", disabled=S.busy)),
               field("To", rx.input(type="date", value=S.date_end, on_change=S.set_date_end, size="3", width="100%", aria_label="To date", disabled=S.busy)),
               class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4"),
        rx.hstack(rx.text("กราฟ, KPI, AI และ PDF ใช้ตัวกรองเดียวกัน • CSV/Excel ส่งออกข้อมูล clean ทั้งชุด", class_name="text-xs text-slate-600"),
                  rx.spacer(), rx.button("Apply filters", on_click=S.apply_filters, size="2", disabled=S.busy),
                  class_name="mt-4", wrap="wrap", align="center"),
    )


def ai_section():
    return rx.box(
        rx.hstack(rx.center(icon("sparkles", 18, color="#0f766e"), class_name="rounded-lg bg-white w-9 h-9 border border-teal-100"),
                  rx.box(rx.hstack(rx.heading("A second perspective", size="4"), rx.badge("AI ASSISTED", size="1", color_scheme="teal"), align="center", wrap="wrap"),
                         rx.text("ข้อความตีความจาก Gemini แยกจากสถิติที่คำนวณจริง", class_name="text-xs text-slate-600 mt-1")),
                  rx.spacer(), rx.button("Generate insights", on_click=S.request_insight, loading=S.insight_busy,
                      disabled=S.busy | ~S.dashboard_ready | (S.dashboard_rows == "0"), size="2", variant="outline"),
                  align="center", wrap="wrap", spacing="3"),
        rx.cond(S.insight != "", rx.text(S.insight, class_name="text-sm leading-7 text-slate-600 mt-5 whitespace-pre-wrap"),
                rx.text("ให้ AI ช่วยเล่าสิ่งที่ข้อมูลบอก ทั้งรูปแบบที่น่าสนใจ ความสัมพันธ์ และจุดที่ควรตรวจสอบ", class_name="text-sm text-slate-600 mt-5")),
        rx.text("เมื่อกด Generate จะส่งเฉพาะสถิติสรุปและชื่อหมวดหมู่ไปยัง Google ไม่มีการส่งตัวอย่างแถวข้อมูล • โปรดตรวจสอบการตีความก่อนใช้งาน", class_name="text-[11px] text-slate-600 leading-5 mt-4"),
        class_name="rounded-xl border-2 border-teal-400 bg-teal-50 p-6 mt-6",
    )


def dashboard_page():
    return rx.box(
        section_title("04 / DISCOVER", "Your data, in perspective.", "กราฟที่สร้างอัตโนมัติตามชนิดข้อมูล พร้อมตัวกรองและเครื่องมือสร้างกราฟของคุณเอง"),
        rx.hstack(rx.badge(S.filename, color_scheme="gray"), rx.text(S.filter_description, class_name="text-xs text-slate-600"),
                  rx.spacer(), next_button("Export results", "Export"), align="center", wrap="wrap", class_name="mb-6"),
        filters(),
        rx.box(stat("FILTERED ROWS", S.dashboard_rows, "ตามตัวกรองที่ Apply แล้ว", "rows-3"),
               stat("COLUMNS", S.total_columns, "ในข้อมูลที่ clean แล้ว", "columns-3"),
               stat("MISSING CELLS", S.dashboard_missing, "ในข้อมูลที่กรองแล้ว", "circle-dashed"),
               rx.box(rx.text("NUMERIC TOTAL", class_name="text-xs font-medium text-slate-600"),
                      rx.text(S.kpi_total, class_name="text-3xl font-semibold tracking-tight text-slate-900 mt-3 tabular-nums"),
                      rx.box(select(S.numeric_columns, S.kpi_column, S.set_kpi_column, "ไม่มีคอลัมน์ตัวเลข"), class_name="mt-2"),
                      class_name="rounded-xl border border-slate-300 bg-white shadow-sm p-5 min-w-0"),
               class_name="grid grid-cols-2 xl:grid-cols-4 gap-4 my-6"),
        rx.hstack(rx.heading("Automatic overview", size="4"), rx.spacer(),
                  rx.text("Top 15 categories · Daily row counts · Pearson correlation", class_name="text-xs text-slate-600"),
                  align="center", wrap="wrap", class_name="mb-4"),
        rx.cond(S.figures.length() > 0,
                rx.box(rx.foreach(S.figures, lambda fig: rx.box(rx.plotly(data=fig, config={"displayModeBar": False, "responsive": True}, width="100%"),
                    class_name="bg-white rounded-xl border border-slate-300 overflow-hidden min-w-0 p-2")),
                    class_name="grid grid-cols-1 xl:grid-cols-2 gap-5"),
                panel(rx.center(icon("chart-no-axes-combined", 32, color="#475569"),
                    rx.text("ไม่มีข้อมูลในตัวกรองนี้", class_name="text-sm text-slate-600 mt-3"),
                    rx.text("ลองปรับตัวกรองหรือล้างตัวกรองเพื่อดูข้อมูลทั้งหมด", class_name="text-xs text-slate-600 mt-2"), class_name="flex-col py-8"))),
        ai_section(),
        rx.box(panel(rx.hstack(icon("chart-column-increasing", 18), rx.heading("Build your own view", size="4"), align="center", class_name="mb-5"),
            rx.box(field("Chart type", select(["Bar", "Line", "Scatter", "Histogram"], S.chart_type, S.set_chart_type)),
                   field("X axis", select(S.columns, S.chart_x, S.set_chart_x)),
                   field("Y axis · numeric", select(S.numeric_columns, S.chart_y, S.set_chart_y)),
                   class_name="grid grid-cols-1 md:grid-cols-3 gap-4"),
            rx.hstack(rx.text("Bar / Line = sum ของ Y ตาม X • Histogram ใช้เฉพาะ X • Scatter แสดงสูงสุด 5,000 แถว", class_name="text-xs text-slate-600"),
                      rx.spacer(), rx.button("Create chart", on_click=S.build_custom, size="2", disabled=S.busy), class_name="mt-4", wrap="wrap", align="center"),
            rx.cond(S.has_custom, rx.box(rx.plotly(data=S.custom_figure, config={"displayModeBar": False, "responsive": True}, width="100%"), class_name="mt-5"))), class_name="mt-6"),
    )
