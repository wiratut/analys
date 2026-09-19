import reflex as rx

from ..state import StudioState as S
from .common import icon

STEPS = [("Upload", "Import your dataset", "upload"), ("Profile", "Understand the data", "scan-search"),
         ("Clean", "Prepare with confidence", "sliders-horizontal"), ("Dashboard", "Find the story", "chart-no-axes-combined"),
         ("Export", "Take your work with you", "download")]


def sidebar():
    return rx.box(
        rx.hstack(rx.center(icon("chart-no-axes-column-increasing", 23, color="white"),
                            class_name="w-10 h-10 bg-teal-900 rounded-xl"),
                  rx.box(rx.text("Analyst", class_name="text-lg font-bold tracking-tight text-slate-900"),
                         rx.text("STUDIO", class_name="text-[10px] tracking-[0.24em] font-semibold text-slate-600")),
                  spacing="3", align="center", class_name="px-5 py-7"),
        rx.text("WORKSPACE", class_name="text-[10px] tracking-widest font-semibold text-slate-600 px-5 mt-6 mb-3 hidden lg:block"),
        rx.box(*[
            rx.el.button(
                rx.hstack(icon(name, 18), rx.box(rx.text(title, class_name="text-sm font-semibold"),
                    rx.text(subtitle, class_name="text-[11px]  mt-1 hidden lg:block")),
                    rx.spacer(), rx.text(f"0{i + 1}", class_name="text-[10px]  hidden lg:block"),
                    spacing="3", align="center", width="100%"),
                on_click=S.go_step(title), disabled=S.busy | ((title != "Upload") & ~S.loaded),
                class_name=rx.cond(S.step == title,
                    "w-full text-left px-4 py-3 rounded-lg bg-teal-900 text-white border-2 border-teal-900 shadow-sm",
                    "w-full text-left px-4 py-3 rounded-lg text-slate-600 hover:bg-teal-50 hover:border-slate-300 border-2 border-transparent disabled:text-slate-500 disabled:bg-slate-100 disabled:cursor-not-allowed"),
                aria_current=rx.cond(S.step == title, "step", "false"),
            ) for i, (title, subtitle, name) in enumerate(STEPS)
        ], class_name="flex lg:flex-col gap-2 px-3 overflow-x-auto"),
        rx.spacer(),
        rx.box(rx.hstack(icon("shield-check", 16), rx.text("Your session, your data", class_name="text-xs font-semibold")),
               rx.text("ข้อมูลอยู่ใน session นี้เท่านั้น ไม่บันทึกประวัติข้ามครั้ง", class_name="text-xs text-slate-600 leading-5 mt-2"),
               class_name="m-4 p-4 rounded-lg border border-slate-300 text-slate-600 hidden lg:block"),
        class_name="bg-white border-b lg:border-b-0 lg:border-r border-slate-300 lg:w-64 lg:fixed lg:inset-y-0 flex flex-col z-20",
    )


def shell(content):
    return rx.box(
        sidebar(),
        rx.box(
            rx.hstack(rx.hstack(rx.text("Workspace", class_name="text-xs text-slate-600"),
                                 icon("chevron-right", 13, color="#64748b"),
                                 rx.text(S.step, class_name="text-xs font-medium text-slate-700"), align="center"),
                      rx.spacer(), rx.hstack(rx.box(class_name="w-1.5 h-1.5 rounded-full bg-teal-700"),
                      rx.text("SESSION WORKSPACE", class_name="text-[10px] tracking-widest text-slate-600"), align="center"),
                      class_name="h-16 border-b border-slate-300 bg-white px-6 lg:px-10", align="center"),
            rx.box(content, class_name="max-w-[1440px] mx-auto p-5 md:p-8 lg:p-10"),
            rx.box(rx.text("ANALYST STUDIO", class_name="text-[10px] tracking-widest font-semibold"),
                   rx.text("From raw data to a clearer picture.", class_name="text-xs"),
                   class_name="flex justify-between px-10 py-6 text-slate-600 border-t border-slate-300 mt-8"),
            class_name="lg:ml-64 min-h-screen bg-[#eef2f6]",
        ),
        class_name="min-h-screen text-slate-800",
    )
