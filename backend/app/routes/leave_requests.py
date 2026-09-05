import os
from datetime import date, datetime
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import Hod, LeaveRequest, Notification, Teacher, User


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


def leave_days(start_date, end_date):

    return (
        end_date - start_date
    ).days + 1


ALLOWED_DOCUMENT_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png"
}

MAX_DOCUMENT_SIZE = 5 * 1024 * 1024


def get_document_extension(filename):

    if not filename or "." not in filename:
        return ""

    return filename.rsplit(
        ".",
        1
    )[1].lower()


def document_size(document):

    document.stream.seek(
        0,
        os.SEEK_END
    )

    size = document.stream.tell()

    document.stream.seek(0)

    return size


def save_leave_document(document):

    safe_name = secure_filename(
        document.filename
    )

    stored_name = (
        f"{uuid4().hex}_{safe_name}"
    )

    relative_path = os.path.join(
        "leave_documents",
        stored_name
    )

    absolute_directory = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        "leave_documents"
    )

    os.makedirs(
        absolute_directory,
        exist_ok=True
    )

    document.save(
        os.path.join(
            absolute_directory,
            stored_name
        )
    )

    return relative_path.replace(
        os.sep,
        "/"
    )


def notify_department_hods_about_leave(
    teacher,
    leave_type,
    start_date,
    end_date
):

    if not teacher.department_id:
        return 0

    hod_profiles = (
        Hod.query
        .filter_by(
            department_id=teacher.department_id
        )
        .all()
    )

    notification_count = 0

    for hod_profile in hod_profiles:
        hod_user = db.session.get(
            User,
            hod_profile.user_id
        )

        if not hod_user or not hod_user.is_active:
            continue

        notification = Notification(
            user_id=hod_user.id,
            title="New Teacher Leave Request",
            message=(
                f"{teacher.full_name} submitted a {leave_type} request "
                f"from {start_date.strftime('%d %b %Y')} "
                f"to {end_date.strftime('%d %b %Y')}."
            ),
            category="leave",
            link="/pages/hod/leave-requests.html",
            is_read=False
        )

        db.session.add(notification)
        notification_count += 1

    return notification_count


def notify_teacher_about_leave_status(leave):

    teacher = leave.teacher

    if not teacher or not teacher.user_id:
        return None

    teacher_user = db.session.get(
        User,
        teacher.user_id
    )

    if not teacher_user or not teacher_user.is_active:
        return None

    status_text = str(
        leave.status or ""
    ).strip().lower()

    title = (
        "Leave Request Approved"
        if status_text == "approved"
        else "Leave Request Rejected"
    )

    message = (
        f"Your {leave.leave_type} request from "
        f"{leave.start_date.strftime('%d %b %Y')} to "
        f"{leave.end_date.strftime('%d %b %Y')} was {status_text}."
    )

    if leave.hod_remarks:
        message += f" HOD remarks: {leave.hod_remarks}"

    notification = Notification(
        user_id=teacher_user.id,
        title=title,
        message=message,
        category="leave",
        link="/pages/teacher/leave-request.html",
        is_read=False
    )

    db.session.add(notification)
    return notification


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

    if request.files or request.form:
        data = request.form
    else:
        data = request.get_json(
            silent=True
        ) or {}

    leave_type = str(
        data.get("leave_type", "")
    ).strip()

    reason = str(
        data.get("reason", "")
    ).strip()

    contact_number = str(
        data.get("contact_number", "")
    ).strip()

    alternate_email = str(
        data.get("alternate_email", "")
    ).strip()

    responsibility_note = str(
        data.get("responsibility_note", "")
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

    if start_date < date.today():
        return jsonify({
            "success": False,
            "message": "Leave start date cannot be in the past"
        }), 400

    if not reason:
        return jsonify({
            "success": False,
            "message": "Reason is required"
        }), 400

    if len(reason) > 500:
        return jsonify({
            "success": False,
            "message": "Reason cannot exceed 500 characters"
        }), 400

    if len(contact_number) > 30:
        return jsonify({
            "success": False,
            "message": "Contact number is too long"
        }), 400

    if alternate_email and (
        "@" not in alternate_email
        or len(alternate_email) > 255
    ):
        return jsonify({
            "success": False,
            "message": "Enter a valid alternate email"
        }), 400

    overlapping_leave = (
        LeaveRequest.query
        .filter(
            LeaveRequest.teacher_id == teacher.id,
            LeaveRequest.status.in_([
                "pending",
                "approved"
            ]),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date
        )
        .first()
    )

    if overlapping_leave:
        return jsonify({
            "success": False,
            "message": (
                "A pending or approved leave request "
                "already exists for these dates"
            )
        }), 409

    document = request.files.get(
        "supporting_document"
    )

    supporting_document = None

    if document and document.filename:
        extension = get_document_extension(
            document.filename
        )

        if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
            return jsonify({
                "success": False,
                "message": "Only PDF, JPG, JPEG and PNG documents are allowed"
            }), 400

        if document_size(document) > MAX_DOCUMENT_SIZE:
            return jsonify({
                "success": False,
                "message": "Supporting document must be 5 MB or smaller"
            }), 400

        supporting_document = save_leave_document(
            document
        )

    leave = LeaveRequest(
        teacher_id=teacher.id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        contact_number=(
            contact_number or None
        ),
        alternate_email=(
            alternate_email or None
        ),
        responsibility_note=(
            responsibility_note or None
        ),
        supporting_document=supporting_document,
        status="pending"
    )

    db.session.add(
        leave
    )

    notify_department_hods_about_leave(
        teacher,
        leave_type,
        start_date,
        end_date
    )

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()

        if supporting_document:
            saved_file = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                supporting_document
            )

            if os.path.isfile(saved_file):
                os.remove(saved_file)

        raise

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

    approved_requests = sum(
        1 for leave in leaves
        if leave.status == "approved"
    )

    rejected_requests = sum(
        1 for leave in leaves
        if leave.status == "rejected"
    )

    pending_requests = sum(
        1 for leave in leaves
        if leave.status == "pending"
    )

    cancelled_requests = sum(
        1 for leave in leaves
        if leave.status == "cancelled"
    )

    approved_days = sum(
        leave_days(
            leave.start_date,
            leave.end_date
        )
        for leave in leaves
        if leave.status == "approved"
    )

    return jsonify({
        "success": True,
        "summary": {
            "total_requests": len(leaves),
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "pending_requests": pending_requests,
            "cancelled_requests": cancelled_requests,
            "approved_days": approved_days
        },
        "data": [
            leave.to_dict()
            for leave in leaves
        ]
    }), 200


# ============================================================
# TEACHER - CANCEL OWN PENDING LEAVE
# PATCH /api/leave-requests/<leave_id>/cancel
# ============================================================

@bp.patch("/<int:leave_id>/cancel")
@jwt_required()
def cancel_my_leave_request(leave_id):

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    if user.role != "teacher":
        return jsonify({
            "success": False,
            "message": "Only teachers can cancel leave requests"
        }), 403

    teacher = Teacher.query.filter_by(
        user_id=user.id
    ).first()

    if not teacher:
        return jsonify({
            "success": False,
            "message": "Teacher profile not found"
        }), 404

    leave = db.session.get(
        LeaveRequest,
        leave_id
    )

    if not leave or leave.teacher_id != teacher.id:
        return jsonify({
            "success": False,
            "message": "Leave request not found"
        }), 404

    if leave.status != "pending":
        return jsonify({
            "success": False,
            "message": "Only pending leave requests can be cancelled"
        }), 409

    leave.status = "cancelled"
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Leave request cancelled successfully",
        "data": leave.to_dict()
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
        "rejected",
        "cancelled"
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
        ),

        "cancelled": sum(
            1
            for leave in all_department_leaves
            if leave.status == "cancelled"
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

    if leave.status != "pending":
        return jsonify({
            "success": False,
            "message": "Only pending leave requests can be reviewed"
        }), 409

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

    notify_teacher_about_leave_status(
        leave
    )

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
