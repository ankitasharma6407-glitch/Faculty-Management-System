import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-key"
    )

    MYSQL_USER = os.getenv(
        "MYSQL_USER",
        "root"
    )

    MYSQL_PASSWORD = os.getenv(
        "MYSQL_PASSWORD",
        ""
    )

    MYSQL_HOST = os.getenv(
        "MYSQL_HOST",
        "localhost"
    )

    MYSQL_PORT = os.getenv(
        "MYSQL_PORT",
        "3306"
    )

    MYSQL_DATABASE = os.getenv(
        "MYSQL_DATABASE",
        "fmps_db"
    )

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://"
        f"{MYSQL_USER}:"
        f"{quote_plus(MYSQL_PASSWORD)}@"
        f"{MYSQL_HOST}:"
        f"{MYSQL_PORT}/"
        f"{MYSQL_DATABASE}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "jwt-dev-secret-key"
    )

    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "uploads"
    )

    ALLOWED_IMAGE_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "pdf"
    }

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500"
    ).split(",")