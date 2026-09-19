import reflex as rx
from ..state import StudioState as S
from ..components.common import panel, section_title, icon, data_table


def export_card(name, title, subtitle, details, format, button):
    return panel(
        rx.center(icon(name, 25, color="#0f766e"), class_name="w-12 h-12 rounded-xl bg-teal-50 mb-6"),
        rx.heading(title, size="5"), rx.text(subtitle, class_name="text-sm text-slate-600 leading-6 mt-2 min-h-12"),
        rx.box(*[rx.hstack(icon("check", 14, color="#64748b"), rx.text(item, class_name="text-xs text-slate-600"), spacing="2", class_name="mb-3") for item in details], class_name="my-6"),
        rx.button(icon("download", 16), button, on_click=S.export_file(format), loading=S.busy,
                  size="3", width="100%", variant="solid" if format == "pdf" else "outline"),
    )


def export_page():
    return rx.box(
        section_title("05 / TAKE IT FORWARD", "Ready for what comes next.", "ดาวน์โหลดข้อมูลที่ทำความสะอาดแล้ว หรือแบ่งปันภาพรวมการวิเคราะห์เป็นรายงาน PDF"),
        rx.hstack(rx.badge(S.filename, color_scheme="gray"), rx.text(S.total_rows + " rows · " + S.history.length().to_string() + " cleaning steps", class_name="text-xs text-slate-600"),
                  class_name="mb-7", align="center"),
        rx.box(
            export_card("file-text", "Clean CSV", "ไฟล์ข้อมูลพร้อมนำไปใช้งานต่อกับเครื่องมือวิเคราะห์อื่น", ["ข้อมูล clean ทุกแถว ทุกคอลัมน์", "UTF-8 พร้อม BOM สำหรับภาษาไทย", "ไม่ใช้ตัวกรองของ dashboard"], "csv", "Download CSV"),
            export_card("file-spreadsheet", "Excel workbook", "ข้อมูลที่จัดเรียบร้อยแล้ว สำหรับเปิดใน Excel หรือส่งต่อให้ทีม", ["ข้อมูล clean ทั้งชุดในหนึ่ง sheet", "คงชนิดตัวเลขและวันที่", "ข้อความสูตรเก็บเป็นข้อความ"], "xlsx", "Download Excel"),
            export_card("file-chart-column", "Insight report", "ภาพรวมที่พร้อมอ่าน พร้อมกราฟ สถิติ และบริบทการวิเคราะห์", ["ใช้ตัวกรองที่ Apply บน dashboard", "กราฟหลักสูงสุด 8 กราฟ + summary stats", "Pipeline และ AI insight ที่สร้างสำเร็จ"], "pdf", "Download PDF"),
            class_name="grid grid-cols-1 xl:grid-cols-3 gap-6",
        ),
        rx.box(panel(rx.hstack(icon("info", 17, color="#64748b"), rx.heading("Report scope", size="3"), align="center"),
            rx.text(S.filter_description, class_name="text-sm text-slate-600 mt-3"),
            rx.text("PDF: " + S.dashboard_rows + " rows · CSV / Excel: " + S.total_rows + " rows", class_name="text-xs text-slate-600 mt-2"),
            rx.cond(S.insight_ok, rx.badge("AI interpretation included", color_scheme="teal", class_name="mt-3"),
                    rx.text("ยังไม่มี AI insight ที่สร้างสำเร็จ — PDF ยังคงมีสถิติและกราฟครบ", class_name="text-xs text-slate-600 mt-3"))), class_name="mt-6"),
        rx.box(panel(rx.heading("Final data preview", size="4", class_name="mb-5"), data_table(S.columns, S.table_rows)), class_name="mt-6"),
    )
