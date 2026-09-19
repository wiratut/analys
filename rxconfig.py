from dotenv import load_dotenv
import os
import reflex as rx

load_dotenv()

# Use the supported Python ASGI runner; avoid forked Granian workers hanging
# during startup with the scientific Python stack on this local environment.
os.environ.setdefault("REFLEX_USE_GRANIAN", "false")
os.environ.setdefault("REFLEX_CHECK_LATEST_VERSION", "false")
os.environ.setdefault("REFLEX_USE_NPM", "true")
os.environ.setdefault("npm_config_audit", "false")
os.environ.setdefault("npm_config_prefer_offline", "true")

config = rx.Config(
    app_name="analyst_studio",
    state_manager_mode="memory",
    show_built_with_reflex=False,
    telemetry_enabled=False,
    plugins=[rx.plugins.TailwindV4Plugin()],
    disable_plugins=[rx.plugins.SitemapPlugin],
)
