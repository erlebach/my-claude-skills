# Hugo behaviours that break templates silently

Taken from the `hugo-course-builder` skill and `course_site/CLAUDE.md`, filtered to what a CAP5771 unit can meet. A new unit should need no template change. Read this before any change to `layouts/`, and load `hugo-course-builder` too.

## Builds and the server

- Check builds with `hugo --noBuildLock -d scratch/checkbuild`. A plain `hugo` blocks with no message on the lock that a running `hugo server` holds, and it writes into `public/`.
- The author's preview is on port 1313. Use another port.
- `hugo server` does not watch a top-level folder created after it started. Restart it.
- `hugo server` does not rebuild a page when a file tested with `fileExists` appears or disappears, and keeps renamed static files until a restart. Use `fileExists` only in build checks; put display facts in data (`planned: true`).
- Test addresses with a production build. The preview `baseURL` has no path; the deploy address has `/~gerlebacher/course/cap5771_s2027/`.

## Templates

- `errorf` logs and continues. One fault then gives many errors. Gate later loops on a validity flag (`$ok` in `rail.html`).
- A check is not verified until it has failed once.
- `else with` is not valid; `else` takes only `if`.
- Use `hugo.Data`, not `site.Data`.
- Use `sort … "Params.weight"`, not `.Pages.ByWeight` (weight 0 sorts last).
- `int "08"` fails (octal). Compare `printf "module-%02d"` with the folder name.
- `.File.ContentBaseName` of a branch bundle is its folder name.
- `resources.Get` piped straight into `fingerprint` fails without naming the file. Get it, check it, then fingerprint.

## Escaping and output

- Raw HTML in Markdown is dropped (`unsafe = false`). Shortcode output is not, so generated HTML comes from shortcodes.
- `jsonify` inside `<script>` needs `safeJS`, or `JSON.parse` returns a string.
- `delimit` over partial output returns a plain string; pipe it through `safeHTML`.
- `+` becomes `&#43;` in titles; use `transform.HTMLEscape | safeHTML`.
- A trim marker removes the white space on its side: `{{- x -}} – {{ y -}}` gives `x– y`.
- `canonifyURLs` does not rewrite addresses in a JSON `<script>`. Strip the leading slash and use `absURL`.

## Math

- Hugo passes through `$$…$$`, `\[…\]` and `\(…\)` only. The Zen script `themes/zen/assets/js/math.js` also took a single `$` as math, so "$32.81 … $63.50" in one paragraph became one formula. The project copy `assets/js/math.js` overrides it. Keep that file.
- To test for this, count `.katex` elements whose text contains ordinary words.

## Zen and CSS

- Do not edit `themes/`.
- All project CSS is in `assets/css/custom.css`, inside `@layer course { … }`; that layer wins over the theme without `!important`. Inside the layer, normal specificity applies.
- The rail page does not use Zen: `assets/css/rail.css`, `assets/js/rail.js`.
- Zen styles a `<ul>` that is a direct child of `<article>` as a table.
- CSS and JS go in `assets/`, not `static/`, so that Hugo fingerprints them.
