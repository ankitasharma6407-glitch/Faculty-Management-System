from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Hod, LeaveRequest, Teacher, User


bp = Blueprint(
    "leave_requests",
    __name__,
    url_prefix="/api/leave-requests"
)


# ============================================================
# HELPERS
# ============================================================

def get_current_user():

    identity = get_jwt_identity()

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None

    return db.session.get(
        User,
        user_id
    )


def parse_date(value):

    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    except (TypeError, ValueError):
        return None


# ============================================================
# TEACHER - APPLY LEAVE
# POST /api/leave-requests
# ============================================================

@bp.post("")
@jwt_required()
def apply_leave():

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    if user.role != "teacher":
        return jsonify({
            "success": False,
            "message": "Only teachers can apply for leave"
        }), 403

    if not user.is_active:
        return jsonify({
            "success": False,
            "message": "Teacher account is inactive"
        }), 403

    teacher = Teacher.query.filter_by(
        user_id=user.id
    ).first()

    if not teacher:
        return jsonify({
            "success": False,
            "message": "Teacher profile not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    leave_type = str(
        data.get("leave_type", "")
    ).strip()

    reason = str(
        data.get("reason", "")
    ).strip()

    start_date = parse_date(
        data.get("start_date")
    )

    end_date = parse_date(
        data.get("end_date")
    )

    if not leave_type:
        return jsonify({
            "success": False,
            "message": "Leave type is required"
        }), 400

    if not start_date:
        return jsonify({
            "success": False,
            "message": "Valid start date is required"
        }), 400

    if not end_date:
        return jsonify({
            "success": False,
            "message": "Valid end date is required"
        }), 400

    if end_date < start_date:
        return jsonify({
            "success": False,
            "message": "End date cannot be before start date"
        }), 400

    if not reason:
        return jsonify({
            "success": False,
            "message": "Reason is required"
        }), 400

    leave = LeaveRequest(
        teacher_id=teacher.id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status="pending"
    )

    db.session.add(
        leave
    )

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Leave request submitted successfully",
        "data": leave.to_dict()
    }), 201


# ============================================================
# TEACHER - VIEW OWN LEAVES
# GET /api/leave-requests/me
# ============================================================

@bp.get("/me")
@jwt_required()
def get_my_leave_requests():

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    if user.role != "teacher":
        return jsonify({
            "success": False,
            "message": "Only teachers can view this resource"
        }), 403

    teacher = Teacher.query.filter_by(
        user_id=user.id
    ).first()

    if not teacher:
        return jsonify({
            "success": False,
            "message": "Teacher profile not found"
        }), 404

    leaves = (
        LeaveRequest.query
        .filter_by(
            teacher_id=teacher.id
        )
        .order_by(
            LeaveRequest.created_at.desc()
        )
        .all()
    )

    return jsonify({
        "success": True,
        "data": [
            leave.to_dict()
            for leave in leaves
        ]
    }), 200


# ============================================================
# HOD - VIEW OWN DEPARTMENT LEAVE REQUESTS
# GET /api/leave-requests/hod
#
# Optional:
# /api/leave-requests/hod?status=pending
# ============================================================

@bp.get("/hod")
@jwt_required()
def get_hod_leave_requests():

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    if user.role != "hod":
        return jsonify({
            "success": False,
            "message": "Only HOD can access this resource"
        }), 403

    if not user.is_active:
        return jsonify({
            "success": False,
            "message": "HOD account is inactive"
        }), 403

    hod = Hod.query.filter_by(
        user_id=user.id
    ).first()

    if not hod:
        return jsonify({
            "success": False,
            "message": "HOD profile not found"
        }), 404

    if not hod.department_id:
        return jsonify({
            "success": True,
            "department_id": None,
            "department": None,
            "summary": {
                "total": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0
            },
            "data": []
        }), 200

    requested_status = request.args.get(
        "status",
        ""
    ).strip().lower()

    allowed_statuses = {
        "pending",
        "approved",
        "rejected"
    }

    if (
        requested_status
        and requested_status not in allowed_statuses
    ):
        return jsonify({
            "success": False,
            "message": "Invalid leave status"
        }), 400

    base_query = (
        LeaveRequest.query
        .join(
            Teacher,
            LeaveRequest.teacher_id == Teacher.id
        )
        .filter(
            Teacher.department_id == hod.department_id
        )
    )

    query = base_query

    if requested_status:
        query = query.filter(
            LeaveRequest.status == requested_status
        )

    leaves = (
        query
        .order_by(
            LeaveRequest.created_at.desc()
        )
        .all()
    )

    all_department_leaves = (
        base_query
        .all()
    )

    summary = {
        "total": len(all_department_leaves),

        "pending": sum(
            1
            for leave in all_department_leaves
            if leave.status == "pending"
        ),

        "approved": sum(
            1
            for leave in all_department_leaves
            if leave.status == "approved"
        ),

        "rejected": sum(
            1
            for leave in all_department_leaves
            if leave.status == "rejected"
        )
    }

    return jsonify({
        "success": True,

        "department_id":
            hod.department_id,

        "department": (
            hod.department.name
            if hod.department
            else None
        ),

        "summary":
            summary,

        "data": [
            leave.to_dict()
            for leave in leaves
        ]
    }), 200


# ============================================================
# HOD - APPROVE / REJECT
# PATCH /api/leave-requests/<leave_id>/status
# ============================================================

@bp.patch("/<int:leave_id>/status")
@jwt_required()
def update_leave_status(leave_id):

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    if user.role != "hod":
        return jsonify({
            "success": False,
            "message": "Only HOD can update leave requests"
        }), 403

    hod = Hod.query.filter_by(
        user_id=user.id
    ).first()

    if not hod:
        return jsonify({
            "success": False,
            "message": "HOD profile not found"
        }), 404

    leave = db.session.get(
        LeaveRequest,
        leave_id
    )

    if not leave:
        return jsonify({
            "success": False,
            "message": "Leave request not found"
        }), 404

    # HOD can only manage teachers
    # belonging to own department.
    if (
        not leave.teacher
        or leave.teacher.department_id
        != hod.department_id
    ):
        return jsonify({
            "success": False,
            "message":
                "You cannot manage leave requests from another department"
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    new_status = str(
        data.get("status", "")
    ).strip().lower()

    if new_status not in {
        "approved",
        "rejected"
    }:
        return jsonify({
            "success": False,
            "message": "Status must be approved or rejected"
        }), 400

    remarks = str(
        data.get("hod_remarks", "")
    ).strip()

    leave.status = new_status

    leave.hod_remarks = (
        remarks
        if remarks
        else None
    )

    leave.reviewed_by = user.id
    leave.reviewed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,

        "message": (
            "Leave request approved successfully"
            if new_status == "approved"
            else "Leave request rejected successfully"
        ),

        "data":
            leave.to_dict()
    }), 200