from flask import Blueprint, jsonify, request

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

from ..extensions import db
from ..models import User, Notification


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/api/notifications"
)


# ============================================================
# GET CURRENT USER NOTIFICATIONS
#
# GET /api/notifications
# ============================================================

@bp.get("")
@jwt_required()
def get_my_notifications():

    try:

        identity = get_jwt_identity()

        try:
            user_id = int(identity)

        except (TypeError, ValueError):

            return jsonify({
                "success": False,
                "message": "Invalid login session"
            }), 401


        user = db.session.get(
            User,
            user_id
        )


        if not user:

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404


        if not user.is_active:

            return jsonify({
                "success": False,
                "message": "Account is inactive"
            }), 403


        # Optional filter:
        # /api/notifications?is_read=false

        is_read_value = (
            request.args
            .get(
                "is_read",
                ""
            )
            .strip()
            .lower()
        )


        query = (
            Notification.query
            .filter(
                Notification.user_id
                == user.id
            )
        )


        if is_read_value in (
            "true",
            "1"
        ):

            query = query.filter(
                Notification.is_read.is_(True)
            )


        elif is_read_value in (
            "false",
            "0"
        ):

            query = query.filter(
                Notification.is_read.is_(False)
            )


        notifications = (
            query
            .order_by(
                Notification.created_at.desc(),
                Notification.id.desc()
            )
            .all()
        )


        total = (
            Notification.query
            .filter(
                Notification.user_id
                == user.id
            )
            .count()
        )


        unread = (
            Notification.query
            .filter(
                Notification.user_id
                == user.id,
                Notification.is_read.is_(False)
            )
            .count()
        )


        return jsonify({

            "success": True,

            "summary": {
                "total": total,
                "unread": unread,
                "read": total - unread
            },

            "data": [
                notification.to_dict()
                for notification
                in notifications
            ]

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load notifications.",

            "error":
                str(error)

        }), 500

@bp.patch("/<int:notification_id>/read")
@jwt_required()
def mark_notification_read(notification_id):

    identity = get_jwt_identity()

    try:
        user_id = int(identity)

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid login session"
        }), 401


    user = db.session.get(
        User,
        user_id
    )


    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404


    if not user.is_active:
        return jsonify({
            "success": False,
            "message": "Account is inactive"
        }), 403


    notification = (
        Notification.query
        .filter_by(
            id=notification_id,
            user_id=user.id
        )
        .first()
    )


    if not notification:
        return jsonify({
            "success": False,
            "message": "Notification not found"
        }), 404


    notification.is_read = True

    db.session.commit()


    return jsonify({
        "success": True,
        "message": "Notification marked as read.",
        "data": notification.to_dict()
    }), 200

@bp.patch("/read-all")
@jwt_required()
def mark_all_notifications_read():

    identity = get_jwt_identity()

    try:
        user_id = int(identity)

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid login session"
        }), 401


    user = db.session.get(
        User,
        user_id
    )


    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404


    if not user.is_active:
        return jsonify({
            "success": False,
            "message": "Account is inactive"
        }), 403


    notifications = (
        Notification.query
        .filter_by(
            user_id=user.id,
            is_read=False
        )
        .all()
    )


    updated_count = 0

    for notification in notifications:
        notification.is_read = True
        updated_count += 1


    db.session.commit()


    return jsonify({
        "success": True,
        "message": "All notifications marked as read.",
        "updated_count": updated_count
    }), 200    