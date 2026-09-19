"""Reflex app entry point. All authored UI is Python."""
import reflex as rx
from .state import StudioState as S
from .components.shell import shell
from .components.common import feedback
from .pages.upload import upload_page
from .pages.profile import profile_page
from .pages.clean import clean_page
from .pages.dashboard import dashboard_page
from .pages.export import export_page


def index() -> rx.Component:
    return shell(rx.box(feedback(), rx.match(S.step,
        ("Upload", upload_page()), ("Profile", profile_page()), ("Clean", clean_page()),
        ("Dashboard", dashboard_page()), ("Export", export_page()), upload_page())))


app = rx.App(
    theme=rx.theme(appearance="light", accent_color="teal", gray_color="slate", radius="large", scaling="100%"),
    style={"font_family": "Inter, ui-sans-serif, system-ui, -apple-system, sans-serif",
           "--accent-9": "#0f766e", "--accent-10": "#115e59", "--accent-11": "#0f766e"},
)
app.add_page(index, title="Analyst Studio | Data workspace", description="Upload, clean, understand and share your data.")
