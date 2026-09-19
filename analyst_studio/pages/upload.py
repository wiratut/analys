import reflex as rx
from ..state import StudioState as S
from ..components.common import icon, panel, section_title, data_table, field, select
from ..services.data import ENCODINGS, DELIMITERS


def upload_page():
    return rx.box(
        section_title("01 / GET STARTED", "Good insights start with good data.",
                      "อัปโหลดข้อมูล สำรวจคุณภาพ และเปลี่ยนไฟล์ที่ยุ่งเหยิงให้เป็น dashboard ที่อ่านเข้าใจง่าย — ทุกขั้นตอนอยู่ในที่เดียว"),
        rx.box(
            panel(
                rx.hstack(rx.heading("Import a dataset", size="4"), rx.spacer(), rx.badge("CSV", variant="soft", color_scheme="gray"), align="center"),
                rx.text("เริ่มต้นจากไฟล์ของคุณ", class_name="text-sm text-slate-600 mt-1 mb-6"),
                rx.upload(
                    rx.center(
                        rx.center(icon("file-up", 30, color="#0f766e"), class_name="w-16 h-16 rounded-2xl bg-teal-50 mb-5"),
                        rx.text("Drop your CSV here", class_name="text-lg font-semibold text-slate-800"),
                        rx.text("ลากไฟล์มาวาง หรือคลิกเพื่อเลือกไฟล์", class_name="text-sm text-slate-600 mt-2"),
                        rx.box("Browse files", class_name="rounded-lg bg-teal-900 text-white text-sm font-medium px-5 py-2.5 mt-5"),
                        rx.text("CSV · UTF-8 / UTF-16 / Thai encoding · Up to 25 MB", class_name="text-[11px] text-slate-600 mt-5"),
                        class_name="flex-col py-12 px-4",
                    ), id="csv-upload", accept={"text/csv": [".csv"]}, multiple=False, max_files=1,
                    max_size=25 * 1024 * 1024, disabled=S.busy,
                    on_drop_rejected=rx.toast.error("กรุณาเลือกไฟล์ CSV หนึ่งไฟล์ ขนาดไม่เกิน 25 MB"),
                    class_name="rounded-xl border-2 border-dashed border-slate-300 bg-teal-50 hover:border-teal-600 transition-colors cursor-pointer",
                ),
                rx.box(
                    field("Encoding", select(list(ENCODINGS), S.csv_encoding, S.set_csv_encoding)),
                    field("ตัวคั่นข้อมูล", select(list(DELIMITERS), S.csv_delimiter, S.set_csv_delimiter)),
                    class_name="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5",
                ),
                rx.text("Auto ตรวจรูปแบบให้อัตโนมัติ หากภาษาเพี้ยนหรือจำนวนคอลัมน์ไม่ถูกต้อง ให้เลือกรูปแบบเองก่อนอัปโหลดใหม่",
                        class_name="text-xs text-slate-600 mt-2"),
                rx.hstack(rx.foreach(rx.selected_files("csv-upload"), lambda name: rx.text(name, size="2", color="#0f766e")),
                          rx.spacer(), rx.button("Upload & profile", icon("arrow-right", 15),
                          on_click=S.upload(rx.upload_files(upload_id="csv-upload")), loading=S.busy,
                          disabled=rx.selected_files("csv-upload").length() == 0, size="3"), class_name="mt-5", align="center", wrap="wrap"),
                rx.cond(S.loaded, rx.callout("การอัปโหลดไฟล์ใหม่จะแทนที่ข้อมูลและประวัติ cleaning ของ session นี้", icon="info", color_scheme="amber", class_name="mt-4")),
            ),
            rx.box(
                panel(rx.hstack(rx.center(icon("flask-conical", 20, color="#0f766e"), class_name="w-10 h-10 rounded-lg bg-teal-50"),
                                 rx.badge("SAMPLE DATA", variant="soft", color_scheme="teal"), align="center", justify="between"),
                      rx.heading("Explore before you upload", size="4", class_name="mt-5 mb-2"),
                      rx.text("ลองใช้ข้อมูลยอดขายตัวอย่างที่มี missing values, แถวซ้ำ และรูปแบบวันที่ต่างกัน", class_name="text-sm text-slate-600 leading-6"),
                      rx.box(rx.hstack(icon("file-spreadsheet", 18, color="#64748b"), rx.box(
                          rx.text("sample_sales.csv", class_name="text-xs font-semibold text-slate-700"),
                          rx.text("128 rows · 8 columns", class_name="text-[11px] text-slate-600 mt-1")), spacing="3", align="center"),
                          class_name="bg-slate-50 rounded-lg p-4 my-5"),
                      rx.button("Try sample dataset", icon("arrow-up-right", 16), on_click=S.load_sample,
                                variant="outline", size="3", width="100%", disabled=S.busy)),
                rx.box(rx.hstack(icon("lock-keyhole", 16, color="#475569"),
                                 rx.text("A fresh workspace, every session", class_name="text-xs font-semibold text-slate-600")),
                       rx.text("ไม่ต้องสมัครบัญชี ไม่มีฐานข้อมูลถาวร ส่งออกผลลัพธ์ก่อนปิด session", class_name="text-xs text-slate-600 leading-6 mt-2"),
                       class_name="p-5 mt-3"),
                class_name="min-w-0",
            ), class_name="grid grid-cols-1 xl:grid-cols-[1.7fr_1fr] gap-6",
        ),
        rx.box(*[rx.hstack(rx.center(icon(name, 19, color="#64748b"), class_name="w-10 h-10 rounded-lg bg-white border border-slate-300 shrink-0"),
            rx.box(rx.text(title, class_name="text-sm font-semibold text-slate-700"), rx.text(desc, class_name="text-xs text-slate-600 mt-1")), align="center", spacing="3")
            for name, title, desc in [("scan-search", "Know your data", "Schema, missing values & outliers"),
                                      ("sliders-horizontal", "Clean with confidence", "Preview every change. Undo anytime."),
                                      ("chart-no-axes-combined", "See the bigger picture", "Automatic charts & optional AI insights")]],
            class_name="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10"),
        rx.cond(S.loaded, rx.box(rx.heading("Current dataset preview", size="4", class_name="mb-4"),
                                data_table(S.columns, S.table_rows), class_name="mt-8")),
    )
