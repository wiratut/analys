import reflex as rx
from ..state import StudioState as S
from ..components.common import panel, section_title, stat, data_table, next_button


def profile_page():
    return rx.box(
        section_title("02 / UNDERSTAND", "Meet your data.", "ตรวจคุณภาพข้อมูลก่อนเริ่มทำความสะอาด สถิติทั้งหมดคำนวณจากข้อมูลจริงใน session นี้"),
        rx.hstack(rx.badge(S.filename, color_scheme="gray", size="2"), rx.spacer(), next_button("Start cleaning", "Clean"), class_name="mb-6", align="center", wrap="wrap"),
        rx.box(stat("TOTAL ROWS", S.total_rows, "ทุกแถวใน dataset", "rows-3"),
               stat("COLUMNS", S.total_columns, "รวมทุกชนิดข้อมูล", "columns-3"),
               stat("MISSING CELLS", S.missing_cells, "ช่องข้อมูลที่ไม่มีค่า", "circle-dashed"),
               stat("DUPLICATE ROWS", S.duplicate_rows, "เปรียบเทียบทุกคอลัมน์", "copy"),
               class_name="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-6"),
        panel(rx.hstack(rx.heading("Column profile", size="4"), rx.spacer(),
                        rx.badge(S.completeness + "% complete", variant="soft", color_scheme="teal"), align="center", class_name="mb-2"),
              rx.text("สถิติตัวเลขไม่นับค่าว่างและ ±inf • Std = sample standard deviation • Outliers = IQR × 1.5", class_name="text-xs text-slate-600 mb-5"),
              data_table(["Column", "Data type", "Missing %", "Unique", "Mean", "Median", "Min", "Max", "Std", "Outliers"], S.schema_rows, "520px")),
        rx.box(panel(rx.hstack(rx.heading("Data preview", size="4"), rx.spacer(), rx.text("FIRST 30 ROWS", class_name="text-[10px] text-slate-600 tracking-widest"), align="center", class_name="mb-5"),
                     data_table(S.columns, S.table_rows)), class_name="mt-6"),
        rx.hstack(rx.text("ค่าที่หายไปแสดงเป็น — • outlier เป็นสัญญาณให้ตรวจสอบ ไม่ได้หมายความว่าข้อมูลผิดเสมอ", class_name="text-xs text-slate-600"),
                  rx.spacer(), next_button("Continue to cleaning", "Clean"), class_name="mt-6", wrap="wrap", align="center"),
    )
