# mailfolio — Claude context

## What this is

A single-endpoint FastAPI microservice. It receives contact form JSON, validates the request origin, and forwards the message as an email via Gmail SMTP. No database, no auth, no state beyond app startup.

## Project layout

```
mailfolio/
  config.py   — pydantic-settings; all env var parsing lives here
  mailer.py   — Mailer protocol + GmailMailer implementation
  main.py     — FastAPI app, lifespan, dependency providers, routes
tests/
  test_main.py
```

## Key design decisions

**`Mailer` Protocol** — `main.py` depends on the `Mailer` protocol, not on `GmailMailer` directly. This means you can add alternative mailer implementations (e.g. SendGrid) without touching `main.py`. Tests inject a `MagicMock` through `app.state` rather than the DI system.

**Origin validation** — `VALID_ORIGINS` stores bare hostnames (no scheme). The validator in `config.py` strips schemes on load. At request time, `_origin_hostname` in `main.py` strips the scheme from the incoming `Origin` header, then `_is_allowed` uses `fnmatch.fnmatch` for wildcard pattern matching. The `in` operator is intentionally not used — it only does exact matches.

**No async on `GmailMailer.send`** — smtplib is synchronous. For high-throughput use, this should move to a background task or be replaced with an async SMTP library (e.g. `aiosmtplib`). Not a problem at contact-form volumes.

## Commands

```bash
uv sync            # install deps
make lint          # ruff check + format
make test          # pytest
make dev           # docker compose up (hot reload)
```

## Environment variables

See README.md for the full table. Local dev uses a `.env` file at the project root.

## Testing approach

Tests use `TestClient` (synchronous) with `MagicMock` injected directly into `app.state` before each test. The lifespan is not exercised in tests — settings and mailer are set manually on the fixture. This keeps tests fast and avoids needing real credentials.
