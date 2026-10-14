# Navigating Streamlit's documentation

Ordered by authority. Use the highest one that can answer the question.

## 1. `streamlit docs <command>` — version-exact, instant

```bash
<project>/.venv/bin/streamlit docs st.fragment
<project>/.venv/bin/streamlit docs number_input                 # `st.` prefix optional
<project>/.venv/bin/streamlit docs st.column_config.NumberColumn  # namespaces work
<project>/.venv/bin/streamlit docs                              # opens docs site
```

Prints the real signature and docstring from the installed version. Available
since 1.59. Run it with the *project's* interpreter — a different environment
gives you a different version's answer, silently.

## 2. The bundled reference tree — version-matched, task-oriented

Inside the installed package at
`<streamlit>/.agents/skills/developing-with-streamlit/`. Locate it with this
skill's `scripts/find_bundled_docs.py`. Its `references/` directory:

| File | Covers |
|---|---|
| `best-practices.md` | the defaults to apply unless there's a reason not to |
| `performance.md` | caching, fragments, rerun cost, profiling |
| `session-state.md` | state, widget keys, callbacks |
| `layouts.md` | columns, tabs, containers, sidebar, width |
| `design.md` | visual quality, spacing, hierarchy |
| `theme.md` | `config.toml` theming, fonts, CSS variables |
| `dashboards.md` | dashboard composition patterns |
| `data-display.md` | `st.dataframe`, `st.data_editor`, `column_config` |
| `selection-widgets.md` | selection/filtering widget choice |
| `markdown.md` | markdown, directives, colors, icons |
| `chat-ui.md` | chat, agentic, chain-of-thought UIs |
| `multipage-apps.md` | `st.navigation`, `st.Page`, routing |
| `authentication.md` | `st.login`/`st.logout`/`st.user`, OIDC, `[auth]` secrets |
| `testing.md` | `st.testing.v1.AppTest` |
| `code-organization.md` | project structure |
| `environment-setup.md` | envs, dependencies |
| `cli.md` | `streamlit run`, config.toml, ports, server options |
| `server-asgi.md` | `st.App`, ASGI, custom routes, middleware, FastAPI mounting |
| `api-reference.md` | the public `st` surface + `streamlit.typing` types |
| `third-party-components.md` | community components with usage snippets |
| `custom-components-v2.md`, `ccv2-*.md` | building components (state sync, packaging, theming, troubleshooting) |
| `snowflake-connection.md` | Snowflake connections |

## 3. https://docs.streamlit.io — for prose and concepts

- API reference: `/develop/api-reference` (and `/develop/api-reference/<category>`)
- Concepts: `/develop/concepts/architecture/{caching,session-state,fragments,widget-behavior,run-your-app}`
- Multipage: `/develop/concepts/multipage-apps/overview`
- Release notes: `/develop/quick-reference/release-notes` and `/release-notes/<year>`
- Cheat sheet: `/develop/quick-reference/cheat-sheet`
- Deployment: `/deploy`

**Read the release notes whenever the project's version is newer than what you
know.** That page is the single best defense against writing code against a
remembered API.

## 4. Avoid answering from memory or from a web search

Streamlit-related search results skew old, and old Streamlit code is frequently
code that now raises. If you cannot verify with 1-3 above, say the parameter is
unverified rather than asserting it.

---

## Current command surface (Streamlit 1.63, September 2026)

Orientation only — confirm signatures with `streamlit docs`.

**Write & text** — `write`, `write_stream`, `markdown`, `title`, `header`,
`subheader`, `badge`, `caption`, `code`, `echo`, `latex`, `text`, `divider`,
`help`, `html`, `iframe`

**Data** — `dataframe`, `data_editor`, `column_config`, `table`, `metric`, `json`

**Charts** — `area_chart`, `bar_chart`, `line_chart`, `scatter_chart`, `map`,
`pyplot`, `altair_chart`, `vega_lite_chart`, `plotly_chart`, `pydeck_chart`,
`graphviz_chart`, `mermaid_chart`

**Input widgets** — `button`, `download_button`, `link_button`, `menu_button`,
`page_link`, `checkbox`, `color_picker`, `feedback`, `multiselect`, `pills`,
`radio`, `segmented_control`, `selectbox`, `select_slider`, `toggle`,
`number_input`, `slider`, `date_input`, `datetime_input`, `time_input`,
`text_area`, `text_input`, `pagination`, `audio_input`, `file_uploader`,
`camera_input`, `chat_input`

**Media** — `image`, `logo`, `pdf`, `audio`, `video`

**Layout** — `columns`, `container`, `empty`, `expander`, `popover`, `sidebar`,
`bottom`, `space`, `tabs`

**Chat & status** — `chat_input`, `chat_message`, `status`, `progress`,
`spinner`, `skeleton`, `toast`, `balloons`, `snow`, `success`, `info`,
`warning`, `error`, `exception`

**Execution flow** — `dialog`, `form`, `form_submit_button`, `fragment`,
`rerun`, `stop`

**Caching & state** — `cache_data`, `cache_resource`, `session_state`,
`query_params`, `context`

**Navigation** — `navigation`, `Page`, `page_link`, `switch_page`

**Connections & secrets** — `connection`, `connections.SQLConnection`,
`connections.SnowflakeConnection`, `connections.BaseConnection`, `secrets`

**Auth** — `login`, `logout`, `user`

**Server & config** — `App`, `set_page_config`, `get_option`, `set_option`,
`config.toml`

**Components** — `components.v2.component` (current), `components.v1.html`,
`components.v1.iframe`, `components.v1.declare_component` (legacy)

**Testing** — `testing.v1.AppTest` (`from_file`, `from_string`, `from_function`)
