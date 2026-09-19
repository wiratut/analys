import reflex as rx

from ..state import StudioState as S

PANEL = "rounded-xl border border-slate-300 border-t-2 border-t-teal-600 bg-white shadow-sm"


def icon(name: str, size: int = 18, **props):
    return rx.icon(name, size=size, **props)


def panel(*children, **props):
    return rx.box(*children, class_name=PANEL + " p-6", **props)


def section_title(eyebrow, title, subtitle):
    return rx.box(
        rx.text(eyebrow, class_name="text-xs font-semibold tracking-widest uppercase text-teal-800 mb-3"),
        rx.heading(title, size="8", class_name="tracking-tight text-slate-900 mb-3"),
        rx.text(subtitle, class_name="text-sm text-slate-600 leading-7 max-w-2xl"),
        class_name="mb-8",
    )


def stat(label, value, note, name="chart-no-axes-column"):
    return rx.box(
        rx.hstack(rx.text(label, class_name="text-xs font-medium text-slate-600"), rx.spacer(),
                  icon(name, 16, color="#475569"), align="center"),
        rx.text(value, class_name="text-3xl font-semibold tracking-tight text-slate-900 mt-3 tabular-nums"),
        rx.text(note, class_name="text-xs text-slate-600 mt-2"),
        class_name=PANEL + " p-5 min-w-0",
    )


def data_table(columns, rows, max_height="360px"):
    return rx.box(
        rx.table.root(
            rx.table.header(rx.table.row(rx.foreach(columns, lambda col: rx.table.column_header_cell(
                col, class_name="whitespace-nowrap text-xs font-semibold text-teal-950 bg-teal-50")))),
            rx.table.body(rx.foreach(rows, lambda row: rx.table.row(rx.foreach(row, lambda cell: rx.table.cell(
                cell, class_name="whitespace-nowrap text-xs text-slate-600 max-w-xs truncate"))))),
            size="2", variant="surface", width="100%",
        ),
        class_name="overflow-auto rounded-lg border border-slate-300 w-full", max_height=max_height,
    )


def field(label, control, hint=""):
    return rx.box(rx.text(label, class_name="text-xs font-semibold text-slate-600 mb-2"),
                  rx.box(control, class_name="rounded-lg ring-1 ring-teal-300 focus-within:ring-2 focus-within:ring-teal-600 transition-shadow"),
                  rx.cond(hint != "", rx.text(hint, class_name="text-xs text-slate-600 mt-1")),
                  class_name="min-w-0 w-full")


def select(items, value, handler, placeholder="เลือกคอลัมน์"):
    return rx.select(items, value=value, on_change=handler, placeholder=placeholder,
                     size="3", width="100%", disabled=S.busy)


def next_button(label, step):
    return rx.button(label, icon("arrow-right", 16), on_click=S.go_step(step), size="3", disabled=S.busy)


def feedback():
    return rx.box(
        rx.cond(S.busy, rx.hstack(rx.spinner(size="2"), rx.text("กำลังประมวลผล…", size="2"),
                                class_name="rounded-lg bg-teal-50 text-teal-900 p-4 mb-4", role="status")),
        rx.cond(S.error != "", rx.callout(S.error, icon="circle-alert", color_scheme="red",
                                          role="alert", class_name="mb-4")),
        rx.cond(S.notice != "", rx.callout(S.notice, icon="circle-check", color_scheme="green",
                                           role="status", class_name="mb-4")),
        aria_live="polite",
    )
