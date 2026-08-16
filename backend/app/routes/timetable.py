from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import (
    User,
    Hod,
    Teacher,
    Subject,
    Timetable,
)


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "timetable",
    __name__,
    url_prefix="/api/hod/timetable"
)


# ============================================================
# GET HOD DEPARTMENT TIMETABLE
# ============================================================

@bp.get("")
@jwt_required()
def get_hod_timetable():

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


    if (
        str(user.role or "")
        .strip()
        .lower()
        != "hod"
    ):
        return jsonify({
            "success": False,
            "message": "HOD access required"
        }), 403


    hod = (
        Hod.query
        .filter_by(
            user_id=user.id
        )
        .first()
    )


    if not hod:
        return jsonify({
            "success": False,
            "message": "HOD profile not found"
        }), 404


    if not hod.department_id:
        return jsonify({
            "success": False,
            "message": "HOD department is not assigned"
        }), 400


    # ========================================================
    # FILTERS
    # ========================================================

    semester = str(
        request.args.get(
            "semester",
            ""
        ) or ""
    ).strip()


    section = str(
        request.args.get(
            "section",
            ""
        ) or ""
    ).strip()


    class_type = str(
        request.args.get(
            "class_type",
            ""
        ) or ""
    ).strip().lower()


    day = str(
        request.args.get(
            "day",
            ""
        ) or ""
    ).strip()


    query = Timetable.query.filter(
        Timetable.department_id ==
        hod.department_id
    )


    if semester and semester != "all":
        query = query.filter(
            Timetable.semester == semester
        )


    if section and section.lower() != "all":
        query = query.filter(
            Timetable.section == section
        )


    if class_type and class_type != "all":
        query = query.filter(
            Timetable.class_type == class_type
        )


    if day and day.lower() != "all":
        query = query.filter(
            Timetable.day_of_week == day
        )


    records = (
        query
        .order_by(
            Timetable.id.asc()
        )
        .all()
    )


    return jsonify({
        "success": True,

        "summary": {
            "total": len(records),
            "department_id": hod.department_id,
            "department": (
                hod.department.name
                if hod.department
                else None
            )
        },

        "data": [
            record.to_dict()
            for record in records
        ]
    }), 200

# ============================================================
# POST - ADD TIMETABLE CLASS
# ============================================================

@bp.post("")
@jwt_required()
def create_hod_timetable():

    identity = get_jwt_identity()

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid login session"
        }), 401


    # ========================================================
    # CURRENT USER
    # ========================================================

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


    if str(user.role or "").strip().lower() != "hod":
        return jsonify({
            "success": False,
            "message": "HOD access required"
        }), 403


    # ========================================================
    # HOD PROFILE
    # ========================================================

    hod = (
        Hod.query
        .filter_by(
            user_id=user.id
        )
        .first()
    )

    if not hod:
        return jsonify({
            "success": False,
            "message": "HOD profile not found"
        }), 404


    if not hod.department_id:
        return jsonify({
            "success": False,
            "message": "HOD department is not assigned"
        }), 400


    # ========================================================
    # REQUEST DATA
    # ========================================================

    data = request.get_json(
        silent=True
    ) or {}


    subject_name = str(
        data.get("subject_name") or ""
    ).strip()


    subject_code = str(
        data.get("subject_code") or ""
    ).strip().upper()


    semester = str(
        data.get("semester") or ""
    ).strip()


    section = str(
        data.get("section") or ""
    ).strip().upper()


    class_type = str(
        data.get("class_type") or ""
    ).strip().lower()


    day_of_week = str(
        data.get("day_of_week") or ""
    ).strip().title()


    start_time_value = str(
        data.get("start_time") or ""
    ).strip()


    end_time_value = str(
        data.get("end_time") or ""
    ).strip()


    room = str(
        data.get("room") or ""
    ).strip()


    teacher_id = data.get(
        "teacher_id"
    )


    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    if not all([
        subject_name,
        subject_code,
        semester,
        section,
        class_type,
        day_of_week,
        start_time_value,
        end_time_value,
        room,
        teacher_id
    ]):

        return jsonify({
            "success": False,
            "message": "All timetable fields are required"
        }), 400


    # ========================================================
    # TEACHER ID
    # ========================================================

    try:
        teacher_id = int(
            teacher_id
        )
    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "teacher_id must be an integer"
        }), 400


    # ========================================================
    # SEMESTER VALIDATION
    # ========================================================

    if semester not in {
        "1", "2", "3", "4",
        "5", "6", "7", "8"
    }:

        return jsonify({
            "success": False,
            "message": "Semester must be between 1 and 8"
        }), 400


    # ========================================================
    # SECTION VALIDATION
    # ========================================================

    if section not in {
        "A",
        "B",
        "C"
    }:

        return jsonify({
            "success": False,
            "message": "Section must be A, B or C"
        }), 400


    # ========================================================
    # CLASS TYPE VALIDATION
    # ========================================================

    allowed_types = {
        "lecture",
        "lab",
        "tutorial",
        "seminar"
    }

    if class_type not in allowed_types:

        return jsonify({
            "success": False,
            "message": (
                "Class type must be lecture, lab, "
                "tutorial or seminar"
            )
        }), 400


    # ========================================================
    # DAY VALIDATION
    # ========================================================

    allowed_days = {
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    }

    if day_of_week not in allowed_days:

        return jsonify({
            "success": False,
            "message": "Invalid timetable day"
        }), 400


    # ========================================================
    # TIME VALIDATION
    # ========================================================

    try:

        start_time = datetime.strptime(
            start_time_value,
            "%H:%M"
        ).time()

        end_time = datetime.strptime(
            end_time_value,
            "%H:%M"
        ).time()

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Time must use HH:MM format"
        }), 400


    if end_time <= start_time:

        return jsonify({
            "success": False,
            "message": "End time must be after start time"
        }), 400


    # ========================================================
    # TEACHER MUST BELONG TO HOD DEPARTMENT
    # ========================================================

    teacher = (
        Teacher.query
        .filter(
            Teacher.id == teacher_id,
            Teacher.department_id == hod.department_id
        )
        .first()
    )

    if not teacher:

        return jsonify({
            "success": False,
            "message": (
                "Teacher not found in your department"
            )
        }), 404


    # ========================================================
    # SUBJECT
    #
    # If subject code already exists -> reuse it.
    # If it does not exist -> create subject automatically.
    # ========================================================

    subject = (
        Subject.query
        .filter(
            Subject.code == subject_code
        )
        .first()
    )


    if subject:

        if (
            subject.department_id
            and subject.department_id
            != hod.department_id
        ):

            return jsonify({
                "success": False,
                "message": (
                    "This subject code belongs to "
                    "another department"
                )
            }), 409

    else:

        subject = Subject(
            name=subject_name,
            code=subject_code,
            department_id=hod.department_id,
            semester=semester,
            teacher_id=teacher.id
        )

        db.session.add(
            subject
        )

        db.session.flush()


    # ========================================================
    # TEACHER TIME CONFLICT
    # ========================================================

    teacher_conflict = (
        Timetable.query
        .filter(
            Timetable.teacher_id == teacher.id,
            Timetable.day_of_week == day_of_week,
            Timetable.start_time < end_time,
            Timetable.end_time > start_time
        )
        .first()
    )


    if teacher_conflict:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                "This teacher already has a class "
                "during this time"
            )
        }), 409


    # ========================================================
    # ROOM TIME CONFLICT
    # ========================================================

    room_conflict = (
        Timetable.query
        .filter(
            Timetable.department_id == hod.department_id,
            db.func.lower(
                Timetable.room
            ) == room.lower(),
            Timetable.day_of_week == day_of_week,
            Timetable.start_time < end_time,
            Timetable.end_time > start_time
        )
        .first()
    )


    if room_conflict:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                "This room is already occupied "
                "during this time"
            )
        }), 409


    # ========================================================
    # SEMESTER + SECTION CONFLICT
    # ========================================================

    class_conflict = (
        Timetable.query
        .filter(
            Timetable.department_id == hod.department_id,
            Timetable.semester == semester,
            Timetable.section == section,
            Timetable.day_of_week == day_of_week,
            Timetable.start_time < end_time,
            Timetable.end_time > start_time
        )
        .first()
    )


    if class_conflict:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                "This semester and section already "
                "has another class at this time"
            )
        }), 409


    # ========================================================
    # CREATE TIMETABLE RECORD
    # ========================================================

    timetable = Timetable(
        department_id=hod.department_id,
        subject_id=subject.id,
        teacher_id=teacher.id,
        semester=semester,
        section=section,
        class_type=class_type,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room=room,
        created_by=user.id
    )


    db.session.add(
        timetable
    )

    db.session.commit()


    return jsonify({
        "success": True,
        "message": "Class added to timetable successfully",
        "data": timetable.to_dict()
    }), 201


# ============================================================
# DELETE TIMETABLE CLASS
# ============================================================

@bp.delete("/<int:timetable_id>")
@jwt_required()
def delete_hod_timetable(timetable_id):

    identity = get_jwt_identity()

    try:
        user_id = int(identity)

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid login session"
        }), 401


    # ========================================================
    # CURRENT USER
    # ========================================================

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


    if str(user.role or "").strip().lower() != "hod":
        return jsonify({
            "success": False,
            "message": "HOD access required"
        }), 403


    # ========================================================
    # HOD PROFILE
    # ========================================================

    hod = (
        Hod.query
        .filter_by(
            user_id=user.id
        )
        .first()
    )

    if not hod:
        return jsonify({
            "success": False,
            "message": "HOD profile not found"
        }), 404


    if not hod.department_id:
        return jsonify({
            "success": False,
            "message": "HOD department is not assigned"
        }), 400


    # ========================================================
    # FIND CLASS ONLY INSIDE HOD DEPARTMENT
    # ========================================================

    timetable = (
        Timetable.query
        .filter(
            Timetable.id == timetable_id,
            Timetable.department_id == hod.department_id
        )
        .first()
    )


    if not timetable:
        return jsonify({
            "success": False,
            "message": "Timetable class not found"
        }), 404


    deleted_data = timetable.to_dict()


    # ========================================================
    # DELETE
    # ========================================================

    db.session.delete(
        timetable
    )

    db.session.commit()


    return jsonify({
        "success": True,
        "message": "Timetable class deleted successfully",
        "data": deleted_data
    }), 200