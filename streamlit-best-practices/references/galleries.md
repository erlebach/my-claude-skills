# The Streamlit galleries

Three separate collections, often confused. Pick by what you actually need.

| Need | Go to |
|---|---|
| A working app to crib patterns or structure from | **App gallery** — https://streamlit.io/gallery |
| A widget/interaction core Streamlit doesn't have | **Components gallery** — https://streamlit.io/components |
| To see what the community is deploying right now | **Community Cloud explore** — https://share.streamlit.io/explore |

All three are JavaScript-rendered, so plain `curl` returns an empty shell. Use a
browser-capable fetch, or go straight to the underlying GitHub repos, which are
plain HTML and far more useful anyway.

---

## App gallery — https://streamlit.io/gallery

Curated apps, each with a live demo **and readable, forkable source**. The
source is the point: a deployed app shows you the layout decisions, caching
strategy, and data-loading shape that actually survived contact with users.

Categories used as filters on the page:

Favorites · Trending · LLMs · Snowflake powered · Data visualization ·
Geography & society · Sports & fun · Science & technology · NLP & language ·
Finance & business · Other

**How to actually mine it.** Browsing screenshots is the slow path. Faster:

1. Find the app's GitHub repo (linked from its gallery card and usually from a
   badge in the running app itself).
2. Read the entrypoint and `requirements.txt` first — they tell you the
   architecture and the real dependency set in under a minute.
3. Check the repo's last-commit date before copying anything. A 2022 gallery app
   is full of `use_container_width=True` and possibly `@st.cache`; see
   `version-drift.md` before lifting code from it.

**Prefer the bundled templates for dashboards.** Before going to the gallery for
a dashboard, check `assets/templates/apps/` inside the installed Streamlit
package (the skill's Step 1 script prints its location). Six dashboard templates
ship there — metrics/KPI, company comparison, compute monitoring, feature
adoption, weather exploration, stock peers. They are version-current by
construction, which gallery apps are not.

---

## Components gallery — https://streamlit.io/components

Third-party packages that extend Streamlit. Sortable by **trending, GitHub
stars, recently updated, and 30-day PyPI downloads** — sort by downloads *and*
recency together; a high-download package that hasn't been touched in two years
is a liability, not a recommendation.

Categories: LLMs · Widgets · Charts · Authentication · Connections ·
Images & video · Audio · Text · Maps · Dataframes · Graphs · Molecules & genes ·
Code editors · Page navigation · Developer tools · Integrations

### Check core Streamlit first

The gallery long predates a lot of what Streamlit now does natively, so it is
full of components that core has since absorbed. Before adopting one, confirm
core can't do it — `st.pagination`, `st.menu_button`, `st.mermaid_chart`,
`st.navigation`, `st.dialog`, `st.login`/`st.user`, `st.connection`, and
`st.segmented_control` all have popular gallery components they supersede.
Adding a dependency to replicate a native widget is a pure downside: it breaks
on upgrade and it themes inconsistently.

### Vetting one before you add it

A custom component is arbitrary third-party JS running in your users' browsers,
pinned to Streamlit's internal component protocol. That protocol changes. So:

- **Maintained?** Commits in the last ~6 months; open issues being answered.
- **Compatible?** Does it declare support for the project's Streamlit version?
  Components tracking the frontend API break on minor upgrades.
- **Used?** 30-day downloads and stars, read together with recency.
- **Necessary?** Can core Streamlit get you 90% there? Usually yes, and usually
  that is the right call.

Install by **PyPI name, which often differs from both the repo name and the
import name** — check all three in the component's docs.

### Frequently useful components

Download figures are 30-day PyPI, as listed on the gallery in September 2026 —
indicative of scale, not current to the day.

| Component | Install | Import | Use for | ~Downloads |
|---|---|---|---|---|
| ITables | `itables` | `itables.streamlit` | interactive DataTables-style tables | 1.3M |
| AgGrid | `streamlit-aggrid` | `st_aggrid` | row grouping, pivoting, complex cell editing beyond `st.data_editor` | 876K |
| Option Menu | `streamlit-option-menu` | `streamlit_option_menu` | styled nav menus (but try `st.navigation` first) | 458K |
| Extras | `streamlit-extras` | `streamlit_extras.*` | grab-bag of small UI utilities; cherry-pick | 420K |
| Folium | `streamlit-folium` | `streamlit_folium` | interactive Leaflet maps beyond `st.map` | 346K |
| Authenticator | `streamlit-authenticator` | `streamlit_authenticator` | login when OIDC via `st.login` isn't an option | 213K |
| WebRTC | `streamlit-webrtc` | `streamlit_webrtc` | live camera/mic streaming | 105K |
| Pygwalker | `pygwalker` | `pygwalker.api.streamlit` | Tableau-style drag-and-drop exploration | — |
| Calendar | `streamlit-calendar` | `streamlit_calendar` | full calendar views | 34K |
| Keyup | `streamlit-keyup` | `st_keyup` | text input firing per keystroke, for live search | — |
| Bokeh | `streamlit-bokeh` | `streamlit_bokeh` | **required** since `st.bokeh_chart` was removed in 1.59 | — |
| Pivot table | `streamlit-pivot` | `streamlit_pivot` | drag-and-drop pivot with drill-down (Streamlit-maintained) | — |

`streamlit-bokeh` and `streamlit-pivot-table` are maintained by Streamlit
itself, which makes them materially safer bets than community packages.

The installed Streamlit's own `references/third-party-components.md` has usage
snippets for most of these — read it rather than guessing at call signatures.

### If nothing fits

Build a component with `st.components.v2.component` (the current API; v1
`declare_component` required a separate frontend build step). The bundled
`references/custom-components-v2.md`, `ccv2-state-sync.md`,
`ccv2-packaged-components.md`, `ccv2-theme-css-variables.md`, and
`ccv2-troubleshooting.md` cover this properly. Only go here for interactions
that have *never* been in Streamlit's API — drag-and-drop, canvas drawing, bespoke
visualizations. If the gap is just that the project's Streamlit is old, the fix
is an upgrade, not a custom component.

---

## Community Cloud explore — https://share.streamlit.io/explore

The live feed of community-deployed apps. Less curated than the gallery, more
current. Useful for seeing what people build for a niche domain, and for
deployment-shape questions (secrets handling, `requirements.txt` pinning,
resource limits). Deployment mechanics live in the bundled `references/` —
including `ccv2-troubleshooting.md` for Community Cloud issues.
