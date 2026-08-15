from flask import Blueprint, jsonify, request

from ..models import AuditLog, User


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "audit_logs",
    __name__,
    url_prefix="/api/audit-logs"
)


# ============================================================
# GET AUDIT LOGS
# ============================================================

@bp.get("")
def get_audit_logs():

    try:

        limit = request.args.get(
            "limit",
            default=10,
            type=int
        )

        if limit < 1:
            limit = 10

        if limit > 50:
            limit = 50


        logs = (
            AuditLog.query
            .filter(
                AuditLog.entity.in_([
                    "teacher",
                    "hod",
                    "student",
                    "recruiter"
                ]),
                AuditLog.action.in_([
                    "CREATE",
                    "UPDATE",
                    "DELETE"
                ])
            )
            .order_by(
                AuditLog.created_at.desc(),
                AuditLog.id.desc()
            )
            .limit(limit)
            .all()
        )


        data = []


        for log in logs:

            actor = "Admin"


            if log.user_id:

                user = User.query.get(
                    log.user_id
                )

                if user:

                    actor = (
                        user.username
                        or user.role
                        or "User"
                    )


            item = log.to_dict()

            item["actor"] = actor

            data.append(item)


        return jsonify({
            "success": True,
            "data": data
        })


    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500