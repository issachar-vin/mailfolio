# mailfolio

A lightweight FastAPI microservice that receives contact form submissions and delivers them to your inbox via Gmail SMTP. Designed to sit behind a frontend contact form and be deployed as a container.

## How it works

`POST /submit` accepts a JSON payload, validates the request `Origin` header against a configurable allowlist, then sends the message as an email using a Gmail App Password. Origin patterns support wildcards (e.g. `*.example.com`).

## Requirements

- Python 3.12+
- A Gmail account with a [Gmail App Password](https://support.google.com/accounts/answer/185833) configured
- [uv](https://docs.astral.sh/uv/) for local development

## Configuration

All configuration is via environment variables. Create a `.env` file at the project root (see `.env.example` if present):

| Variable | Description | Example |
|---|---|---|
| `GMAIL_USER` | Gmail address used as the sender | `you@gmail.com` |
| `GMAIL_APP_PASSWORD` | 16-character Gmail App Password | `abcd efgh ijkl mnop` |
| `MAIL_TO` | Address that receives contact form emails | `inbox@yourdomain.com` |
| `VALID_ORIGINS` | Comma-separated allowed origin domains or wildcard patterns | `yourdomain.com,*.staging.yourdomain.com` |

### `VALID_ORIGINS` format

Values are bare hostnames or [`fnmatch`](https://docs.python.org/3/library/fnmatch.html) wildcard patterns — **no scheme**:

```
# exact match
VALID_ORIGINS=yourdomain.com

# wildcard subdomain — matches app.yourdomain.com, www.yourdomain.com, etc.
VALID_ORIGINS=*.yourdomain.com

# multiple patterns
VALID_ORIGINS=yourdomain.com,*.staging.yourdomain.com
```

Schemes (`https://`) are stripped automatically if you accidentally include them.

> **Note:** `fnmatch` `*` crosses dots, so `*.example.com` also matches `deep.sub.example.com`. Add more-specific patterns to restrict to a single subdomain level.

## Running locally

```bash
uv sync
uv run fastapi dev mailfolio/main.py
```

## Running with Docker

```bash
docker compose up --build
```

The container listens on port `8000`.

## API

### `POST /submit`

Submit a contact form message.

**Request body (JSON):**

| Field | Type | Required | Default |
|---|---|---|---|
| `name` | string | yes | — |
| `email` | email address | yes | — |
| `message` | string | yes | — |
| `subject` | string | no | `"Contact form submission"` |

**Responses:**

| Status | Meaning |
|---|---|
| `202` | Message sent — `{"status": "sent"}` |
| `403` | Request `Origin` not in `VALID_ORIGINS` |
| `422` | Validation error (bad email, missing fields) |

### `GET /health`

Returns `200 {"status": "ok"}`. Use this for container health checks.

## Development

```bash
# Install deps
uv sync

# Lint and format
make lint

# Run tests
make test
```
