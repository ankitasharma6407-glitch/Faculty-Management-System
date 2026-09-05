from datetime import datetime
import math

from flask import Blueprint
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash

from ..extensions import db
from ..models import User, FaceEncoding
from ..utils import body, fail, ok


bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


# ============================================================
# FACE RECOGNITION SETTINGS
# ============================================================

FACE_MATCH_THRESHOLD = 0.55


# ============================================================
# FACE DESCRIPTOR HELPER
# ============================================================

def normalize_face_descriptor(descriptor):
    """
    face-api.js returns a 128-value descriptor.
    Validate and convert every value to float.
    """

    if not isinstance(descriptor, list):
        return None

    if len(descriptor) != 128:
        return None

    try:
        return [
            float(value)
            for value in descriptor
        ]

    except (TypeError, ValueError):
        return None


# ============================================================
# FACE DISTANCE
# ============================================================

def calculate_face_distance(
    descriptor_one,
    descriptor_two
):
    if (
        descriptor_one is None
        or descriptor_two is None
    ):
        return None

    if len(descriptor_one) != len(descriptor_two):
        return None

    return math.sqrt(
        sum(
            (first - second) ** 2
            for first, second in zip(
                descriptor_one,
                descriptor_two
            )
        )
    )


# ============================================================
# CREATE JWT TOKENS
# ============================================================

def create_user_tokens(user):
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role
        }
    )

    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role
        }
    )

    return access_token, refresh_token


# ============================================================
# LOGIN
# ============================================================

@bp.post("/login")
def login():
    data = body()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not password or (not username and not email):
        return fail(
            "Username/email and password are required",
            422
        )

    # Login using username OR email
    if username:
        user = User.query.filter_by(
            username=username
        ).first()

    else:
        user = User.query.filter_by(
            email=email
        ).first()

    if user is None:
        return fail(
            "Invalid credentials",
            401
        )

    if not check_password_hash(
        user.password_hash,
        password
    ):
        return fail(
            "Invalid credentials",
            401
        )

    if not user.is_active:
        return fail(
            "Account is disabled",
            403
        )

    user.last_login = datetime.utcnow()

    db.session.commit()

    access_token, refresh_token = (
        create_user_tokens(user)
    )

    return ok(
        {
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        "Logged in successfully"
    )


# ============================================================
# REFRESH TOKEN
# ============================================================

@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()

    user = db.session.get(
        User,
        int(user_id)
    )

    if user is None or not user.is_active:
        return fail(
            "Account is inactive",
            401
        )

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role
        }
    )

    return ok(
        {
            "access_token": access_token
        }
    )


# ============================================================
# CURRENT USER
# ============================================================

@bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()

    user = db.session.get(
        User,
        int(user_id)
    )

    if user is None:
        return fail(
            "User not found",
            404
        )

    return ok(
        user.to_dict()
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@bp.post("/change-password")
@jwt_required()
def change_password():
    data = body()

    current_password = data.get(
        "current_password"
    )

    new_password = data.get(
        "new_password"
    )

    confirm_password = data.get(
        "confirm_password"
    )

    if (
        not current_password
        or not new_password
        or not confirm_password
    ):
        return fail(
            "Current password, new password and confirm password are required",
            422
        )

    if new_password != confirm_password:
        return fail(
            "New password and confirm password do not match",
            400
        )

    if len(new_password) < 8:
        return fail(
            "New password must be at least 8 characters long",
            400
        )

    user_id = get_jwt_identity()

    user = db.session.get(
        User,
        int(user_id)
    )

    if user is None:
        return fail(
            "User not found",
            404
        )

    if not user.is_active:
        return fail(
            "Account is disabled",
            403
        )

    if not user.check_password(
        current_password
    ):
        return fail(
            "Current password is incorrect",
            400
        )

    if user.check_password(
        new_password
    ):
        return fail(
            "New password must be different from current password",
            400
        )

    user.set_password(
        new_password
    )

    db.session.commit()

    return ok(
        message="Password changed successfully"
    )


# ============================================================
# FACE REGISTRATION STATUS
# ============================================================

@bp.get("/face/status")
@jwt_required()
def face_status():
    user_id = get_jwt_identity()

    user = db.session.get(
        User,
        int(user_id)
    )

    if user is None:
        return fail(
            "User not found",
            404
        )

    face = FaceEncoding.query.filter_by(
        user_id=user.id
    ).first()

    return ok(
        {
            "registered": face is not None,
            "face": (
                face.to_dict()
                if face
                else None
            )
        }
    )


# ============================================================
# REGISTER / UPDATE FACE
# ============================================================

@bp.post("/face/register")
@jwt_required()
def register_face():
    data = body()

    descriptor = normalize_face_descriptor(
        data.get("descriptor")
    )

    if descriptor is None:
        return fail(
            "A valid 128-value face descriptor is required",
            422
        )

    user_id = get_jwt_identity()

    user = db.session.get(
        User,
        int(user_id)
    )

    if user is None:
        return fail(
            "User not found",
            404
        )

    if not user.is_active:
        return fail(
            "Account is disabled",
            403
        )

    existing_face = (
        FaceEncoding.query
        .filter_by(
            user_id=user.id
        )
        .first()
    )

    # Update existing registered face
    if existing_face:
        existing_face.descriptor = descriptor

        db.session.commit()

        return ok(
            existing_face.to_dict(),
            "Face updated successfully"
        )

    # Register new face
    face = FaceEncoding(
        user_id=user.id,
        descriptor=descriptor,
        image_url=None
    )

    db.session.add(face)

    db.session.commit()

    return ok(
        face.to_dict(),
        "Face registered successfully"
    )


# ============================================================
# DELETE REGISTERED FACE
# ============================================================

@bp.delete("/face")
@jwt_required()
def remove_face():
    user_id = get_jwt_identity()

    face = (
        FaceEncoding.query
        .filter_by(
            user_id=int(user_id)
        )
        .first()
    )

    if face is None:
        return fail(
            "No registered face found",
            404
        )

    db.session.delete(face)

    db.session.commit()

    return ok(
        message="Registered face removed successfully"
    )


# ============================================================
# FACE LOGIN
# ============================================================
@bp.post("/face/login")
def face_login():

    data = body()

    # Keep the existing Admin face-login flow backward compatible: older
    # Admin pages do not send a role, so Admin remains the safe default.
    # HOD and Teacher face-login pages send their own role. Matching stays
    # limited to that role, preventing biometric mix-ups across panels.
    requested_role = str(
        data.get("role") or "admin"
    ).strip().lower()

    if requested_role not in {"admin", "hod", "teacher"}:
        return fail(
            "Face login role must be admin, hod or teacher",
            422
        )

    descriptor = normalize_face_descriptor(
        data.get("descriptor")
    )

    if descriptor is None:
        return fail(
            "A valid 128-value face descriptor is required",
            400
        )


    # =========================================================
    # GET ACTIVE USERS OF THE REQUESTED ROLE WITH REGISTERED FACE
    # =========================================================

    candidates = (
        db.session.query(
            FaceEncoding,
            User
        )
        .join(
            User,
            User.id == FaceEncoding.user_id
        )
        .filter(
            User.role == requested_role,
            User.is_active.is_(True)
        )
        .all()
    )


    if not candidates:
        return fail(
            f"No registered {requested_role.upper()} face found",
            404
        )


    # =========================================================
    # FIND CLOSEST FACE
    # =========================================================

    best_user = None
    best_distance = None


    for face_encoding, user in candidates:

        stored_descriptor = normalize_face_descriptor(
            face_encoding.descriptor
        )

        if stored_descriptor is None:
            continue


        distance = calculate_face_distance(
            descriptor,
            stored_descriptor
        )


        if distance is None:
            continue


        if (
            best_distance is None
            or distance < best_distance
        ):
            best_distance = distance
            best_user = user


    # =========================================================
    # NO VALID FACE
    # =========================================================

    if (
        best_user is None
        or best_distance is None
    ):
        return fail(
            f"No valid registered {requested_role.upper()} face found",
            404
        )


    # =========================================================
    # FACE MATCH CHECK
    # =========================================================

    if best_distance > FACE_MATCH_THRESHOLD:
        return fail(
            "Face not recognized",
            401
        )


    # =========================================================
    # LOGIN SUCCESS
    # =========================================================

    best_user.last_login = datetime.utcnow()

    db.session.commit()


    access_token, refresh_token = create_user_tokens(
        best_user
    )


    return ok(
        {
            "user": best_user.to_dict(
                with_profile=True
            ),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "face_distance": round(
                best_distance,
                4
            ),
        },
        "Face login successful"
    )


# ============================================================
# LOGOUT
# ============================================================

@bp.post("/logout")
@jwt_required()
def logout():
    return ok(
        message="Logged out successfully"
    )


