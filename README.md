# URL Shortener API (Flask)

A small REST API built with Flask and SQLAlchemy that shortens URLs. It supports click counting, custom aliases, expiry dates and QR codes.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py          # serves on http://localhost:5000
pytest                 # runs the test suite
```

## Endpoints

| Method | Path | Description | Status codes |
|---|---|---|---|
| POST | `/shorten` | Create a short link | 201, 400, 409 |
| GET | `/<code>` | Redirect to the original URL (+1 click) | 302, 404, 410 |
| GET | `/<code>/stats` | Show link details and click count | 200, 404 |
| GET | `/<code>/qr` | QR code PNG for the short link | 200, 404, 410 |
| DELETE | `/<code>` | Delete a link | 204, 404 |

Every error comes back as JSON in the form `{"error": "..."}`.

### `POST /shorten` body

```jsonc
{
  "url": "https://example.com/some/long/path",   // required, http(s) only
  "alias": "my-link",                             // optional, 3-32 chars [A-Za-z0-9_-]
  "expires_in_days": 7                            // optional (or use expires_at below)
  // "expires_at": "2026-12-31T23:59:59Z"         // optional ISO 8601 (UTC if no offset)
}
```

## Try it

```bash
curl -X POST localhost:5000/shorten -H "Content-Type: application/json" -d "{\"url\":\"https://example.com\",\"alias\":\"example\"}"
curl -i localhost:5000/example        # 302 with a Location header
curl localhost:5000/example/stats     # "clicks": 1
# open http://localhost:5000/example/qr in a browser
```

## Switching to MySQL

1. Run `pip install pymysql`.
2. Create the database: `CREATE DATABASE shortener;`
3. Set the env var before running:
   `$env:DATABASE_URL = "mysql+pymysql://user:pass@localhost/shortener"`

Tables are created automatically at startup with `db.create_all()`.

## Next steps
- Use Flask-Migrate (Alembic) for schema migrations instead of `create_all()`.
- Add rate limiting (Flask-Limiter) on `/shorten`.
- Add API keys so only authorized clients can create or delete links.
