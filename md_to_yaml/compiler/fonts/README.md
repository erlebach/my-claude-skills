# Cached fonts

A `.woff2` here is inlined into the compiled deck as a base64 `@font-face`, replacing the
stylesheet link to Google that `base.html.j2` would otherwise emit. The lookup is by slug:
a deck whose `font:` is `IBM Plex Sans` uses `ibm-plex-sans.woff2`. A font with no file here
still falls back to the Google link, so naming a new font in a deck keeps working.

| file | family | subset | axis | source |
|---|---|---|---|---|
| `ibm-plex-sans.woff2` | IBM Plex Sans | latin (`U+0000-00FF` + punctuation, per Google's `css2` split) | variable, `wght` | `fonts.gstatic.com/s/ibmplexsans/v23/…woff2`, fetched 2026-08-24 |

**Why the latin subset only.** Google's `css2` endpoint splits each family into latin,
latin-ext, cyrillic, cyrillic-ext, greek and vietnamese. Embedding all six would be ~6× the
bytes for glyphs no deck uses. A deck that needs another script should fetch that subset and
add it here as a second `@font-face`.

**Licence.** IBM Plex is under the SIL Open Font License 1.1 — `OFL.txt`, copied from the
IBM/plex repository. The OFL permits embedding; the licence must travel with the font, which
is why the file is kept beside it rather than only linked.
