import reflex as rx
from ..state import StudioState as S
from ..services.cleaning import METHODS
from ..components.common import panel, section_title, data_table, field, select, icon, next_button


def clean_page():
    multi = (S.action == "Duplicates") | ((S.action == "Columns") & ((S.method == "reorder") | (S.method == "merge")))
    return rx.box(
        section_title("03 / PREPARE", "A little cleaner. A lot clearer.", "เลือกคำสั่ง ดูตัวอย่างผลลัพธ์ แล้วค่อย Apply ทุกการเปลี่ยนแปลงย้อนกลับได้"),
        rx.hstack(rx.badge(S.filename, color_scheme="gray"), rx.text(S.total_rows + " rows · " + S.total_columns + " columns", class_name="text-xs text-slate-600"),
                  rx.spacer(), next_button("Build dashboard", "Dashboard"), align="center", wrap="wrap", class_name="mb-6"),
        rx.box(
            panel(rx.hstack(icon("sliders-horizontal", 18), rx.heading("Cleaning workbench", size="4"), align="center", class_name="mb-6"),
                rx.box(field("Action", select(list(METHODS), S.action, S.set_action)),
                       field("Method", select(S.methods, S.method, S.set_method)),
                       rx.cond(~multi, field("Column", select(S.columns, S.column, S.set_column))),
                       class_name="grid grid-cols-1 md:grid-cols-2 gap-4"),
                rx.text(S.help_text, class_name="text-xs leading-6 bg-slate-50 border border-slate-300 rounded-lg p-3 my-5 text-slate-600"),
                rx.cond(multi,
                    rx.box(rx.text("Columns · คลิกตามลำดับที่ต้องการ", class_name="text-xs font-semibold text-slate-600 mb-3"),
                        rx.box(rx.foreach(S.columns, lambda col: rx.button(col, on_click=S.toggle_column(col),
                            variant=rx.cond(S.selected_columns.contains(col), "solid", "outline"), color_scheme="teal", size="1", disabled=S.busy)),
                            class_name="flex flex-wrap gap-2"),
                        rx.text(S.selected_columns.join(" → "), class_name="text-xs text-teal-800 mt-3"), class_name="mb-5")),
                rx.box(field("Value / pattern / new name", rx.input(value=S.value, on_change=S.set_value,
                           placeholder="ค่าหรือรูปแบบที่ต้องการ", size="3", width="100%", aria_label="Cleaning value", disabled=S.busy)),
                       field("Replacement / separator", rx.input(value=S.replacement, on_change=S.set_replacement,
                           placeholder="ใช้กับ regex replace หรือ merge", size="3", width="100%", aria_label="Replacement", disabled=S.busy)),
                       class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5"),
                rx.button(icon("eye", 16), "Preview changes", on_click=S.preview_action, size="3", loading=S.busy, width="100%"),
            ),
            panel(rx.hstack(rx.heading("Pipeline history", size="4"), rx.spacer(),
                            rx.button(icon("undo-2", 14), "Undo", on_click=S.undo, variant="outline", size="1", disabled=(S.history.length() == 0) | S.busy), align="center", class_name="mb-5"),
                rx.cond(S.history.length() == 0,
                    rx.center(icon("list-ordered", 28, color="#64748b"), rx.text("A clean slate", class_name="text-sm font-semibold text-slate-600 mt-4"),
                        rx.text("คำสั่งที่ Apply แล้วจะปรากฏที่นี่", class_name="text-xs text-slate-600 mt-2"), class_name="flex-col py-12"),
                    rx.box(rx.foreach(S.history, lambda item, i: rx.box(
                        rx.hstack(rx.badge(i + 1, color_scheme="teal"), rx.text(item["time"], class_name="text-[10px] text-slate-600"), align="center"),
                        rx.text(item["label"], class_name="text-xs font-semibold text-slate-700 mt-2 break-words"),
                        rx.text(item["impact"], class_name="text-[11px] text-slate-600 mt-2"),
                        class_name="border-l-2 border-teal-400 pl-4 pb-5 mb-2")), max_height="430px", overflow_y="auto")),
            ), class_name="grid grid-cols-1 xl:grid-cols-[1.6fr_1fr] gap-6",
        ),
        rx.cond(S.pending,
            rx.box(panel(rx.hstack(rx.heading("Before & after", size="4"), rx.spacer(), rx.badge("NOT APPLIED YET", color_scheme="amber"), align="center", wrap="wrap"),
                rx.text(S.impact, class_name="text-sm text-slate-600 mt-2 mb-5"),
                rx.box(rx.box(rx.text("BEFORE", class_name="text-xs tracking-widest font-semibold text-slate-600 mb-3"), data_table(S.before_columns, S.before_rows)),
                       rx.box(rx.text("AFTER", class_name="text-xs tracking-widest font-semibold text-teal-800 mb-3"), data_table(S.after_columns, S.after_rows)),
                       class_name="grid grid-cols-1 xl:grid-cols-2 gap-5"),
                rx.hstack(rx.text("แสดง 30 แถวแรกของแต่ละชุด", class_name="text-xs text-slate-600"), rx.spacer(),
                          rx.button(icon("check", 16), "Apply changes", on_click=S.apply_preview, size="3", disabled=S.busy),
                          align="center", class_name="mt-5")), class_name="mt-6"),
            rx.box(panel(rx.heading("Current data", size="4", class_name="mb-4"), data_table(S.columns, S.table_rows)), class_name="mt-6")),
    )
