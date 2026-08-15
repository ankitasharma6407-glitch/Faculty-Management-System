import os
import uuid
from datetime import datetime, date
from functools import wraps

from flask import current_app, jsonify, request
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
)
from werkzeug.utils import secure_filename

from .extensions import db
from .models import AuditLog, Notification, User


class ApiError(Exception):
    def __init__(self, message, status=400, details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details


def ok(data=None, message=None, status=200, **extra):
    payload = {"success": True}

    if message:
        payload["message"] = message

    if data is not None:
        payload["data"] = data

    payload.update(extra)

    return jsonify(payload), status


def fail(message, status=400, details=None):
    payload = {
        "success": False,
        "message": message
    }

    if details:
        payload["errors"] = details

    return jsonify(payload), status


def body():
    return request.get_json(silent=True) or {}


def require_fields(data, fields):
    missing = [
        field
        for field in fields
        if data.get(field) in (None, "")
    ]

    if missing:
        raise ApiError(
            "Missing required fields",
            422,
            {field: "required" for field in missing}
        )


def parse_date(value, field="date"):
    if value in (None, ""):
        return None

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(
            str(value)[:10],
            "%Y-%m-%d"
        ).date()
    except ValueError as exc:
        raise ApiError(
            f"Invalid date for '{field}', expected YYYY-MM-DD",
            422
        ) from exc


def parse_time(value, field="time"):
    if value in (None, ""):
        return None

    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(str(value), fmt).time()
        except ValueError:
            continue

    raise ApiError(
        f"Invalid time for '{field}', expected HH:MM",
        422
    )


def current_user():
    identity = get_jwt_identity()

    if identity is None:
        return None

    return db.session.get(User, int(identity))


def roles_required(*roles):
    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            verify_jwt_in_request()

            claims = get_jwt()

            if roles and claims.get("role") not in roles:
                return fail(
                    "You do not have permission to perform this action",
                    403
                )

            user = current_user()

            if user is None or not user.is_active:
                return fail(
                    "Account is inactive or no longer exists",
                    401
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def paginate(query, schema=lambda i: i.to_dict()):
    page = request.args.get("page", 1, type=int)

    per_page = min(
        request.args.get("per_page", 20, type=int),
        100
    )

    result = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return ok(
        [schema(item) for item in result.items],
        meta={
            "page": result.page,
            "per_page": result.per_page,
            "total": result.total,
            "pages": result.pages,
        }
    )


def apply_updates(instance, data, fields):
    for field in fields:
        if field in data:
            setattr(instance, field, data[field])


def notify(
    user_id,
    title,
    message=None,
    category="general",
    link=None
):
    db.session.add(
        Notification(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            link=link
        )
    )


def audit(
    action,
    entity=None,
    entity_id=None,
    details=None
):
    try:
        uid = get_jwt_identity()
    except Exception:
        uid = None

    db.session.add(
        AuditLog(
            user_id=int(uid) if uid else None,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr
        )
    )


def save_upload(file_storage, subdir="misc"):
    if not file_storage or not file_storage.filename:
        return None

    ext = file_storage.filename.rsplit(".", 1)[-1].lower()

    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        raise ApiError(
            "Unsupported file type",
            422
        )

    folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        subdir
    )

    os.makedirs(folder, exist_ok=True)

    filename = (
        f"{uuid.uuid4().hex}_"
        f"{secure_filename(file_storage.filename)}"
    )

    file_storage.save(
        os.path.join(folder, filename)
    )

    return f"/uploads/{subdir}/{filename}"