# Streamlit version drift: what was removed, and what you probably don't know exists

Compiled from Streamlit's official release notes on 2026-09-11, against
Streamlit 1.63.0 (released 2026-09-01). Streamlit ships a minor version every
2-3 weeks; re-derive this from
https://docs.streamlit.io/develop/quick-reference/release-notes if the project's
version is far ahead of 1.63.

**How to use this file.** Two failure modes matter, and they pull in opposite
directions:

- *Writing something that was removed* — produces a crash or a deprecation
  warning. Covered in Part 1.
- *Not knowing something exists* — produces needlessly elaborate workarounds
  (hand-rolling pagination, faking a modal with an expander, embedding Mermaid
  through an HTML iframe). Covered in Part 2.

Always confirm a specific signature with `streamlit docs st.<command>` against
the project's own install rather than trusting this table verbatim.

---

## Part 1 — Removed and deprecated

### Removed (these raise)

| Removed | Version | Date | Migration |
|---|---|---|---|
| `spec` and `sharing` kwargs on chart commands | 1.57.0 | 2026-04-29 | drop them; configure the chart object instead |
| `st.cache` | 1.62.0 | 2026-08-19 | `@st.cache_data` (serializable results) or `@st.cache_resource` (connections, models) |
| `st.bokeh_chart` | 1.59.0 | 2026-07-06 | `streamlit-bokeh` package (maintained by Streamlit) |
| `st.experimental_get_query_params`, `st.experimental_set_query_params` | 1.54.0 | 2026-02-04 | `st.query_params` |
| `st.experimental_user` | 1.54.0 | 2026-02-04 | `st.user` |
| `use_column_width` on `st.image` | 1.61.0 | 2026-08-04 | `width="stretch"` / `width="content"` / int pixels |
| `element.add_rows` | 1.58.0 | 2026-05-28 | rebuild the element, or use a fragment to redraw |
| Snowpark connection type | 1.59.0 | 2026-07-06 | `st.connections.SnowflakeConnection` |
| `_get_websocket_headers` | 1.57.0 | 2026-04-29 | `st.context.headers` |
| Calling `st.pyplot()` with no figure argument | 1.62.0 | 2026-08-19 | pass the figure explicitly: `st.pyplot(fig)` |

### Deprecated (still works, will be removed)

| Deprecated | Since | Migration |
|---|---|---|
| `use_container_width` — **everywhere** (`st.dataframe`, `st.altair_chart`, `st.plotly_chart`, `st.image`, `st.button`, ...) | phased through 2025-2026 | `width="stretch"` (was `True`) / `width="content"` (was `False`) |
| Passing Matplotlib `savefig` kwargs through `st.pyplot` | 1.62.0 | configure the figure before passing it |
| Local file paths as `str` to `st.html` / `st.iframe` | 1.61.0 | pass a `pathlib.Path` |

> **Verified against Streamlit 1.63.0 (2026-09-11):** `use_container_width` is
> still *accepted* on `st.altair_chart`, `st.dataframe`, `st.plotly_chart`, and
> `st.image` — it is deprecated, not yet removed, despite release-note wording
> that reads like a removal. Treat it as code debt to fix on sight, not as an
> active crash. `use_column_width` on `st.image` **is** gone, as are `st.cache`,
> `st.bokeh_chart`, `st.experimental_user`, and
> `st.experimental_get_query_params` (all confirmed absent from the 1.63 module).
> Confirm status in the project's own version before asserting either way:
> `python -c "import inspect,streamlit as st; print(inspect.signature(st.altair_chart))"`

### The `width` migration, concretely

This is the one you will hit constantly, because `use_container_width=True` was
idiomatic for years and appears throughout older code, tutorials, and model
training data.

```python
# Old — deprecated everywhere, already removed on chart commands
st.dataframe(df, use_container_width=True)
st.altair_chart(chart, use_container_width=True)
st.plotly_chart(fig, use_container_width=True)

# Current
st.dataframe(df, width="stretch")
st.altair_chart(chart, width="stretch")
st.plotly_chart(fig, width="stretch")

# And note: most elements now stretch by default, so the common case is simply
st.dataframe(df)
```

`width` accepts `"stretch"`, `"content"`, `"auto"` (some commands), or an
integer pixel count. When modernizing a file, fix every occurrence rather than
only the one you came for — they will all break on the same upgrade.

---

## Part 2 — Added recently (post-cutoff for most models)

If a task looks like it needs a workaround, check here first. Verify with
`streamlit docs st.<name>` before using, and confirm the project's version is
new enough.

### New commands

| Command | Since | What it replaces |
|---|---|---|
| `st.mermaid_chart` | 1.59.0 | embedding Mermaid via `st.html` / an iframe hack |
| `st.skeleton` | 1.59.0 | placeholder `st.empty()` + spinner juggling |
| `st.pagination` | 1.58.0 | hand-rolled page-number widgets |
| `st.menu_button` | 1.56.0 | popover-plus-buttons dropdown imitations |
| `st.iframe` | 1.56.0 | `st.components.v1.iframe` |
| `st.bottom` | 1.57.0 | CSS hacks to pin a chat input |
| `st.datetime_input` | current | paired `st.date_input` + `st.time_input` |
| `st.App` | 1.53.0+ | custom ASGI routes, middleware, lifespan, programmatic secrets; `python app.py` entry via `st.App.run()` |
| `st.components.v2.component` | 1.53.0+ | the v1 `declare_component` build-step workflow |

### Notable parameters and behaviors

- `@st.fragment(parallel=True)` (1.58) — independent fragments run concurrently
  on a thread pool during a full rerun. Give each its own session-state keys.
- `st.rerun("<fragment key>")` (1.63) — target a named fragment's rerun from a
  widget callback elsewhere; pair with `@st.fragment(key=...)`.
- `refresh_mode="background"` on `st.cache_data` / `st.cache_resource` (1.61) —
  serve the stale value while refreshing off the request path. Config knob:
  `runner.cacheBackgroundRefreshTTLMultiplier`.
- `lazy=` on `st.dataframe` (1.61) — lazy loading for large frames.
- `on_release=` on `st.cache_resource` (1.53) — cleanup hook when an entry is
  evicted. Use it to close connections instead of leaking them.
- Session-scoped caching (1.53) — `st.cache_data` / `st.cache_resource` can
  scope per session rather than globally.
- `persist_state=` on widgets (1.59) — state survives the widget not being
  rendered, which defuses the classic "widget disappeared, value lost" trap.
- `bind=` on widgets (1.55) — two-way binding to a URL query parameter, so app
  state becomes shareable by link with no manual `st.query_params` plumbing.
- `st.Page(visibility=...)` (1.55) and external URLs in `st.Page` (1.56).
- `st.navigation(expanded=...)` (1.56).
- `filter_mode=` on `st.selectbox` / `st.multiselect` (1.56); `select_all=` on
  `st.multiselect` (1.63).
- `selection=` on `st.dataframe` (1.56) — set row selection programmatically;
  plus `"single-row-required"` mode.
- `st.column_config` additions: `ButtonColumn`, `MarkdownColumn` (1.59),
  `AudioColumn`, `VideoColumn` (1.56), `ListColumn`, `MultiselectColumn` (1.54).
- `type="step"` on `st.expander` / `st.status` (1.63) — timeline rendering,
  well suited to agent/chain-of-thought UIs.
- `on_change="ignore"` on `st.slider` / `st.text_input` (1.63) — suppress the
  rerun on change, a cheap fix for laggy text inputs.
- Typed/validated `st.text_input` (1.62) — email, URL, phone, search.
- `st.context` — `headers`, browser/session info; `st.user.tokens` (1.53) for
  OIDC ID/access tokens.
- `streamlit.typing` / `st.typing` (1.62) — public types for annotating
  Streamlit-owned values. Import from here, never from internal modules.
- Starlette/Uvicorn is the default server since 1.57 (was Tornado). Relevant if
  anything in the project reaches into the server layer.
- Config worth knowing: `server.allowedHosts` (1.61), `client.allowedOrigins`
  (1.55), `client.disableDataExport` (1.60), `server.maxWidgetStateSize` (1.60,
  25 MB default), `client.showErrorLinks` (1.54).

### CLI

- `streamlit docs <command>` (1.59) — print the exact signature and docstring
  from the installed version. The fastest authoritative check available.
- `streamlit skills` (1.58) — install Streamlit's bundled agent skills
  (`--global` for a version-agnostic meta-skill).
