# Analyst Studio

Build the requested Python-only Reflex application in the current empty workspace.
Use a white/slate interface with navy blue accents, Thai explanatory text, five
persistent workflow steps, responsive cards, and accessible labeled controls.

## Boundaries

`analyst_studio/services` owns CSV parsing, DuckDB profiling/aggregation, pure
copy-on-write cleaning, dashboard figures, Gemini requests, and report exports.
`analyst_studio/state.py` owns private per-session DataFrames, undo snapshots,
pending previews, filter values and public presentation data. `components` and
`pages` build the Reflex UI. No data database, localStorage, or custom JavaScript.
Reflex's transport may use its own session identifier; dataset/pipeline data stays
in memory on the server. State manager is explicitly memory, one backend process.

## Workflow

CSV or dirty sample → immediate profile and 30-row preview → select cleaning
operation and parameters → preview before/after and impact → apply → undo.
Each successful action creates a history entry and snapshot. Invalid previews do
not mutate data. Dataset replacement clears history, figures, filters and insights.
Upload limit 25 MiB; maximum 200,000 rows, 150 columns; reject malformed CSV.

Dashboard generates histograms, top-category bars, daily date counts, and numeric
Pearson correlation. Date detection requires date-shaped values to avoid numeric
identifier misclassification. Category/date filters affect charts, KPIs, AI summary
and PDF; clean CSV/Excel exports always contain the complete cleaned dataset.
All generated charts are available; custom histogram/bar/line/scatter uses chosen
axes. Empty and no-numeric datasets render explanatory states.

Gemini is optional; only bounded aggregate summaries are sent after explicit
Generate insights action. Category labels can be included, but no raw row samples.
Responses are labeled AI text; deterministic statistics remain separate. API key
only comes from environment/.env, which is ignored. Model is configurable using
GEMINI_MODEL (default gemini-2.5-flash-lite). Failures do not block other operations.

PDF uses WeasyPrint and Matplotlib images rendered from the same prepared chart
data as Plotly, avoiding a Chrome/Kaleido installation dependency. Includes filtered
KPIs, profile stats, main charts, pipeline, filter context, and AI result when present.
Escaped HTML prevents uploaded values being interpreted as report markup.

## Verification

Test malformed upload, profiling, every cleaning family, nonmutation on errors,
undo, filters, custom charts, empty data, CSV/Excel integrity, PDF including charts,
AI missing key and request failure. Compile Reflex UI, run backend/frontend, and
exercise the workflow in browser when tooling is available. Record limits honestly.
