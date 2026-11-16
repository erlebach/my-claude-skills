# Deploying a local site to Cloudflare: where the docs are

All paths are on `https://developers.cloudflare.com`; read any of them with
`cfdocs.py page <path>`. Checked against the live indexes on 2026-10-30. If a path returns 404,
the page moved: find it again with `cfdocs.py search <title words>`.

## Contents

1. Choosing: Workers or Pages
2. Workers with static assets (recommended for new sites)
3. Deploying from GitHub
4. Deploying without GitHub
5. Pages (existing projects)
6. Wrangler
7. D1
8. Domains and DNS
9. Sign-in: Cloudflare Access
10. API tokens and the REST API
11. Logs and troubleshooting

## 1. Choosing: Workers or Pages

| Page | Path |
|---|---|
| Pages overview (its banner says to start new projects with Workers) | `/pages/` |
| Migrate from Pages to Workers (includes a feature compatibility matrix) | `/workers/static-assets/migration-guides/migrate-from-pages/` |

## 2. Workers with static assets

| Page | Path |
|---|---|
| Static Assets overview | `/workers/static-assets/` |
| Get started | `/workers/static-assets/get-started/` |
| Configuration and bindings (`assets` keys, `run_worker_first`, `not_found_handling`, `html_handling`) | `/workers/static-assets/binding/` |
| Routing: static site (SSG) and custom 404 pages | `/workers/static-assets/routing/static-site-generation/` |
| Routing: single-page application | `/workers/static-assets/routing/single-page-application/` |
| Routing: full-stack application | `/workers/static-assets/routing/full-stack-application/` |
| Routing: Worker script in front of the assets | `/workers/static-assets/routing/worker-script/` |
| `_headers` file | `/workers/static-assets/headers/` |
| `_redirects` file | `/workers/static-assets/redirects/` |
| Direct Uploads (assets through the API) | `/workers/static-assets/direct-upload/` |
| Billing and limitations | `/workers/static-assets/billing-and-limitations/` |
| Platform limits (file count, file size: see `#static-assets`) | `/workers/platform/limits/` |
| Pricing | `/workers/platform/pricing/` |

## 3. Deploying from GitHub

**Workers Builds** (Cloudflare clones, builds and deploys on push):

| Page | Path |
|---|---|
| CI/CD overview | `/workers/ci-cd/` |
| Builds | `/workers/ci-cd/builds/` |
| Build configuration (build, deploy and preview commands, root directory) | `/workers/ci-cd/builds/configuration/` |
| Git integration / GitHub integration | `/workers/ci-cd/builds/git-integration/`, `/workers/ci-cd/builds/git-integration/github-integration/` |
| Build branches, watch paths (monorepos) | `/workers/ci-cd/builds/build-branches/`, `/workers/ci-cd/builds/build-watch-paths/` |
| Build image (Node, Python versions available) | `/workers/ci-cd/builds/build-image/` |
| Deploy hooks | `/workers/ci-cd/builds/deploy-hooks/` |
| Builds API | `/workers/ci-cd/builds/api-reference/` |
| Troubleshooting builds | `/workers/ci-cd/builds/troubleshoot/` |

**Your own CI** (GitHub Actions runs wrangler):

| Page | Path |
|---|---|
| External CI/CD | `/workers/ci-cd/external-cicd/` |
| GitHub Actions (`cloudflare/wrangler-action`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`) | `/workers/ci-cd/external-cicd/github-actions/` |
| Pages: Direct Upload from CI | `/pages/how-to/use-direct-upload-with-continuous-integration/` |

**Pages Git integration:** `/pages/get-started/git-integration/`,
`/pages/configuration/git-integration/github-integration/`, `/pages/configuration/build-configuration/`,
`/pages/configuration/branch-build-controls/`, `/pages/configuration/preview-deployments/`.

## 4. Deploying without GitHub

| Page | Path |
|---|---|
| Workers from the CLI (`wrangler deploy`) | `/workers/get-started/guide/` |
| Workers from the dashboard | `/workers/get-started/dashboard/` |
| `wrangler deploy` and other general commands | `/workers/wrangler/commands/general/` |
| Pages Direct Upload (wrangler, or drag and drop) | `/pages/get-started/direct-upload/` |
| Pages: a plain static HTML site | `/pages/framework-guides/deploy-anything/` |

## 5. Pages (existing projects)

| Page | Path |
|---|---|
| Custom domains | `/pages/configuration/custom-domains/` |
| `_headers`, `_redirects` | `/pages/configuration/headers/`, `/pages/configuration/redirects/` |
| Serving Pages (trailing slashes, `.html` handling) | `/pages/configuration/serving-pages/` |
| Functions: get started, routing, bindings (D1 and others), configuration | `/pages/functions/get-started/`, `/pages/functions/routing/`, `/pages/functions/bindings/`, `/pages/functions/wrangler-configuration/` |
| Redirect `*.pages.dev` to a custom domain; www to apex | `/pages/how-to/redirect-to-custom-domain/`, `/pages/how-to/www-redirect/` |
| Limits, known issues | `/pages/platform/limits/`, `/pages/platform/known-issues/` |
| `wrangler pages` commands | `/workers/wrangler/commands/pages/` |

## 6. Wrangler

| Page | Path |
|---|---|
| Install / update | `/workers/wrangler/install-and-update/` |
| Configuration file (`wrangler.jsonc` / `.toml`; long, use `--grep`) | `/workers/wrangler/configuration/` |
| Environments (`--env`, staging/production) | `/workers/wrangler/environments/` |
| Commands index; per product: `general`, `workers`, `d1`, `kv`, `r2`, `pages` | `/workers/wrangler/commands/`, `/workers/wrangler/commands/<name>/` |
| System environment variables (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, ...) | `/workers/wrangler/system-environment-variables/` |
| Environment variables and secrets for the Worker | `/workers/configuration/environment-variables/`, `/workers/configuration/secrets/` |

## 7. D1

| Page | Path |
|---|---|
| Get started | `/d1/get-started/` |
| Wrangler commands (`d1 create`, `execute`, `migrations`, `export`) | `/d1/wrangler-commands/` |
| Migrations | `/d1/reference/migrations/` |
| Local development (`--local`, `.wrangler/state`) | `/d1/best-practices/local-development/` |
| Import and export data | `/d1/best-practices/import-export-data/` |
| Query: binding, REST API, wrangler | `/d1/best-practices/query-d1/` |
| Workers binding API (`prepare`, `bind`, `batch`) | `/d1/worker-api/d1-database/` |
| SQL statements, foreign keys | `/d1/sql-api/sql-statements/`, `/d1/sql-api/foreign-keys/` |
| Limits | `/d1/platform/limits/` |
| REST API | `cfdocs.py api d1 database` |

## 8. Domains and DNS

| Page | Path |
|---|---|
| Workers: routes and domains overview | `/workers/configuration/routing/` |
| Workers Custom Domains | `/workers/configuration/routing/custom-domains/` |
| Workers Routes | `/workers/configuration/routing/routes/` |
| workers.dev subdomain | `/workers/configuration/routing/workers-dev/` |
| Add a domain (full setup) / CNAME (partial) setup | `/dns/zone-setups/full-setup/setup/`, `/dns/zone-setups/partial-setup/` |
| DNS records | `/dns/manage-dns-records/how-to/create-dns-records/` |

## 9. Sign-in: Cloudflare Access

Access is under the `cloudflare-one` product, in the nested index `cloudflare-one/access-controls/llms.txt`.

| Page | Path |
|---|---|
| Publish a self-hosted application (protect a site or path) | `/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/` |
| Authorization cookie | `/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/` |
| Validate JWTs (`Cf-Access-Jwt-Assertion`, certs, AUD) | `/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/` |
| Application token (claims) | `/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/application-token/` |
| REST API | `cfdocs.py api access applications` |

## 10. API tokens and the REST API

| Page | Path |
|---|---|
| Create an API token | `/fundamentals/api/get-started/create-token/` |
| Account-owned tokens (for CI) | `/fundamentals/api/get-started/account-owned-tokens/` |
| Token permissions reference | `/fundamentals/api/reference/permissions/` |
| Make API calls | `/fundamentals/api/how-to/make-api-calls/` |
| Find account and zone IDs | `/fundamentals/account/find-account-and-zone-ids/` |
| REST API index | `/api/llms.txt` (use `cfdocs.py api ...`) |

Useful API resources: `api workers scripts`, `api workers scripts assets upload`,
`api pages projects`, `api pages projects deployments`, `api d1 database`, `api dns records`,
`api access applications`, `api zones`.

## 11. Logs and troubleshooting

| Page | Path |
|---|---|
| Workers Logs (`observability` in the config) | `/workers/observability/logs/workers-logs/` |
| Real-time logs (`wrangler tail`) | `/workers/observability/logs/real-time-logs/` |
| Troubleshooting Workers Builds / Pages builds | `/workers/ci-cd/builds/troubleshoot/`, `/pages/configuration/git-integration/troubleshooting/` |
