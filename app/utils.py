import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

ALPHABET = string.ascii_letters + string.digits  # base62
ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
RESERVED = {"shorten", "static", "api"}
MAX_URL_LENGTH = 2048


def generate_code(length):
    # secrets (not random) so codes aren't predictable/guessable.
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def validate_url(url):
    """Return an error message, or None if the URL is acceptable."""
    if not isinstance(url, str) or not url.strip():
        return "'url' is required and must be a string"
    if len(url) > MAX_URL_LENGTH:
        return f"'url' must be at most {MAX_URL_LENGTH} characters"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "'url' must be a valid http(s) URL"
    return None


def validate_alias(alias):
    if not isinstance(alias, str) or not ALIAS_RE.match(alias):
        return "'alias' must be 3-32 characters: letters, digits, '-' or '_'"
    if alias.lower() in RESERVED:
        return f"'alias' cannot be one of: {', '.join(sorted(RESERVED))}"
    return None


def parse_expiry(data):
    """Read expires_in_days or expires_at from the request body.

    Returns (naive_utc_datetime_or_None, error_message_or_None).
    """
    now = datetime.now(timezone.utc)

    if "expires_in_days" in data:
        days = data["expires_in_days"]
        # bool is a subclass of int in Python, so exclude it explicitly.
        if isinstance(days, bool) or not isinstance(days, (int, float)) or days <= 0:
            return None, "'expires_in_days' must be a positive number"
        return (now + timedelta(days=days)).replace(tzinfo=None), None

    if "expires_at" in data:
        raw = data["expires_at"]
        try:
            # Accept a trailing "Z" (fromisoformat only handles it on Python 3.11+).
            expires = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            return None, "'expires_at' must be an ISO 8601 datetime"
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)  # assume UTC if no offset
        if expires <= now:
            return None, "'expires_at' must be in the future"
        return expires.astimezone(timezone.utc).replace(tzinfo=None), None

    return None, None
