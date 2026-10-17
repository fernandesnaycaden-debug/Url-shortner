from datetime import datetime, timezone

from . import db


def utcnow():
    # Stored as naive UTC: SQLite and MySQL DATETIME columns don't keep timezone info.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, index=True, nullable=False)
    original_url = db.Column(db.Text, nullable=False)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    # An explicit constructor documents the fields (and keeps editors/type checkers happy,
    # since they can't see the keyword arguments SQLAlchemy generates automatically).
    def __init__(self, code, original_url, expires_at=None):
        self.code = code
        self.original_url = original_url
        self.expires_at = expires_at

    def is_expired(self):
        return self.expires_at is not None and self.expires_at <= utcnow()

    def to_dict(self):
        return {
            "code": self.code,
            "original_url": self.original_url,
            "clicks": self.clicks,
            "created_at": self.created_at.isoformat() + "Z",
            "expires_at": self.expires_at.isoformat() + "Z" if self.expires_at else None,
        }
