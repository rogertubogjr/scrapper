Project Agents Guide (AGENTS.md)

Purpose

- This guide gives agents clear, repo‑specific instructions for safely making changes, running, and extending this project.
- Follow these rules for any work inside this repo unless a task explicitly says otherwise.

Scope Rules

- The scope of this file applies to the entire repository.
- Obey the instructions here for every file you touch in this repo.
- Prefer minimal, targeted changes; avoid unrelated edits or refactors.
- Update docs when behavior or interfaces change.

Repo Overview

- Stack: Python 3.12, Flask + Flask‑RESTful API, Playwright (async), CORS.
- Entry: `run.py` starts the app on `0.0.0.0:5001`.
- App: `src/app.py` configures Flask, CORS (in debug), and wires routes.
- Routes: `src/routes/` registers resources (e.g., `property.py`).
- Feature modules: `src/modules/<feature>/` hold `api.py` (Resources) and `use_case.py` (logic).
- Middleware: `src/middlewares/` (e.g., token auth decorators).
- Errors: `src/handler/error_handler.py` centralizes HTTP‑friendly exceptions.

Docker & VPS (Ubuntu) Compatibility

- Images/Runtime:
  - Use the provided `Dockerfile` based on `mcr.microsoft.com/playwright/python:v1.55.0-noble` (browsers preinstalled).
  - Dev orchestration via `docker-compose.yml` (service `api`, port `5001`, `shm_size: 1gb`).
  - Production orchestration via `docker-compose-prod.yml` (no source mounts, restart policy, json-file logging).
- Local dev with Docker:
  - Build/run: `docker compose up --build`
  - Logs: `docker compose logs -f api`
  - Stop: `docker compose down`
- VPS (Ubuntu Server):
  - Install Docker Engine + Compose plugin, copy repo, set `.env`, then `docker compose up -d --build`.
  - Keep `PLAYWRIGHT_HEADLESS=true` by default; no extra Linux deps needed (Playwright base image includes them).
  - Expose port `5001` or run behind a reverse proxy (e.g., Nginx). Do not run privileged containers.
- Non-Docker local dev remains supported (venv + `playwright install`) but Docker is recommended for parity with VPS.

Local Run

- Create and activate a venv, then install deps:
  - `python -m venv venv && source venv/bin/activate`
  - `pip install -r requirements.txt`
- Install Playwright browsers locally (needed for scraping):
  - `python -m playwright install`
- Start the API:
  - `python run.py`
- Health check (example endpoint):
  - `GET http://localhost:5001/properties` → returns JSON (currently placeholder).

Configuration & Secrets

- Do not commit or print secrets. Never echo full `.env` contents in logs or PRs.
- Config loading: `src/app.py` loads `instance/config.py` via `app.config.from_pyfile('config.py')`.
  - `instance/config.py` loads environment variables via `python-dotenv` if a `.env` file is present.
  - Core keys: `DEBUG`, `SECRET_KEY`, `TOKEN`, `PLAYWRIGHT_HEADLESS` (default True), `PLAYWRIGHT_ARGS`.
  - Optional keys used by scrapers:
    - `PLAYWRIGHT_STEALTH` (default True): hide `navigator.webdriver` via init script.
    - `PLAYWRIGHT_DEBUG_ARTIFACTS` (default False): when enabled and a scrape yields zero results, saves `/tmp/properties_screenshot.png` and `/tmp/properties_snippet.html` for debugging.
    - `PLAYWRIGHT_DEBUG_PRINT` (default False): when enabled, logs the page title and a truncated HTML snippet (default 10k chars) at WARNING level after navigation.
    - `PLAYWRIGHT_DEBUG_PRINT_MAX` (default 10000): max characters of HTML to log when debug print is enabled.
- Auth expectations for `api_auth_token.py`:
  - `TOKEN` for static token checks, or `SECRET_KEY` for JWT (HS256) verification.
  - Clients may send tokens via `x-access-token` or `Authorization: Bearer <token>`.
- Default Playwright headless for servers/CI. If headless behavior changes, make it configurable and ensure Docker/VPS compatibility.

API Architecture

- Define API resources in `src/modules/<feature>/api.py` using Flask‑RESTful classes.
- Register resources under `src/routes/` to keep route map centralized.
- Put business logic in `use_case.py` (or additional helpers) to keep `api.py` thin.
- Return values:
  - Prefer `dict` or `(dict, status_code)` from resource methods.
  - Use `error_handler` exceptions for consistent error responses.

Playwright Usage

- `src/modules/property/use_case.py` demonstrates async Playwright usage; it currently hardcodes `headless=False`.
- `src/modules/property/use_case2.py` is the recommended pattern:
  - Respects `PLAYWRIGHT_HEADLESS` and `PLAYWRIGHT_ARGS` from config.
  - Uses explicit waits instead of fixed sleeps.
  - Ensures clean resource teardown (context/broswer) using async context managers.
  - Handles common consent banners and applies light stealth; can save debug artifacts when enabled.
- For Docker/VPS, prefer the `use_case2.py` approach or update existing use-cases to read config for headless/args.

Auth Middleware

- `src/middlewares/api_auth_token.py` provides a `requires([...])` decorator.
- Behavior:
  - Supports tokens from `x-access-token` or `Authorization: Bearer <token>`.
  - Authorizes via either a static token (`TOKEN`) or a JWT signed with `SECRET_KEY` (HS256).
  - Uses `current_app` to avoid import cycles, avoids printing secrets, and returns consistent errors.
- Current property endpoint does not enforce auth (decorator commented). If enabling, document required headers for clients.

Error Handling

- Raise `InvalidDataError`, `NotFoundError`, `UnauthorizedError`, or `UnexpectedError` from `src/handler/error_handler.py`.
- Don’t return raw strings for errors. Use exceptions to get proper HTTP codes.

Coding Conventions

- Python: PEP 8, 4‑space indents, snake_case for functions/vars, CapWords for classes.
- Module layout:
  - `src/modules/<feature>/api.py` for Flask‑RESTful Resources.
  - `src/modules/<feature>/use_case.py` for business logic and external interactions.
  - Register in `src/routes/<feature>.py`.
- Logging: use `logging` (configured in debug) instead of `print` for new code.
- Keep functions small and side‑effect aware; separate concerns (I/O vs logic).

Adding A New Endpoint (Checklist)

- Create `src/modules/<feature>/use_case.py` with the core logic.
- Create `src/modules/<feature>/api.py` exposing a `Resource` that calls the use‑case.
- Add route in `src/routes/<feature>.py` and import from `src/app.py` if needed.
- Consider auth with `@requires([...])` and document required headers.
- Return JSON dicts; raise typed errors for failures.
- Add minimal docstrings and update this file if you introduce patterns.

Testing & Validation

- No formal tests present. Validate endpoints via curl or Postman.
- For Playwright flows, verify that headless mode works and resources close cleanly.
- Keep changes small and test the specific area you touched.

Operational Notes

- Server runs on port `5001`. Adjust only via config and update docs if changed.
- Network scraping sites may block automation; use realistic user agents and respectful delays.
- Be mindful of rate limits and robots.txt for any new scrapers.

Agent Working Rules

- Keep changes minimal and focused on the user’s request.
- Don’t change filenames, public interfaces, or behavior unless necessary for the task—if you must, document and justify in your summary.
- Do not fix unrelated bugs; you may call them out in notes.
- When you add dependencies, update `requirements.txt` and mention any install steps (e.g., `playwright install`).
- Never include secrets (keys, tokens) in code or logs; redactions are mandatory.

Quick Commands

- Setup: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Playwright: `python -m playwright install`
- Run: `python run.py`
- Example request: `curl http://localhost:5001/properties`
- Docker (dev): `docker compose up --build`
- Docker logs: `docker compose logs -f api`
- Docker stop: `docker compose down`
- Docker (prod): `docker compose -f docker-compose-prod.yml up -d --build`

Contact & Next Steps

- If you introduce new modules or conventions, add a short note here to keep future work consistent.
- Maintain Docker/VPS compatibility for any new endpoints, middlewares, or Playwright changes (headless config, args, and resource teardown). Add notes here when patterns change.

Git Flow

- Branch roles: `main` = production; `develop` = integration.
- Prefixes: `feature/`, `bugfix/`, `release/`, `hotfix/`, `support/`; tags prefixed with `v` (e.g., `v1.2.3`).
- Start work:
  - Feature: `git flow feature start <slug>` → PR to `develop`.
  - Bugfix: `git flow bugfix start <slug>` → PR to `develop`.
- Stabilize/release:
  - Release: `git flow release start <x.y.z>`; finalize via PRs to `main` and back-merge into `develop`.
  - Hotfix: `git flow hotfix start <x.y.z>` from `main`; finalize via PRs to `main` and back-merge into `develop`.
- Finish with PRs (no direct pushes to protected branches). Use squash or merge per repo policy.
  Solo Branch Protection (Optional Now)

- main
  - Require a pull request before merging.
  - Required reviews: 0 (solo developer).
  - Required status checks: `lint` only (add CI job named `lint`).
  - Optional: require branches to be up to date; require conversation resolution; disallow force pushes and deletions; enforce on admins if you want no bypass.
- develop
  - Option A: mirror `main` without required checks (no blockers).
  - Option B: leave unprotected; keep a PR habit when feasible.
- How to enable later (UI steps)
  - Create `.github/workflows/lint.yml` with a job named `lint` (e.g., ruff/flake8) that runs on PRs to `main`.
  - GitHub → Settings → Branches → Add rule for `main`:
    - Require a pull request before merging; set required reviews to 0.
    - Require status checks to pass before merging → select `lint`.
    - Optionally: require branches to be up to date; require conversation resolution; block force pushes/deletions.
  - Optionally add a rule for `develop` with no required checks.
