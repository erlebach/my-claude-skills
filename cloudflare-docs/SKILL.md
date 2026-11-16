---
name: cloudflare-docs
description: Look up the official Cloudflare developer documentation (developers.cloudflare.com) live, as Markdown, including the REST API reference, and answer from it with page links. Use this whenever the work touches Cloudflare in any way — deploying or uploading a static or local website to Cloudflare (Workers static assets, Pages, Direct Upload, drag and drop), deploying from GitHub (Workers Builds, Pages Git integration, GitHub Actions with wrangler-action), wrangler commands or wrangler.jsonc/wrangler.toml settings, D1, KV, R2, Workers code, custom domains, routes and DNS, Cloudflare Access / Zero Trust sign-in, API tokens and permissions, or calling api.cloudflare.com — and also when a wrangler or Cloudflare error needs explaining, even if the user does not mention the docs. Cloudflare changes fast enough that answers from memory are often stale; check the docs first.
---

# Cloudflare docs

Cloudflare's docs are large (hundreds of products, thousands of pages) and change weekly: products
get renamed, Pages is now second to Workers for new sites, wrangler flags come and go. Answers from
memory are therefore often outdated in ways that break a deploy. This skill reads the live docs in
a form made for agents, so that every answer rests on the current page and can cite it.

## How the docs are exposed

- `https://developers.cloudflare.com/llms.txt`: every product, each with its own index.
- `https://developers.cloudflare.com/<product>/llms.txt`: every page of that product, with a
  one-line summary. Some products nest further indexes (Cloudflare One: `access-controls/llms.txt`).
- Any page as Markdown: its URL + `index.md` (e.g. `/workers/static-assets/index.md`).
- REST API reference: `/api/llms.txt` lists resources (D1 > Database, Pages > Projects >
  Deployments, ...); each resource page lists its methods (`POST /accounts/{account_id}/d1/...`);
  each method page has parameters, body and required token permissions.

## The script

`scripts/cfdocs.py` (Python 3, standard library only) does the fetching, searching and cleanup,
with a one-day cache in `~/.cache/cfdocs`. Run it with `python3 <skill-dir>/scripts/cfdocs.py`.

| Command | Use |
|---|---|
| `search WORD...` | Page titles/summaries across the products deploys usually touch (workers, pages, d1, cloudflare-one, fundamentals, dns, ssl, r2, kv, rules, cache, turnstile). Start here. |
| `search WORD... --in workers,pages` | The same, limited to (or extended to) the products named. |
| `index PRODUCT [WORD...]` | One product's pages (`workers`, `pages`, `d1`, `cloudflare-one`, ...). |
| `products [WORD...]` | Product slugs, when you don't know which product covers something. |
| `api WORD...` | REST API: resources matching the first words, their methods filtered by the rest (`api d1 query`, `api pages projects deployments`, `api dns records create`, `api access applications`). |
| `page URL_OR_PATH [--grep RE] [--max N]` | One page as clean Markdown. `--grep` keeps only matching sections, which matters for long pages (wrangler configuration is ~100 KB). |

Every word in a query must match (case-insensitive), so use one or two distinctive words
(`search custom domain`, not a sentence). If nothing matches, drop a word or try a synonym; the
docs say "Custom Domains", "Routes", "Direct Upload", "Workers Builds", "Access application".

## Workflow

1. **Orient.** Decide which product owns the question (the map below helps). For anything
   about deploying a site, read `references/deploy-map.md` first: it lists the key pages for each
   way of putting a local site on Cloudflare, with and without GitHub.
2. **Find the page** with `search`, `index` or `api`.
3. **Read it** with `page`, using `--grep` for the section you need. Read the actual page before
   giving commands, config keys or limits; don't fill those in from memory, since they are exactly
   what changes between versions.
4. **Answer with the source.** Give the page URL for each fact, and its "Last updated" date when
   the fact is version-sensitive (limits, pricing, flags). If the docs and the user's installed
   wrangler might disagree, say which wrangler version the page assumes, or suggest
   `npx wrangler <command> --help` to confirm locally.

If the network is down, the script falls back to its cache and says so; tell the user the answer
may be stale.

## Orientation map

These are pointers for step 1, not answers; confirm details on the pages.

- **New static or full-stack site: Workers with static assets.** Cloudflare now says to start new
  projects on Workers, not Pages (`/pages/` says so at the top; `/workers/static-assets/`). A
  `wrangler.jsonc` with `"assets": {"directory": ...}` and `npx wrangler deploy` uploads a folder;
  an optional Worker script adds server code (`run_worker_first`, routing pages under
  `/workers/static-assets/routing/`).
- **Pages** still works: Git integration, Direct Upload (`wrangler pages deploy <dir>` or drag and
  drop), Pages Functions. Migration guide: `/workers/static-assets/migration-guides/migrate-from-pages/`.
- **From GitHub:** Workers Builds (Cloudflare builds on push; `/workers/ci-cd/builds/`), or your own
  CI with GitHub Actions (`/workers/ci-cd/external-cicd/github-actions/`, secrets
  `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`). Pages has its own Git integration.
- **Without GitHub:** `npx wrangler deploy` (Workers) or `wrangler pages deploy` / drag and drop
  (Pages) from the local machine, after `npx wrangler login` or with an API token in
  `CLOUDFLARE_API_TOKEN`.
- **Databases and storage:** D1 (SQLite; `/d1/`, wrangler commands `/workers/wrangler/commands/d1/`),
  KV, R2. The binding lives in the wrangler config.
- **Sign-in in front of a site:** Cloudflare Access, under the `cloudflare-one` product
  (`search self-hosted --in cloudflare-one`, `search jwt --in cloudflare-one`).
- **Domains:** Workers Custom Domains and Routes (`/workers/configuration/routing/`), Pages custom
  domains, DNS zone setup (`dns`).
- **Automation through the API:** tokens and permissions under `fundamentals`
  (`/fundamentals/api/get-started/create-token/`, `/fundamentals/api/reference/permissions/`);
  endpoints via `api ...`. Requests go to `https://api.cloudflare.com/client/v4` + the method path,
  with `Authorization: Bearer <token>`.

## Gotchas worth checking against the docs

These came up in real use; each is worth a quick `page --grep` before relying on it.

- D1 limits (`/d1/platform/limits/`): 100 KB per SQL statement, 100 bound parameters per query,
  per-file import limits. `wrangler d1 execute --file` rejects `BEGIN`/`COMMIT`; a file is the unit
  of work. `--local` uses `.wrangler/state` and needs no login; `--remote` needs one. `-y/--yes`
  answers prompts in scripts.
- `wrangler.jsonc` keys move between versions; check `/workers/wrangler/configuration/` with
  `--grep` for the key in question rather than relying on an older example.
- Workers Builds runs the wrangler version in the repo's `package.json`, and its deploy command
  defaults to `npx wrangler deploy` (`/workers/ci-cd/builds/configuration/`).
- An Access JWT must be verified (signature, audience, issuer, expiry), not trusted from a header
  (`Validate JWTs` page under cloudflare-one).

## Reference files

- `references/deploy-map.md`: the key pages for putting a local site on Cloudflare (Workers static
  assets, Pages, with and without GitHub, D1, Access, domains, API tokens), checked against the live
  indexes. Read it for any deployment question.
