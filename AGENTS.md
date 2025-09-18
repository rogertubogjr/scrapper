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
- The app expects configuration loaded via `src/app.py` (`app.config.from_pyfile('config.py')`).
  - Provide an instance config file (e.g., `instance/config.py`) with values like `SECRET_KEY` and `TOKEN`.
  - Alternatively, mirror these values via environment variables if you adapt config loading.
- Middleware `api_auth_token.py` expects:
  - `SECRET_KEY`: for JWT decoding.
  - `TOKEN`: for simple header token checks (via `x-access-token`).
- Keep Playwright in headless mode for non‑interactive runs by default. If you change headless behavior, make it configurable.

API Architecture
- Define API resources in `src/modules/<feature>/api.py` using Flask‑RESTful classes.
- Register resources under `src/routes/` to keep route map centralized.
- Put business logic in `use_case.py` (or additional helpers) to keep `api.py` thin.
- Return values:
  - Prefer `dict` or `(dict, status_code)` from resource methods.
  - Use `error_handler` exceptions for consistent error responses.

Playwright Usage
- `src/modules/property/use_case.py` demonstrates async Playwright usage with a helper to run it synchronously.
- Default to `headless=True` for CI/servers; allow overriding via config/env.
- Always close `context`, `browser`, and stop `playwright` in `finally` blocks.
- Avoid fixed sleep; prefer explicit waits (`wait_for_*`) when practical.

Auth Middleware
- `src/middlewares/api_auth_token.py` provides a `requires([...])` decorator.
- Current property endpoint does not enforce auth (decorator commented). If enabling, ensure `x-access-token` header and `SECRET_KEY`/`TOKEN` are configured.

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

Contact & Next Steps
- If you introduce new modules or conventions, add a short note here to keep future work consistent.

