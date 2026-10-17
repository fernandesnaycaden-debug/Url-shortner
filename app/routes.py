import io

import qrcode
from flask import Blueprint, abort, current_app, jsonify, redirect, request, send_file, url_for
from qrcode.image.pil import PilImage

from . import db
from .models import Link
from .utils import generate_code, parse_expiry, validate_alias, validate_url

bp = Blueprint("links", __name__)


def error(message, status):
    return jsonify(error=message), status


def short_url_for(code):
    base = current_app.config.get("BASE_URL") or request.host_url
    return base.rstrip("/") + "/" + code


def get_link_or_404(code):
    link = Link.query.filter_by(code=code).first()
    if link is None:
        abort(404, description=f"No link with code '{code}'")
    return link


def get_active_link_or_error(code):
    link = get_link_or_404(code)
    if link.is_expired():
        # 410 Gone: it existed, but isn't coming back.
        abort(410, description=f"Link '{code}' has expired")
    return link


@bp.get("/")
def index():
    # A small "help" response so visiting the root URL in a browser isn't a 404.
    return jsonify(
        name="URL Shortener API",
        endpoints={
            "POST /shorten": "Create a short link. JSON: {url, alias?, expires_in_days? | expires_at?}",
            "GET /<code>": "Redirect to the original URL",
            "GET /<code>/stats": "Link details and click count",
            "GET /<code>/qr": "QR code PNG",
            "DELETE /<code>": "Delete a link",
        },
    ), 200


@bp.post("/shorten")
def shorten():
    # silent=True returns None instead of raising on bad/missing JSON.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 400)

    url = data.get("url")
    if (msg := validate_url(url)):
        return error(msg, 400)

    expires_at, msg = parse_expiry(data)
    if msg:
        return error(msg, 400)

    alias = data.get("alias")
    if alias is not None:
        if (msg := validate_alias(alias)):
            return error(msg, 400)
        if Link.query.filter_by(code=alias).first():
            return error(f"Alias '{alias}' is already taken", 409)
        code = alias
    else:
        # Random codes can (rarely) collide, so retry a few times.
        length = current_app.config["CODE_LENGTH"]
        for _ in range(5):
            code = generate_code(length)
            if not Link.query.filter_by(code=code).first():
                break
        else:
            return error("Could not generate a unique code, try again", 500)

    link = Link(code=code, original_url=url.strip(), expires_at=expires_at)
    db.session.add(link)
    db.session.commit()

    body = link.to_dict()
    body["short_url"] = short_url_for(code)
    body["qr_url"] = url_for("links.qr", code=code, _external=True)
    return jsonify(body), 201


@bp.get("/<code>")
def follow(code):
    link = get_active_link_or_error(code)
    # Increment in SQL (clicks = clicks + 1) so simultaneous clicks don't overwrite each other.
    Link.query.filter_by(id=link.id).update({Link.clicks: Link.clicks + 1})
    db.session.commit()
    return redirect(link.original_url, code=302)


@bp.get("/<code>/stats")
def stats(code):
    link = get_link_or_404(code)
    body = link.to_dict()
    body["short_url"] = short_url_for(code)
    body["expired"] = link.is_expired()
    return jsonify(body), 200


@bp.get("/<code>/qr")
def qr(code):
    get_active_link_or_error(code)
    img = qrcode.make(short_url_for(code), image_factory=PilImage)
    buf = io.BytesIO()  # build the PNG in memory, no temp files
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name=f"{code}.png")


@bp.delete("/<code>")
def delete(code):
    link = get_link_or_404(code)
    db.session.delete(link)
    db.session.commit()
    return "", 204
