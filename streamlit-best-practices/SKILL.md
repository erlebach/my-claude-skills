---
name: streamlit-best-practices
description: "Best-practice guidance for building, reviewing, debugging, and modernizing Streamlit apps. Loads the version-matched official docs bundled inside the project's own Streamlit install, guards against the removed/renamed APIs that make generated Streamlit code fail, and navigates the Streamlit app gallery and components gallery. Use this whenever the work touches Streamlit in any way — writing or editing an app, `st.` anything, app.py / streamlit_app.py, dashboards, pages/, caching, session state, fragments, reruns, widgets, layout, theming, secrets, multipage navigation, custom components, deployment to Community Cloud — and also when the user asks 'is there a Streamlit component for X', wants a Streamlit example to crib from, hits a slow or looping app, or sees an unexpected keyword argument / deprecation error. Use it even for small edits: Streamlit's API changes fast enough that unaided edits routinely introduce arguments that no longer exist."
---

# Streamlit best practices

## Why this skill exists

Streamlit ships a new minor version every 2-3 weeks and *removes* deprecated
APIs on a schedule. That makes Streamlit unusually hostile to answering from
memory: a parameter that was idiomatic in one release is a hard `TypeError` two
releases later. Most broken Streamlit code an assistant produces is not bad
logic — it is confidently-written calls to an API that no longer exists.

Two habits fix almost all of it, and they are what this skill enforces:

1. **Read the docs that shipped with *this project's* Streamlit**, not
   remembered docs. Streamlit >= 1.57 bundles a full agent-facing documentation
   tree inside the pip package, so it is always version-exact.
2. **Check any parameter you did not just read** with `streamlit docs st.<cmd>`.

Everything else here is the material the bundled docs do not cover: version
drift, and the galleries.

## Step 1 — Load the version-matched official docs

Run this first, before writing or editing any Streamlit code:

```bash
python3 ~/.claude/skills/streamlit-best-practices/scripts/find_bundled_docs.py --project-dir <project root>
```

It prints `<version>\t<path to SKILL.md>`. **Read that SKILL.md.** It is
Streamlit's own routing skill and points into ~27 topic references
(`references/` beside it) covering dashboards, layouts, theming, session state,
performance, chat UIs, custom components v2, testing, ASGI/`st.App`, and auth.
It also ships assets worth using rather than reinventing:

- `assets/templates/apps/` — six working dashboard templates
  (`dashboard-metrics`, `dashboard-companies`, `dashboard-compute`,
  `dashboard-feature-usage`, `dashboard-seattle-weather`,
  `dashboard-stock-peers`). Start a new dashboard by copying the closest one.
- `assets/templates/themes/configs/` — twelve ready `.streamlit/config.toml`
  themes (dracula, financial-dashboard, fluent, jupyter, material-ui, minimal,
  nord, one-dark-pro, shadcn, solarized-light, ubuntu, vscode).

Note the version it printed. You will need it in Step 2.

**If the script exits non-zero**, Streamlit is older than 1.57 or absent. Say so,
then fall back to `references/` here plus https://docs.streamlit.io — and treat
every parameter as unverified until checked.

Optional, once per machine: `streamlit skills --global` installs Streamlit's own
meta-skill so the bundled docs are reachable without this skill. Harmless
alongside it; this skill still adds Steps 2-4.

## Step 2 — Guard against version drift

This is the highest-value thing you can do, and the bundled docs do not do it:
they describe what *is*, not what *was* and will now raise.

Before finishing any edit, scan your code for the removed and deprecated names
in `references/version-drift.md`, and read that file whenever you are editing
code you did not write, migrating an app, or debugging a `TypeError:
... unexpected keyword argument` / `AttributeError` / deprecation warning.

The four that bite most often:

| Do not write | Write instead | Gone since |
|---|---|---|
| `use_container_width=True` | `width="stretch"` (and `width="content"` for `False`) | deprecated everywhere; still accepted in 1.63 — fix on sight, it is a scheduled break |
| `@st.cache` | `@st.cache_data` or `@st.cache_resource` | removed in 1.62 (Aug 2026) |
| `st.experimental_get_query_params` / `st.experimental_user` | `st.query_params` / `st.user` | removed in 1.54 (Feb 2026) |
| `st.bokeh_chart` | `streamlit-bokeh` package | removed in 1.59 (Jul 2026) |

When you find these in an existing file, fix them — a stale parameter is a
latent crash on the user's next Streamlit upgrade, not a style nit.

**Verify anything you are not certain of**, using the project's own Streamlit:

```bash
<project>/.venv/bin/streamlit docs st.fragment          # exact signature + docstring
<project>/.venv/bin/streamlit docs st.column_config.NumberColumn
```

This is cheap, authoritative, and version-exact. Prefer it to guessing, and
prefer it to a web search — the web will happily show you three-year-old blog
posts.

## Step 3 — Apply the mental models that outlive the API

The bundled references have the detail; these are the models that explain *why*
the idioms are what they are, so you can reason rather than pattern-match.

**The whole script reruns, top to bottom, on every interaction.** Not a
callback graph — a re-execution. Every widget interaction, every `st.rerun()`.
This single fact explains caching, session state, and fragments: they all exist
to make a full re-execution cheap and to let something survive it.

**Caching: the split is serializability, not speed.**
`@st.cache_data` returns a *copy* each call — use it for DataFrames, query
results, API responses, anything serializable. The copy is the feature: it stops
one user's mutation from corrupting another's view. `@st.cache_resource` returns
the *same object* — use it for connections, clients, models, anything that must
not be duplicated, and only when that object is thread-safe, because every
session shares it. Prefix unhashable args with `_` (`def q(_conn, sql)`) to skip
hashing them, remembering that the cache then will not invalidate when they
change. Reach for `ttl=` on anything backed by a moving data source.

**Session state is the only thing that survives a rerun.** A widget's `key`
mirrors it into `st.session_state[key]` automatically. Two traps: a widget that
is not rendered on a rerun loses its state, and you cannot set a widget's value
via session state after instantiating it. Callbacks (`on_change`/`on_click`) run
*before* the rerun, which is what makes them the right place to mutate state.

**`st.button` is not a checkbox.** It returns `True` for exactly one rerun.
`if st.button(...):` guarding multi-step work is the single most common
Streamlit bug — the next interaction reruns the script, the button is `False`,
and the work vanishes. Latch it into session state instead.

**Fragments are the fix for "one slow widget reruns everything."**
`@st.fragment` scopes a rerun to that function. `run_every="10s"` gives live
refresh without a full rerun; `@st.fragment(parallel=True)` runs independent
fragments concurrently. A fragment cannot be cached on the same function.

**Multipage: prefer `st.navigation` + `st.Page`** over a bare `pages/`
directory. The `pages/` convention still works, but `st.navigation` lets the
entrypoint act as a frame around every page (shared sidebar, auth gate, common
data load) and supports grouping, hidden pages, and login-dependent nav. Call
`st.set_page_config()` once, in the entrypoint, before anything else.

**Secrets belong in `.streamlit/secrets.toml`, never in source, and that file
must be gitignored.** Read via `st.secrets`; `st.connection("sql")` wires
SQLAlchemy connections from it with pooling already handled. If you touch a
project's secrets handling, confirm the gitignore covers it.

**Layout: `width="stretch"` / `width="content"`.** Use `st.columns` for KPI
rows, `st.tabs` to cut scrolling, `st.container(height=...)` for scroll regions,
`st.expander` for detail that most readers skip.

## Step 4 — Use the galleries

When the user wants an example to crib from, asks whether a component exists for
some interaction, or needs something Streamlit's core API cannot do, read
`references/galleries.md`. It covers the app gallery (browsable, every app's
source readable and forkable), the components gallery (sortable by downloads and
recency, with the vetting criteria that matter before adopting a dependency),
and Community Cloud's explore feed.

The short version: **check the components gallery before building any custom
component, and check core Streamlit before reaching for the gallery.** Custom
components are third-party code that breaks on Streamlit upgrades; a native
widget that does 90% of the job is usually the better trade.

## Step 5 — Verify

Never claim an app works without running something.

- `streamlit run app.py` — check whether one is already serving on 8501 first
  (`lsof -nP -iTCP -sTCP:LISTEN | grep ':85'`); Streamlit hot-reloads on save,
  so a running app may need only a refresh.
- `st.testing.v1.AppTest` — headless, in-process assertions with no browser.
  This is the right way to prove behavior; see the bundled `references/testing.md`.

## Reference files

- `references/version-drift.md` — removed/deprecated APIs by version with
  migrations, and what is new enough that you likely do not know it exists.
  Read when editing unfamiliar code, migrating, or debugging an argument error.
- `references/galleries.md` — app gallery, components gallery, Community Cloud;
  curated components with install names; how to vet one.
- `references/docs-map.md` — where each topic lives in the docs, the
  `streamlit docs` CLI, and the current command surface by category.
