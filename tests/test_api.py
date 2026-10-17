from datetime import timedelta

from app import db
from app.models import Link, utcnow


def shorten(client, **body):
    return client.post("/shorten", json=body)


def test_shorten_success(client):
    res = shorten(client, url="https://example.com")
    assert res.status_code == 201
    data = res.get_json()
    assert len(data["code"]) == 6
    assert data["short_url"].endswith("/" + data["code"])
    assert data["clicks"] == 0


def test_invalid_url(client):
    assert shorten(client, url="not-a-url").status_code == 400
    assert shorten(client, url="ftp://example.com").status_code == 400


def test_missing_body(client):
    assert client.post("/shorten").status_code == 400
    assert client.post("/shorten", data="junk", content_type="application/json").status_code == 400


def test_custom_alias_and_conflict(client):
    assert shorten(client, url="https://a.com", alias="mylink").status_code == 201
    assert shorten(client, url="https://b.com", alias="mylink").status_code == 409


def test_invalid_alias(client):
    assert shorten(client, url="https://a.com", alias="x").status_code == 400
    assert shorten(client, url="https://a.com", alias="shorten").status_code == 400
    assert shorten(client, url="https://a.com", alias="bad alias!").status_code == 400


def test_redirect_increments_clicks(client):
    shorten(client, url="https://example.com", alias="ex1")
    res = client.get("/ex1")
    assert res.status_code == 302
    assert res.headers["Location"] == "https://example.com"
    client.get("/ex1")
    assert client.get("/ex1/stats").get_json()["clicks"] == 2


def test_unknown_code(client):
    res = client.get("/nope123")
    assert res.status_code == 404
    assert "error" in res.get_json()


def test_expired_link(client, app):
    shorten(client, url="https://example.com", alias="old")
    with app.app_context():
        link = Link.query.filter_by(code="old").first()
        link.expires_at = utcnow() - timedelta(seconds=1)
        db.session.commit()
    assert client.get("/old").status_code == 410
    assert client.get("/old/stats").get_json()["expired"] is True


def test_expiry_validation(client):
    assert shorten(client, url="https://a.com", expires_in_days=-1).status_code == 400
    assert shorten(client, url="https://a.com", expires_at="2000-01-01T00:00:00Z").status_code == 400
    assert shorten(client, url="https://a.com", expires_at="garbage").status_code == 400
    res = shorten(client, url="https://a.com", expires_in_days=7)
    assert res.status_code == 201
    assert res.get_json()["expires_at"] is not None


def test_qr_returns_png(client):
    shorten(client, url="https://example.com", alias="qrme")
    res = client.get("/qrme/qr")
    assert res.status_code == 200
    assert res.mimetype == "image/png"
    assert res.data.startswith(b"\x89PNG")


def test_delete(client):
    shorten(client, url="https://example.com", alias="gone")
    assert client.delete("/gone").status_code == 204
    assert client.get("/gone").status_code == 404
    assert client.delete("/gone").status_code == 404


def test_method_not_allowed_is_json(client):
    res = client.get("/shorten")
    # GET /shorten matches /<code> -> 404 because "shorten" is reserved and never stored.
    assert res.status_code == 404
    res = client.put("/shorten")
    assert res.status_code == 405
    assert "error" in res.get_json()
