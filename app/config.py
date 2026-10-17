import os


class Config:
    # SQLite by default. To use MySQL, set DATABASE_URL, e.g.
    #   mysql+pymysql://user:pass@localhost/shortener
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///urls.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Public base for generated short links. If unset, the request's host is used.
    BASE_URL = os.getenv("BASE_URL")

    # Length of auto-generated codes (62^6 ≈ 56 billion combinations).
    CODE_LENGTH = 6
