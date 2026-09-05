from datetime import datetime, timedelta
import math

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import func, or_

from ..extensions import db
from ..models import (
    AcademicEvent,
    FacultyAttendance,
    FaceEncoding,
    Hod,
    LeaveRequest,
    Teacher,
    User,
)


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "faculty_attendance_api",
    __name__,
    url_prefix="/api/faculty-attendance"
)


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_ATTENDANCE_STATUS = {
    "present",
    "absent",
    "leave",
}


FACE_MATCH_THRESHOLD = 0.55


def normalize_face_descriptor(descriptor):

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


def calculate_face_distance(
    descriptor_one,
    descriptor_two
):

    if (
        descriptor_one is None
        or descriptor_two is None
        or len(descriptor_one) != len(descriptor_two)
    ):
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


def calculate_face_similarity(
    descriptor_one,
    descriptor_two
):

    if (
        descriptor_one is None
        or descriptor_two is None
        or len(descriptor_one) != len(descriptor_two)
    ):
        return None

    dot_product = sum(
        first * second
        for first, second in zip(
            descriptor_one,
            descriptor_two
        )
    )

    first_norm = math.sqrt(
        sum(value ** 2 for value in descriptor_one)
    )

    second_norm = math.sqrt(
        sum(value ** 2 for value in descriptor_two)
    )

    if first_norm == 0 or second_norm == 0:
        return None

    cosine_similarity = (
        dot_product /
        (first_norm * second_norm)
    )

    return round(
        max(0.0, min(100.0, cosine_similarity * 100.0)),
        1
    )


# ============================================================
# HELPER - DATE PARSING
# ============================================================

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
# HELPER - WORKING DAYS AND AUTOMATIC MISSING ATTENDANCE
# ============================================================

def get_non_working_reason(
    attendance_date,
    department_id=None
):

    # Sunday is a weekly holiday. Saturday remains a working day.
    if attendance_date.weekday() == 6:
        return "Sunday"

    department_filter = AcademicEvent.department_id.is_(None)

    if department_id is not None:
        department_filter = or_(
            AcademicEvent.department_id.is_(None),
            AcademicEvent.department_id == department_id
        )

    holiday = (
        AcademicEvent.query
        .filter(
            AcademicEvent.start_date <= attendance_date,
            or_(
                AcademicEvent.end_date.is_(None),
                AcademicEvent.end_date >= attendance_date
            ),
            department_filter,
            or_(
                func.lower(AcademicEvent.event_type).in_([
                    "holiday",
                    "vacation",
                    "college_closed",
                    "college closed",
                ]),
                func.lower(AcademicEvent.title).like("%holiday%")
            )
        )
        .order_by(AcademicEvent.id.desc())
        .first()
    )

    return holiday.title if holiday else None


def get_working_dates(
    start_date,
    end_date,
    department_id
):

    if not start_date or not end_date or start_date > end_date:
        return []

    working_dates = []
    current_date = start_date

    while current_date <= end_date:
        if not get_non_working_reason(
            current_date,
            department_id
        ):
            working_dates.append(current_date)

        current_date += timedelta(days=1)

    return working_dates


def get_individual_attendance_data(
    faculty_user_id,
    department_id,
    teacher_id=None,
    faculty_start_date=None,
    history_limit=30
):

    today = datetime.now().date()

    all_records = (
        FacultyAttendance.query
        .filter_by(faculty_user_id=faculty_user_id)
        .order_by(FacultyAttendance.date.asc())
        .all()
    )

    record_by_date = {
        record.date: record
        for record in all_records
        if record.date
    }

    calculation_start = faculty_start_date

    if all_records:
        first_record_date = all_records[0].date

        if (
            calculation_start is None
            or first_record_date < calculation_start
        ):
            calculation_start = first_record_date

    if calculation_start is None:
        return {
            "summary": {
                "total_records": 0,
                "recorded_records": len(all_records),
                "working_days": 0,
                "present": 0,
                "absent": 0,
                "leave": 0,
                "inferred_absent": 0,
                "attendance_percentage": 0.0,
            },
            "records": [],
        }

    approved_leave_by_date = {}

    if teacher_id is not None:
        approved_leaves = (
            LeaveRequest.query
            .filter(
                LeaveRequest.teacher_id == teacher_id,
                func.lower(LeaveRequest.status) == "approved",
                LeaveRequest.end_date >= calculation_start,
                LeaveRequest.start_date <= today
            )
            .all()
        )

        for leave in approved_leaves:
            leave_date = leave.start_date
            while leave_date <= leave.end_date and leave_date <= today:
                approved_leave_by_date[leave_date] = leave
                leave_date += timedelta(days=1)

    include_today = (
        today in record_by_date
        or today in approved_leave_by_date
    )
    calculation_end = (
        today
        if include_today
        else today - timedelta(days=1)
    )
    working_dates = get_working_dates(
        calculation_start,
        calculation_end,
        department_id
    )

    present = 0
    absent = 0
    leave = 0
    inferred_absent = 0
    history = []

    for working_date in working_dates:
        record = record_by_date.get(working_date)

        if record:
            item = record.to_dict()
            item["inferred"] = False
            status = str(record.status or "").lower()
        elif working_date in approved_leave_by_date:
            approved_leave = approved_leave_by_date[working_date]
            status = "leave"
            item = {
                "id": None,
                "faculty_user_id": faculty_user_id,
                "department_id": department_id,
                "date": working_date.isoformat(),
                "status": "leave",
                "remarks": f"Approved {approved_leave.leave_type}",
                "marked_by": approved_leave.reviewed_by,
                "created_at": None,
                "updated_at": None,
                "inferred": True,
            }
        else:
            status = "absent"
            inferred_absent += 1
            item = {
                "id": None,
                "faculty_user_id": faculty_user_id,
                "department_id": department_id,
                "date": working_date.isoformat(),
                "status": "absent",
                "remarks": "Attendance not marked",
                "marked_by": None,
                "created_at": None,
                "updated_at": None,
                "inferred": True,
            }

        if status == "present":
            present += 1
        elif status == "leave":
            leave += 1
        else:
            absent += 1

        history.append(item)

    total_working_days = len(working_dates)
    attendance_percentage = (
        round((present / total_working_days) * 100, 1)
        if total_working_days
        else 0.0
    )

    history.sort(
        key=lambda item: item.get("date") or "",
        reverse=True
    )

    return {
        "summary": {
            "total_records": total_working_days,
            "recorded_records": len(all_records),
            "working_days": total_working_days,
            "present": present,
            "absent": absent,
            "leave": leave,
            "inferred_absent": inferred_absent,
            "attendance_percentage": attendance_percentage,
        },
        "records": (
            history[:history_limit]
            if history_limit is not None
            else history
        ),
    }


def get_department_daily_summary(
    department_id,
    attendance_date
):

    non_working_reason = get_non_working_reason(
        attendance_date,
        department_id
    )

    if non_working_reason:
        return {
            "date": attendance_date.isoformat(),
            "working_day": False,
            "non_working_reason": non_working_reason,
            "total_active_teachers": 0,
            "present": 0,
            "absent": 0,
            "leave": 0,
            "unmarked": 0,
            "attendance_percentage": 0.0,
        }

    teachers = (
        Teacher.query
        .join(User, Teacher.user_id == User.id)
        .filter(
            Teacher.department_id == department_id,
            func.lower(Teacher.status) == "active",
            User.is_active.is_(True),
            func.lower(User.role) == "teacher"
        )
        .all()
    )

    teachers = [
        teacher
        for teacher in teachers
        if not teacher.joining_date
        or teacher.joining_date <= attendance_date
    ]
    teacher_user_ids = [teacher.user_id for teacher in teachers]

    record_by_user = {}
    if teacher_user_ids:
        record_by_user = {
            record.faculty_user_id: record
            for record in FacultyAttendance.query.filter(
                FacultyAttendance.date == attendance_date,
                FacultyAttendance.faculty_user_id.in_(teacher_user_ids)
            ).all()
        }

    approved_leave_teacher_ids = set()
    if teachers:
        approved_leave_teacher_ids = {
            leave.teacher_id
            for leave in LeaveRequest.query.filter(
                LeaveRequest.teacher_id.in_([
                    teacher.id for teacher in teachers
                ]),
                func.lower(LeaveRequest.status) == "approved",
                LeaveRequest.start_date <= attendance_date,
                LeaveRequest.end_date >= attendance_date
            ).all()
        }

    present = 0
    stored_absent = 0
    leave = 0
    unmarked = 0

    for teacher in teachers:
        record = record_by_user.get(teacher.user_id)

        if record:
            status = str(record.status or "").lower()
        elif teacher.id in approved_leave_teacher_ids:
            status = "leave"
        else:
            status = "unmarked"

        if status == "present":
            present += 1
        elif status == "leave":
            leave += 1
        elif status == "absent":
            stored_absent += 1
        else:
            unmarked += 1

    total_teachers = len(teachers)

    return {
        "date": attendance_date.isoformat(),
        "working_day": True,
        "non_working_reason": None,
        "total_active_teachers": total_teachers,
        "present": present,
        "absent": stored_absent + unmarked,
        "stored_absent": stored_absent,
        "leave": leave,
        "unmarked": unmarked,
        "attendance_percentage": (
            round((present / total_teachers) * 100, 1)
            if total_teachers
            else 0.0
        ),
    }


def get_all_teachers_daily_data(
    attendance_date,
    department_id=None
):

    teachers_query = (
        Teacher.query
        .join(User, Teacher.user_id == User.id)
        .filter(
            func.lower(Teacher.status) == "active",
            User.is_active.is_(True),
            func.lower(User.role) == "teacher"
        )
    )

    if department_id is not None:
        teachers_query = teachers_query.filter(
            Teacher.department_id == department_id
        )

    registered_teachers = [
        teacher
        for teacher in teachers_query.all()
        if (
            not teacher.joining_date
            or teacher.joining_date <= attendance_date
        )
    ]

    working_teachers = []
    non_working_teachers = []

    for teacher in registered_teachers:
        reason = get_non_working_reason(
            attendance_date,
            teacher.department_id
        )

        if reason:
            non_working_teachers.append((teacher, reason))
        else:
            working_teachers.append(teacher)

    teacher_user_ids = [
        teacher.user_id
        for teacher in working_teachers
    ]

    record_by_user = {}

    if teacher_user_ids:
        record_by_user = {
            record.faculty_user_id: record
            for record in FacultyAttendance.query.filter(
                FacultyAttendance.date == attendance_date,
                FacultyAttendance.faculty_user_id.in_(
                    teacher_user_ids
                )
            ).all()
        }

    approved_leave_teacher_ids = set()

    if working_teachers:
        approved_leave_teacher_ids = {
            leave.teacher_id
            for leave in LeaveRequest.query.filter(
                LeaveRequest.teacher_id.in_([
                    teacher.id
                    for teacher in working_teachers
                ]),
                func.lower(LeaveRequest.status) == "approved",
                LeaveRequest.start_date <= attendance_date,
                LeaveRequest.end_date >= attendance_date
            ).all()
        }

    present = 0
    stored_absent = 0
    leave = 0
    unmarked = 0
    records = []

    for teacher in working_teachers:
        stored_record = record_by_user.get(teacher.user_id)

        if stored_record:
            status = str(
                stored_record.status or ""
            ).strip().lower()
            inferred = False
            remarks = stored_record.remarks
            attendance_id = stored_record.id
        elif teacher.id in approved_leave_teacher_ids:
            status = "leave"
            inferred = True
            remarks = "Approved leave"
            attendance_id = None
        else:
            status = "absent"
            inferred = True
            remarks = "Attendance not marked"
            attendance_id = None

        if status == "present":
            present += 1
        elif status == "leave":
            leave += 1
        elif stored_record:
            stored_absent += 1
        else:
            unmarked += 1

        records.append({
            "id": attendance_id,
            "teacher_id": teacher.id,
            "faculty_user_id": teacher.user_id,
            "faculty_code": teacher.teacher_code,
            "faculty_name": teacher.full_name,
            "designation": teacher.designation,
            "department_id": teacher.department_id,
            "department": (
                teacher.department.name
                if teacher.department
                else None
            ),
            "date": attendance_date.isoformat(),
            "status": status,
            "remarks": remarks,
            "inferred": inferred,
            "working_day": True,
            "non_working_reason": None,
        })

    for teacher, reason in non_working_teachers:
        records.append({
            "id": None,
            "teacher_id": teacher.id,
            "faculty_user_id": teacher.user_id,
            "faculty_code": teacher.teacher_code,
            "faculty_name": teacher.full_name,
            "designation": teacher.designation,
            "department_id": teacher.department_id,
            "department": (
                teacher.department.name
                if teacher.department
                else None
            ),
            "date": attendance_date.isoformat(),
            "status": "non_working",
            "remarks": reason,
            "inferred": True,
            "working_day": False,
            "non_working_reason": reason,
        })

    records.sort(
        key=lambda item: (
            str(item.get("department") or ""),
            str(item.get("faculty_name") or "")
        )
    )

    total_working_teachers = len(working_teachers)

    return {
        "summary": {
            "date": attendance_date.isoformat(),
            "working_day": total_working_teachers > 0,
            "total_registered_teachers": len(
                registered_teachers
            ),
            "total_active_teachers": total_working_teachers,
            "non_working_teachers": len(
                non_working_teachers
            ),
            "present": present,
            "absent": stored_absent + unmarked,
            "stored_absent": stored_absent,
            "leave": leave,
            "unmarked": unmarked,
            "attendance_percentage": (
                round(
                    (present / total_working_teachers) * 100,
                    1
                )
                if total_working_teachers
                else 0.0
            ),
        },
        "records": records,
    }


def get_all_hods_daily_summary(attendance_date):

    if attendance_date.weekday() == 6:
        return {
            "date": attendance_date.isoformat(),
            "working_day": False,
            "non_working_reason": "Sunday",
            "total_active_hods": 0,
            "present": 0,
            "absent": 0,
            "leave": 0,
            "unmarked": 0,
            "attendance_percentage": 0.0,
        }

    hods = (
        Hod.query
        .join(User, Hod.user_id == User.id)
        .filter(
            func.lower(Hod.status) == "active",
            Hod.department_id.isnot(None),
            User.is_active.is_(True),
            func.lower(User.role) == "hod"
        )
        .all()
    )

    eligible_hods = [
        hod
        for hod in hods
        if (
            (not hod.joining_date or hod.joining_date <= attendance_date)
            and not get_non_working_reason(
                attendance_date,
                hod.department_id
            )
        )
    ]
    hod_user_ids = [hod.user_id for hod in eligible_hods]

    record_by_user = {}
    if hod_user_ids:
        record_by_user = {
            record.faculty_user_id: record
            for record in FacultyAttendance.query.filter(
                FacultyAttendance.date == attendance_date,
                FacultyAttendance.faculty_user_id.in_(hod_user_ids)
            ).all()
        }

    present = 0
    stored_absent = 0
    leave = 0
    unmarked = 0

    for hod in eligible_hods:
        record = record_by_user.get(hod.user_id)
        status = (
            str(record.status or "").lower()
            if record
            else "unmarked"
        )

        if status == "present":
            present += 1
        elif status == "leave":
            leave += 1
        elif status == "absent":
            stored_absent += 1
        else:
            unmarked += 1

    total_hods = len(eligible_hods)

    return {
        "date": attendance_date.isoformat(),
        "working_day": True,
        "non_working_reason": None,
        "total_active_hods": total_hods,
        "present": present,
        "absent": stored_absent + unmarked,
        "stored_absent": stored_absent,
        "leave": leave,
        "unmarked": unmarked,
        "attendance_percentage": (
            round((present / total_hods) * 100, 1)
            if total_hods
            else 0.0
        ),
    }


# ============================================================
# HELPER - CURRENT ADMIN
# ============================================================

def get_current_admin():

    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None, (
            jsonify({
                "success": False,
                "message": "Invalid login session"
            }),
            401
        )

    user = db.session.get(User, user_id)

    if not user:
        return None, (
            jsonify({
                "success": False,
                "message": "User not found"
            }),
            404
        )

    if str(user.role or "").strip().lower() != "admin":
        return None, (
            jsonify({
                "success": False,
                "message": "Admin access required"
            }),
            403
        )

    if not user.is_active:
        return None, (
            jsonify({
                "success": False,
                "message": "Admin account is inactive"
            }),
            403
        )

    return user, None


# ============================================================
# HELPER - CURRENT HOD
# ============================================================

def get_current_hod():

    identity = get_jwt_identity()

    try:

        user_id = int(identity)

    except (TypeError, ValueError):

        return None, None, (
            jsonify({
                "success": False,
                "message": "Invalid login session"
            }),
            401
        )


    user = db.session.get(
        User,
        user_id
    )


    if not user:

        return None, None, (
            jsonify({
                "success": False,
                "message": "User not found"
            }),
            404
        )


    if (
        str(user.role or "")
        .strip()
        .lower()
        != "hod"
    ):

        return None, None, (
            jsonify({
                "success": False,
                "message": "HOD access required"
            }),
            403
        )


    if not user.is_active:

        return None, None, (
            jsonify({
                "success": False,
                "message": "HOD account is inactive"
            }),
            403
        )


    hod = (
        Hod.query
        .filter_by(
            user_id=user.id
        )
        .first()
    )


    if not hod:

        return None, None, (
            jsonify({
                "success": False,
                "message": "HOD profile not found"
            }),
            404
        )


    if not hod.department_id:

        return None, None, (
            jsonify({
                "success": False,
                "message": (
                    "No department is assigned "
                    "to this HOD"
                )
            }),
            403
        )


    return user, hod, None


# ============================================================
# HELPER - CURRENT TEACHER
# ============================================================

def get_current_teacher():

    identity = get_jwt_identity()

    try:
        user_id = int(identity)

    except (TypeError, ValueError):
        return None, None, (
            jsonify({
                "success": False,
                "message": "Invalid login session"
            }),
            401
        )

    user = db.session.get(User, user_id)

    if not user:
        return None, None, (
            jsonify({
                "success": False,
                "message": "User not found"
            }),
            404
        )

    if (
        str(user.role or "")
        .strip()
        .lower()
        != "teacher"
    ):
        return None, None, (
            jsonify({
                "success": False,
                "message": "Teacher access required"
            }),
            403
        )

    if not user.is_active:
        return None, None, (
            jsonify({
                "success": False,
                "message": "Teacher account is inactive"
            }),
            403
        )

    teacher = (
        Teacher.query
        .filter_by(user_id=user.id)
        .first()
    )

    if not teacher:
        return None, None, (
            jsonify({
                "success": False,
                "message": "Teacher profile not found"
            }),
            404
        )

    if not teacher.department_id:
        return None, None, (
            jsonify({
                "success": False,
                "message": (
                    "No department is assigned "
                    "to this teacher"
                )
            }),
            403
        )

    return user, teacher, None


# ============================================================
# ADMIN - CALCULATED FACULTY ATTENDANCE REPORT
#
# GET /api/faculty-attendance/admin/calculated-report
#
# Teachers and HODs use the same completed-working-day rules:
# stored attendance, approved teacher leave, automatic absence,
# Sunday/holiday exclusion and no automatic absence for today.
# The existing raw attendance endpoint remains unchanged.
# ============================================================

@bp.get("/admin/calculated-report")
@jwt_required()
def get_admin_calculated_attendance_report():

    try:
        admin_user, admin_error = get_current_admin()

        if admin_error:
            return admin_error

        role = request.args.get("role", "").strip().lower()
        status = request.args.get("status", "").strip().lower()
        department_value = request.args.get(
            "department_id",
            ""
        ).strip()
        search = request.args.get("search", "").strip().lower()

        exact_date_value = request.args.get("date", "").strip()
        from_date_value = request.args.get("from_date", "").strip()
        to_date_value = request.args.get("to_date", "").strip()

        if role and role not in {"teacher", "hod"}:
            return jsonify({
                "success": False,
                "message": "Role must be teacher or hod."
            }), 400

        if status and status not in ALLOWED_ATTENDANCE_STATUS:
            return jsonify({
                "success": False,
                "message": (
                    "Invalid attendance status. "
                    "Use present, absent or leave."
                )
            }), 400

        department_id = None

        if department_value:
            try:
                department_id = int(department_value)
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "department_id must be an integer."
                }), 400

        exact_date = (
            parse_date(exact_date_value)
            if exact_date_value
            else None
        )
        from_date = (
            parse_date(from_date_value)
            if from_date_value
            else None
        )
        to_date = (
            parse_date(to_date_value)
            if to_date_value
            else None
        )

        if exact_date_value and not exact_date:
            return jsonify({
                "success": False,
                "message": "Invalid date. Use YYYY-MM-DD."
            }), 400

        if from_date_value and not from_date:
            return jsonify({
                "success": False,
                "message": "Invalid from_date. Use YYYY-MM-DD."
            }), 400

        if to_date_value and not to_date:
            return jsonify({
                "success": False,
                "message": "Invalid to_date. Use YYYY-MM-DD."
            }), 400

        if from_date and to_date and from_date > to_date:
            return jsonify({
                "success": False,
                "message": "from_date cannot be after to_date."
            }), 400

        faculty_profiles = []

        if role in {"", "teacher"}:
            teacher_query = (
                Teacher.query
                .join(User, Teacher.user_id == User.id)
                .filter(
                    func.lower(Teacher.status) == "active",
                    User.is_active.is_(True),
                    func.lower(User.role) == "teacher"
                )
            )

            if department_id is not None:
                teacher_query = teacher_query.filter(
                    Teacher.department_id == department_id
                )

            faculty_profiles.extend([
                {
                    "profile": teacher,
                    "role": "teacher",
                    "code": teacher.teacher_code,
                    "teacher_id": teacher.id,
                    "designation": teacher.designation,
                }
                for teacher in teacher_query.all()
            ])

        if role in {"", "hod"}:
            hod_query = (
                Hod.query
                .join(User, Hod.user_id == User.id)
                .filter(
                    func.lower(Hod.status) == "active",
                    User.is_active.is_(True),
                    func.lower(User.role) == "hod"
                )
            )

            if department_id is not None:
                hod_query = hod_query.filter(
                    Hod.department_id == department_id
                )

            faculty_profiles.extend([
                {
                    "profile": hod,
                    "role": "hod",
                    "code": hod.hod_code,
                    "teacher_id": None,
                    "designation": "Head of Department",
                }
                for hod in hod_query.all()
            ])

        data = []

        for faculty in faculty_profiles:
            profile = faculty["profile"]

            calculated = get_individual_attendance_data(
                faculty_user_id=profile.user_id,
                department_id=profile.department_id,
                teacher_id=faculty["teacher_id"],
                faculty_start_date=profile.joining_date,
                history_limit=None
            )

            department_name = (
                profile.department.name
                if profile.department
                else None
            )

            for calculated_item in calculated["records"]:
                item = dict(calculated_item)
                item_date = parse_date(item.get("date"))

                if exact_date and item_date != exact_date:
                    continue

                if from_date and (
                    item_date is None
                    or item_date < from_date
                ):
                    continue

                if to_date and (
                    item_date is None
                    or item_date > to_date
                ):
                    continue

                item_status = str(
                    item.get("status") or ""
                ).strip().lower()

                if status and item_status != status:
                    continue

                item.update({
                    "faculty_user_id": profile.user_id,
                    "faculty_code": faculty["code"],
                    "faculty_name": profile.full_name,
                    "full_name": profile.full_name,
                    "role": faculty["role"],
                    "designation": faculty["designation"],
                    "department_id": profile.department_id,
                    "department": department_name,
                })

                if item.get("inferred"):
                    item["marked_by_name"] = "System"

                if search:
                    searchable_text = " ".join([
                        str(item.get("faculty_code") or ""),
                        str(item.get("faculty_name") or ""),
                        str(item.get("role") or ""),
                        str(item.get("department") or ""),
                        str(item.get("status") or "")
                    ]).lower()

                    if search not in searchable_text:
                        continue

                data.append(item)

        data.sort(
            key=lambda item: (
                str(item.get("date") or ""),
                str(item.get("faculty_name") or "")
            ),
            reverse=True
        )

        present_count = sum(
            1 for item in data
            if str(item.get("status") or "").lower()
            == "present"
        )
        absent_count = sum(
            1 for item in data
            if str(item.get("status") or "").lower()
            == "absent"
        )
        leave_count = sum(
            1 for item in data
            if str(item.get("status") or "").lower()
            == "leave"
        )
        total_count = len(data)

        return jsonify({
            "success": True,
            "data": data,
            "summary": {
                "total": total_count,
                "present": present_count,
                "absent": absent_count,
                "leave": leave_count,
                "inferred_absent": sum(
                    1 for item in data
                    if (
                        str(item.get("status") or "").lower()
                        == "absent"
                        and bool(item.get("inferred"))
                    )
                ),
                "attendance_percentage": (
                    round(
                        (present_count / total_count) * 100,
                        1
                    )
                    if total_count
                    else 0.0
                )
            }
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Unable to load calculated attendance.",
            "error": str(error)
        }), 500


# ============================================================
# GET ALL FACULTY ATTENDANCE
# ADMIN ATTENDANCE REPORT
# ============================================================

@bp.get("")
@jwt_required()
def get_faculty_attendance():

    try:

        admin_user, admin_error = get_current_admin()

        if admin_error:
            return admin_error

        # ----------------------------------------------------
        # FILTER VALUES
        # ----------------------------------------------------

        role = (
            request.args
            .get("role", "")
            .strip()
            .lower()
        )

        status = (
            request.args
            .get("status", "")
            .strip()
            .lower()
        )

        department_id = (
            request.args
            .get("department_id", "")
            .strip()
        )

        search = (
            request.args
            .get("search", "")
            .strip()
        )

        from_date_value = (
            request.args
            .get("from_date", "")
            .strip()
        )

        to_date_value = (
            request.args
            .get("to_date", "")
            .strip()
        )

        exact_date_value = (
            request.args
            .get("date", "")
            .strip()
        )


        # ----------------------------------------------------
        # BASE QUERY
        # ----------------------------------------------------

        query = FacultyAttendance.query


        # ----------------------------------------------------
        # STATUS FILTER
        # ----------------------------------------------------

        if status:

            if status not in (
                "present",
                "absent",
                "leave"
            ):

                return jsonify({
                    "success": False,
                    "message": (
                        "Invalid attendance status. "
                        "Use present, absent or leave."
                    )
                }), 400


            query = query.filter(
                FacultyAttendance.status
                == status
            )


        # ----------------------------------------------------
        # DEPARTMENT FILTER
        # ----------------------------------------------------

        if department_id:

            try:

                department_id = int(
                    department_id
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message": (
                        "department_id must be "
                        "an integer."
                    )
                }), 400


            query = query.filter(
                FacultyAttendance.department_id
                == department_id
            )


        # ----------------------------------------------------
        # DATE FILTER
        # ----------------------------------------------------

        from_date = parse_date(
            from_date_value
        )

        to_date = parse_date(
            to_date_value
        )

        exact_date = parse_date(
            exact_date_value
        )

        if (
            exact_date_value
            and not exact_date
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Invalid date. "
                    "Use YYYY-MM-DD."
                )
            }), 400


        if (
            from_date_value
            and not from_date
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Invalid from_date. "
                    "Use YYYY-MM-DD."
                )
            }), 400


        if (
            to_date_value
            and not to_date
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Invalid to_date. "
                    "Use YYYY-MM-DD."
                )
            }), 400


        if (
            from_date
            and to_date
            and from_date > to_date
        ):

            return jsonify({
                "success": False,
                "message": (
                    "from_date cannot be "
                    "after to_date."
                )
            }), 400


        if from_date:

            query = query.filter(
                FacultyAttendance.date
                >= from_date
            )


        if to_date:

            query = query.filter(
                FacultyAttendance.date
                <= to_date
            )

        if exact_date:

            query = query.filter(
                FacultyAttendance.date
                == exact_date
            )


        # ----------------------------------------------------
        # GET RECORDS
        # ----------------------------------------------------

        records = (
            query
            .order_by(
                FacultyAttendance.date.desc(),
                FacultyAttendance.id.desc()
            )
            .all()
        )


        data = []


        for attendance in records:

            item = attendance.to_dict()


            # ------------------------------------------------
            # ROLE FILTER
            # ------------------------------------------------

            if role:

                if role not in (
                    "teacher",
                    "hod"
                ):

                    return jsonify({
                        "success": False,
                        "message": (
                            "Role must be "
                            "teacher or hod."
                        )
                    }), 400


                if (
                    str(
                        item.get(
                            "role",
                            ""
                        )
                    ).lower()
                    != role
                ):

                    continue


            # ------------------------------------------------
            # SEARCH FILTER
            # Faculty name / code / department
            # ------------------------------------------------

            if search:

                search_value = (
                    search.lower()
                )


                searchable_text = " ".join([

                    str(
                        item.get(
                            "faculty_code",
                            ""
                        ) or ""
                    ),

                    str(
                        item.get(
                            "faculty_name",
                            ""
                        ) or ""
                    ),

                    str(
                        item.get(
                            "role",
                            ""
                        ) or ""
                    ),

                    str(
                        item.get(
                            "department",
                            ""
                        ) or ""
                    ),

                    str(
                        item.get(
                            "status",
                            ""
                        ) or ""
                    )

                ]).lower()


                if (
                    search_value
                    not in searchable_text
                ):

                    continue


            data.append(
                item
            )


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        total_records = len(
            data
        )


        present_records = sum(
            1
            for item in data
            if (
                str(
                    item.get(
                        "status",
                        ""
                    )
                ).lower()
                == "present"
            )
        )


        absent_records = sum(
            1
            for item in data
            if (
                str(
                    item.get(
                        "status",
                        ""
                    )
                ).lower()
                == "absent"
            )
        )


        leave_records = sum(
            1
            for item in data
            if (
                str(
                    item.get(
                        "status",
                        ""
                    )
                ).lower()
                == "leave"
            )
        )


        daily_summary_date = (
            exact_date
            or datetime.now().date()
        )

        teacher_daily_data = (
            get_all_teachers_daily_data(
                daily_summary_date,
                department_id=(
                    department_id
                    if isinstance(department_id, int)
                    else None
                )
            )
        )

        hod_daily_summary = (
            get_all_hods_daily_summary(
                daily_summary_date
            )
        )

        return jsonify({

            "success": True,

            "data": data,

            "summary": {

                "total":
                    total_records,

                "present":
                    present_records,

                "absent":
                    absent_records,

                "leave":
                    leave_records
            },

            "daily_summary": {
                "date": daily_summary_date.isoformat(),
                "teachers": teacher_daily_data["summary"],
                "hods": hod_daily_summary
            }

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load faculty attendance.",

            "error":
                str(error)

        }), 500


# ============================================================
# ADMIN - DAILY TEACHER ATTENDANCE
#
# GET /api/faculty-attendance/admin/teachers/daily
#     ?date=YYYY-MM-DD
#     &department_id=2
#     &status=absent
#     &search=teacher_name
# ============================================================

@bp.get("/admin/teachers/daily")
@jwt_required()
def get_admin_teachers_daily_attendance():

    try:
        admin_user, error_response = get_current_admin()

        if error_response:
            return error_response

        date_value = request.args.get("date", "").strip()
        department_value = request.args.get(
            "department_id",
            ""
        ).strip()
        status = request.args.get(
            "status",
            ""
        ).strip().lower()
        search = request.args.get(
            "search",
            ""
        ).strip().lower()

        attendance_date = (
            parse_date(date_value)
            if date_value
            else datetime.now().date()
        )

        if date_value and not attendance_date:
            return jsonify({
                "success": False,
                "message": "Invalid date. Use YYYY-MM-DD."
            }), 400

        department_id = None

        if department_value:
            try:
                department_id = int(department_value)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": (
                        "department_id must be an integer."
                    )
                }), 400

        if status and status not in {
            "present",
            "absent",
            "leave",
            "non_working",
        }:
            return jsonify({
                "success": False,
                "message": (
                    "Invalid status. Use present, absent, "
                    "leave or non_working."
                )
            }), 400

        daily_data = get_all_teachers_daily_data(
            attendance_date,
            department_id=department_id
        )

        records = daily_data["records"]

        if status:
            records = [
                item
                for item in records
                if str(item.get("status") or "").lower()
                == status
            ]

        if search:
            records = [
                item
                for item in records
                if search in " ".join([
                    str(item.get("faculty_code") or ""),
                    str(item.get("faculty_name") or ""),
                    str(item.get("department") or ""),
                    str(item.get("designation") or ""),
                    str(item.get("status") or ""),
                ]).lower()
            ]

        return jsonify({
            "success": True,
            "summary": daily_data["summary"],
            "data": records
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": (
                "Unable to load daily teacher attendance."
            ),
            "error": str(error),
        }), 500


# ============================================================
# ADMIN - COMBINED DAILY FACULTY SUMMARY
#
# GET /api/faculty-attendance/admin/daily?date=YYYY-MM-DD
# ============================================================

@bp.get("/admin/daily")
@jwt_required()
def get_admin_combined_daily_attendance():

    try:
        admin_user, error_response = get_current_admin()

        if error_response:
            return error_response

        date_value = request.args.get("date", "").strip()
        attendance_date = (
            parse_date(date_value)
            if date_value
            else datetime.now().date()
        )

        if date_value and not attendance_date:
            return jsonify({
                "success": False,
                "message": "Invalid date. Use YYYY-MM-DD."
            }), 400

        teacher_data = get_all_teachers_daily_data(
            attendance_date
        )
        hod_summary = get_all_hods_daily_summary(
            attendance_date
        )
        teacher_summary = teacher_data["summary"]

        present = (
            teacher_summary["present"]
            + hod_summary["present"]
        )
        absent = (
            teacher_summary["absent"]
            + hod_summary["absent"]
        )
        leave = (
            teacher_summary["leave"]
            + hod_summary["leave"]
        )
        total_active_faculty = (
            teacher_summary["total_active_teachers"]
            + hod_summary["total_active_hods"]
        )

        return jsonify({
            "success": True,
            "date": attendance_date.isoformat(),
            "summary": {
                "total_active_faculty": total_active_faculty,
                "present": present,
                "absent": absent,
                "leave": leave,
                "unmarked": (
                    teacher_summary["unmarked"]
                    + hod_summary["unmarked"]
                ),
                "attendance_percentage": (
                    round(
                        (present / total_active_faculty) * 100,
                        1
                    )
                    if total_active_faculty
                    else 0.0
                )
            },
            "teachers": teacher_summary,
            "hods": hod_summary
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": (
                "Unable to load combined daily attendance."
            ),
            "error": str(error),
        }), 500


# ============================================================
# ADMIN - DAILY HOD ATTENDANCE SUMMARY
#
# GET /api/faculty-attendance/admin/hods/daily?date=YYYY-MM-DD
# ============================================================

@bp.get("/admin/hods/daily")
@jwt_required()
def get_admin_hods_daily_attendance():

    try:
        user, error_response = get_current_admin()

        if error_response:
            return error_response

        date_value = request.args.get("date", "").strip()
        attendance_date = (
            parse_date(date_value)
            if date_value
            else datetime.now().date()
        )

        if date_value and not attendance_date:
            return jsonify({
                "success": False,
                "message": "Invalid date. Use YYYY-MM-DD."
            }), 400

        return jsonify({
            "success": True,
            "data": get_all_hods_daily_summary(attendance_date)
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Unable to load daily HOD attendance.",
            "error": str(error),
        }), 500


# ============================================================
# GET SINGLE ATTENDANCE RECORD
# ADMIN / EXISTING API
# ============================================================

@bp.get("/<int:attendance_id>")
def get_single_attendance(
    attendance_id
):

    try:

        attendance = db.session.get(
            FacultyAttendance,
            attendance_id
        )


        if not attendance:

            return jsonify({
                "success": False,
                "message":
                    "Attendance record not found."
            }), 404


        return jsonify({

            "success": True,

            "data":
                attendance.to_dict()

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load attendance record.",

            "error":
                str(error)

        }), 500


# ============================================================
# ============================================================
#
#               TEACHER SELF ATTENDANCE APIs
#
# ============================================================
# ============================================================


# ============================================================
# TEACHER - OWN ATTENDANCE SUMMARY AND HISTORY
#
# GET /api/faculty-attendance/teacher/self
# ============================================================

@bp.get("/teacher/self")
@jwt_required()
def get_teacher_self_attendance():

    try:
        user, teacher, error_response = (
            get_current_teacher()
        )

        if error_response:
            return error_response

        today = datetime.now().date()

        today_attendance = (
            FacultyAttendance.query
            .filter_by(
                faculty_user_id=user.id,
                date=today
            )
            .first()
        )

        calculated_attendance = (
            get_individual_attendance_data(
                faculty_user_id=user.id,
                department_id=teacher.department_id,
                teacher_id=teacher.id,
                faculty_start_date=teacher.joining_date
            )
        )

        registered_face = (
            FaceEncoding.query
            .filter_by(user_id=user.id)
            .first()
        )

        return jsonify({
            "success": True,
            "data": {
                "teacher": {
                    "user_id": user.id,
                    "teacher_id": teacher.id,
                    "teacher_code": teacher.teacher_code,
                    "full_name": teacher.full_name,
                    "designation": teacher.designation,
                    "department_id": teacher.department_id,
                    "department": (
                        teacher.department.name
                        if teacher.department
                        else None
                    ),
                    "photo_url": teacher.photo_url
                },
                "face_registered": registered_face is not None,
                "today": {
                    "date": today.isoformat(),
                    "marked": today_attendance is not None,
                    "record": (
                        today_attendance.to_dict()
                        if today_attendance
                        else None
                    )
                },
                "summary": calculated_attendance["summary"],
                "records": calculated_attendance["records"]
            }
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Unable to load teacher attendance.",
            "error": str(error)
        }), 500


# ============================================================
# TEACHER - MARK OWN ATTENDANCE USING REGISTERED FACE
#
# POST /api/faculty-attendance/teacher/self/face
# JSON: {"descriptor": [128 numeric values]}
# ============================================================

@bp.post("/teacher/self/face")
@jwt_required()
def mark_teacher_self_attendance_by_face():

    try:
        user, teacher, error_response = (
            get_current_teacher()
        )

        if error_response:
            return error_response

        today = datetime.now().date()
        non_working_reason = get_non_working_reason(
            today,
            teacher.department_id
        )

        if non_working_reason:
            return jsonify({
                "success": False,
                "message": (
                    "Attendance is not required today: "
                    f"{non_working_reason}."
                )
            }), 409

        data = request.get_json(silent=True) or {}

        captured_descriptor = normalize_face_descriptor(
            data.get("descriptor")
        )

        if captured_descriptor is None:
            return jsonify({
                "success": False,
                "message": (
                    "A valid 128-value face descriptor "
                    "is required."
                )
            }), 422

        registered_face = (
            FaceEncoding.query
            .filter_by(user_id=user.id)
            .first()
        )

        if not registered_face:
            return jsonify({
                "success": False,
                "message": (
                    "Your face is not registered. "
                    "Please complete Face Registration first."
                )
            }), 404

        stored_descriptor = normalize_face_descriptor(
            registered_face.descriptor
        )

        distance = calculate_face_distance(
            captured_descriptor,
            stored_descriptor
        )

        if distance is None:
            return jsonify({
                "success": False,
                "message": "Registered face data is invalid."
            }), 422

        # A biometric mismatch must not invalidate the JWT session.
        if distance > FACE_MATCH_THRESHOLD:
            return jsonify({
                "success": False,
                "recognized": False,
                "message": (
                    "Face does not match the logged-in "
                    "teacher account."
                )
            }), 422

        confidence = calculate_face_similarity(
            captured_descriptor,
            stored_descriptor
        )

        if confidence is None:
            confidence = round(
                max(
                    0.0,
                    min(
                        100.0,
                        (1.0 - distance) * 100.0
                    )
                ),
                1
            )

        today = datetime.now().date()

        existing_attendance = (
            FacultyAttendance.query
            .filter_by(
                faculty_user_id=user.id,
                date=today
            )
            .first()
        )

        teacher_data = {
            "user_id": user.id,
            "teacher_id": teacher.id,
            "teacher_code": teacher.teacher_code,
            "full_name": teacher.full_name,
            "designation": teacher.designation,
            "department_id": teacher.department_id,
            "department": (
                teacher.department.name
                if teacher.department
                else None
            ),
            "photo_url": teacher.photo_url
        }

        if existing_attendance:
            return jsonify({
                "success": True,
                "recognized": True,
                "already_marked": True,
                "message": (
                    "Attendance is already recorded "
                    "for today."
                ),
                "confidence": confidence,
                "match_distance": round(distance, 6),
                "teacher": teacher_data,
                "data": existing_attendance.to_dict()
            }), 200

        attendance = FacultyAttendance(
            faculty_user_id=user.id,
            department_id=teacher.department_id,
            date=today,
            status="present",
            remarks="Face Recognition",
            marked_by=user.id
        )

        db.session.add(attendance)
        db.session.commit()

        return jsonify({
            "success": True,
            "recognized": True,
            "already_marked": False,
            "message": "Teacher attendance marked successfully.",
            "confidence": confidence,
            "match_distance": round(distance, 6),
            "teacher": teacher_data,
            "data": attendance.to_dict()
        }), 201

    except Exception as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to mark teacher face attendance.",
            "error": str(error)
        }), 500


# ============================================================
# ============================================================
#
#                 HOD ATTENDANCE APIs
#
# ============================================================
# ============================================================


# ============================================================
# HOD - GET TEACHERS IN OWN DEPARTMENT
#
# GET /api/faculty-attendance/hod/teachers
# ============================================================

@bp.get("/hod/teachers")
@jwt_required()
def get_hod_department_teachers():

    try:

        _, hod, error_response = get_current_hod()

        if error_response:
            return error_response

        teachers = (
            Teacher.query
            .filter_by(department_id=hod.department_id)
            .order_by(Teacher.full_name.asc())
            .all()
        )

        return jsonify({
            "success": True,
            "department_id": hod.department_id,
            "data": [
                teacher.to_dict()
                for teacher in teachers
            ]
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Unable to load department teachers.",
            "error": str(error)
        }), 500


# ============================================================
# HOD - GET OWN ATTENDANCE FOR TODAY
#
# GET /api/faculty-attendance/hod/self/today
# ============================================================

@bp.get("/hod/self/today")
@jwt_required()
def get_hod_self_attendance_today():

    try:

        user, hod, error_response = (
            get_current_hod()
        )

        if error_response:
            return error_response

        today = datetime.now().date()

        attendance = (
            FacultyAttendance.query
            .filter_by(
                faculty_user_id=user.id,
                date=today
            )
            .first()
        )

        return jsonify({
            "success": True,
            "marked": attendance is not None,
            "data": (
                attendance.to_dict()
                if attendance
                else None
            ),
            "hod": {
                "user_id": user.id,
                "hod_code": hod.hod_code,
                "full_name": hod.full_name,
                "department_id": hod.department_id,
                "department": (
                    hod.department.name
                    if hod.department
                    else None
                ),
                "photo_url": hod.photo_url
            }
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Unable to load today's HOD attendance.",
            "error": str(error)
        }), 500


# ============================================================
# HOD - OWN ATTENDANCE SUMMARY AND HISTORY
#
# GET /api/faculty-attendance/hod/self
# ============================================================

@bp.get("/hod/self")
@jwt_required()
def get_hod_self_attendance():

    try:
        user, hod, error_response = get_current_hod()

        if error_response:
            return error_response

        today = datetime.now().date()
        today_attendance = (
            FacultyAttendance.query
            .filter_by(
                faculty_user_id=user.id,
                date=today
            )
            .first()
        )
        calculated_attendance = get_individual_attendance_data(
            faculty_user_id=user.id,
            department_id=hod.department_id,
            faculty_start_date=hod.joining_date
        )
        registered_face = (
            FaceEncoding.query
            .filter_by(user_id=user.id)
            .first()
        )

        return jsonify({
            "success": True,
            "data": {
                "hod": {
                    "user_id": user.id,
                    "hod_id": hod.id,
                    "hod_code": hod.hod_code,
                    "full_name": hod.full_name,
                    "department_id": hod.department_id,
                    "department": (
                        hod.department.name
                        if hod.department
                        else None
                    ),
                    "photo_url": hod.photo_url,
                },
                "face_registered": registered_face is not None,
                "today": {
                    "date": today.isoformat(),
                    "marked": today_attendance is not None,
                    "record": (
                        today_attendance.to_dict()
                        if today_attendance
                        else None
                    ),
                },
                "summary": calculated_attendance["summary"],
                "records": calculated_attendance["records"],
            }
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Unable to load HOD attendance.",
            "error": str(error),
        }), 500


# ============================================================
# HOD - MARK OWN ATTENDANCE USING REGISTERED FACE
#
# POST /api/faculty-attendance/hod/self/face
# JSON: {"descriptor": [128 numeric values]}
# ============================================================

@bp.post("/hod/self/face")
@jwt_required()
def mark_hod_self_attendance_by_face():

    try:

        user, hod, error_response = (
            get_current_hod()
        )

        if error_response:
            return error_response

        today = datetime.now().date()
        non_working_reason = get_non_working_reason(
            today,
            hod.department_id
        )

        if non_working_reason:
            return jsonify({
                "success": False,
                "message": (
                    "Attendance is not required today: "
                    f"{non_working_reason}."
                )
            }), 409

        data = request.get_json(silent=True) or {}

        captured_descriptor = normalize_face_descriptor(
            data.get("descriptor")
        )

        if captured_descriptor is None:
            return jsonify({
                "success": False,
                "message": (
                    "A valid 128-value face descriptor "
                    "is required."
                )
            }), 422

        registered_face = (
            FaceEncoding.query
            .filter_by(user_id=user.id)
            .first()
        )

        if not registered_face:
            return jsonify({
                "success": False,
                "message": (
                    "Your face is not registered. "
                    "Please register it first."
                )
            }), 404

        stored_descriptor = normalize_face_descriptor(
            registered_face.descriptor
        )

        distance = calculate_face_distance(
            captured_descriptor,
            stored_descriptor
        )

        if distance is None:
            return jsonify({
                "success": False,
                "message": "Registered face data is invalid."
            }), 422

        # Do not return HTTP 401 for a biometric mismatch. The JWT is still
        # valid and the API client must not clear the active HOD session.
        if distance > FACE_MATCH_THRESHOLD:
            return jsonify({
                "success": False,
                "recognized": False,
                "message": (
                    "Face does not match the logged-in HOD account."
                )
            }), 422

        today = datetime.now().date()

        existing_attendance = (
            FacultyAttendance.query
            .filter_by(
                faculty_user_id=user.id,
                date=today
            )
            .first()
        )

        # Euclidean distance remains the security decision. Cosine similarity
        # is returned only as a clearer UI match score, not as a probability.
        confidence = calculate_face_similarity(
            captured_descriptor,
            stored_descriptor
        )

        if confidence is None:
            confidence = round(
                max(0.0, min(100.0, (1.0 - distance) * 100.0)),
                1
            )

        hod_data = {
            "user_id": user.id,
            "hod_code": hod.hod_code,
            "full_name": hod.full_name,
            "department_id": hod.department_id,
            "department": (
                hod.department.name
                if hod.department
                else None
            ),
            "photo_url": hod.photo_url
        }

        if existing_attendance:
            return jsonify({
                "success": True,
                "recognized": True,
                "already_marked": True,
                "message": "Attendance is already marked for today.",
                "confidence": confidence,
                "match_distance": round(distance, 6),
                "hod": hod_data,
                "data": existing_attendance.to_dict()
            }), 200

        attendance = FacultyAttendance(
            faculty_user_id=user.id,
            department_id=hod.department_id,
            date=today,
            status="present",
            remarks="Face Recognition",
            marked_by=user.id
        )

        db.session.add(attendance)
        db.session.commit()

        return jsonify({
            "success": True,
            "recognized": True,
            "already_marked": False,
            "message": "HOD attendance marked successfully.",
            "confidence": confidence,
            "match_distance": round(distance, 6),
            "hod": hod_data,
            "data": attendance.to_dict()
        }), 201

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to mark HOD face attendance.",
            "error": str(error)
        }), 500


# ============================================================
# HOD - GET OWN DEPARTMENT TEACHER ATTENDANCE
#
# GET /api/faculty-attendance/hod
#
# Optional filters:
#
# ?status=present
# ?date=2026-08-15
# ?from_date=2026-08-01
# ?to_date=2026-08-31
# ?search=teacher_name
#
# ============================================================

@bp.get("/hod")
@jwt_required()
def get_hod_attendance():

    try:

        user, hod, error_response = (
            get_current_hod()
        )


        if error_response:

            return error_response


        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        status = (
            request.args
            .get("status", "")
            .strip()
            .lower()
        )


        exact_date_value = (
            request.args
            .get("date", "")
            .strip()
        )


        from_date_value = (
            request.args
            .get("from_date", "")
            .strip()
        )


        to_date_value = (
            request.args
            .get("to_date", "")
            .strip()
        )


        search = (
            request.args
            .get("search", "")
            .strip()
            .lower()
        )


        # ----------------------------------------------------
        # STATUS VALIDATION
        # ----------------------------------------------------

        if (
            status
            and status
            not in ALLOWED_ATTENDANCE_STATUS
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Invalid attendance status. "
                    "Use present, absent or leave."
                )
            }), 400


        # ----------------------------------------------------
        # DATE VALIDATION
        # ----------------------------------------------------

        exact_date = (
            parse_date(
                exact_date_value
            )
            if exact_date_value
            else None
        )


        from_date = (
            parse_date(
                from_date_value
            )
            if from_date_value
            else None
        )


        to_date = (
            parse_date(
                to_date_value
            )
            if to_date_value
            else None
        )


        if (
            exact_date_value
            and not exact_date
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Invalid date. "
                    "Use YYYY-MM-DD."
                )
            }), 400


        if (
            from_date_value
            and not from_date
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Invalid from_date. "
                    "Use YYYY-MM-DD."
                )
            }), 400


        if (
            to_date_value
            and not to_date
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Invalid to_date. "
                    "Use YYYY-MM-DD."
                )
            }), 400


        if (
            from_date
            and to_date
            and from_date > to_date
        ):

            return jsonify({
                "success": False,
                "message": (
                    "from_date cannot be "
                    "after to_date."
                )
            }), 400


        # ----------------------------------------------------
        # CALCULATED DEPARTMENT ATTENDANCE
        #
        # Use the same working-day rules as the Teacher
        # Dashboard. This includes automatic/inferred absences,
        # approved leave and excludes Sundays/holidays.
        # Today's unmarked attendance remains pending and is not
        # added as an absence until the next working day.
        # ----------------------------------------------------

        teachers = (
            Teacher.query
            .join(
                User,
                Teacher.user_id == User.id
            )
            .filter(
                Teacher.department_id == hod.department_id,
                func.lower(Teacher.status) == "active",
                User.is_active.is_(True),
                func.lower(User.role) == "teacher"
            )
            .order_by(Teacher.full_name.asc())
            .all()
        )

        department_name = (
            hod.department.name
            if hod.department
            else None
        )

        data = []

        for teacher in teachers:

            calculated = get_individual_attendance_data(
                faculty_user_id=teacher.user_id,
                department_id=teacher.department_id,
                teacher_id=teacher.id,
                faculty_start_date=teacher.joining_date,
                history_limit=None
            )

            for calculated_item in calculated["records"]:

                item = dict(calculated_item)
                item_date = parse_date(item.get("date"))

                if exact_date and item_date != exact_date:
                    continue

                if from_date and (
                    item_date is None
                    or item_date < from_date
                ):
                    continue

                if to_date and (
                    item_date is None
                    or item_date > to_date
                ):
                    continue

                item_status = str(
                    item.get("status") or ""
                ).strip().lower()

                if status and item_status != status:
                    continue

                item.update({
                    "teacher_id": teacher.id,
                    "faculty_user_id": teacher.user_id,
                    "faculty_code": teacher.teacher_code,
                    "faculty_name": teacher.full_name,
                    "designation": teacher.designation,
                    "department_id": teacher.department_id,
                    "department": department_name,
                })

                if item.get("inferred"):
                    item["marked_by_name"] = "System"

                if search:
                    searchable_text = " ".join([
                        str(item.get("faculty_code") or ""),
                        str(item.get("faculty_name") or ""),
                        str(item.get("department") or ""),
                        str(item.get("status") or "")
                    ]).lower()

                    if search not in searchable_text:
                        continue

                data.append(item)

        data.sort(
            key=lambda item: (
                str(item.get("date") or ""),
                str(item.get("faculty_name") or "")
            ),
            reverse=True
        )

        present_count = sum(
            1
            for item in data
            if str(item.get("status") or "").lower()
            == "present"
        )

        absent_count = sum(
            1
            for item in data
            if str(item.get("status") or "").lower()
            == "absent"
        )

        leave_count = sum(
            1
            for item in data
            if str(item.get("status") or "").lower()
            == "leave"
        )

        total_count = len(data)

        summary = {
            "total": total_count,
            "present": present_count,
            "absent": absent_count,
            "leave": leave_count,
            "inferred_absent": sum(
                1
                for item in data
                if (
                    str(item.get("status") or "").lower()
                    == "absent"
                    and bool(item.get("inferred"))
                )
            ),
            "attendance_percentage": (
                round(
                    (present_count / total_count) * 100,
                    1
                )
                if total_count
                else 0.0
            )
        }

        daily_summary_date = (
            exact_date
            if exact_date
            else datetime.now().date()
        )

        daily_summary = get_department_daily_summary(
            hod.department_id,
            daily_summary_date
        )


        return jsonify({

            "success": True,

            "department_id":
                hod.department_id,

            "department":
                (
                    hod.department.name
                    if hod.department
                    else None
                ),

            "summary":
                summary,

            "daily_summary":
                daily_summary,

            "data":
                data

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message": (
                "Unable to load department "
                "attendance."
            ),

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - MARK TEACHER ATTENDANCE
#
# POST /api/faculty-attendance/hod/mark
#
# JSON:
# {
#     "teacher_id": 1,
#     "date": "2026-08-15",
#     "status": "present",
#     "remarks": ""
# }
#
# If same teacher/date already exists:
# existing record will be UPDATED.
#
# ============================================================

@bp.post("/hod/mark")
@jwt_required()
def mark_hod_teacher_attendance():

    try:

        user, hod, error_response = (
            get_current_hod()
        )


        if error_response:

            return error_response


        data = (
            request.get_json(
                silent=True
            )
            or {}
        )


        # ----------------------------------------------------
        # TEACHER ID
        # ----------------------------------------------------

        teacher_id = data.get(
            "teacher_id"
        )


        try:

            teacher_id = int(
                teacher_id
            )

        except (TypeError, ValueError):

            return jsonify({
                "success": False,
                "message":
                    "Valid teacher_id is required"
            }), 400


        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        date_value = str(
            data.get(
                "date",
                ""
            )
        ).strip()


        attendance_date = parse_date(
            date_value
        )


        if not attendance_date:

            return jsonify({
                "success": False,
                "message": (
                    "Valid attendance date is required. "
                    "Use YYYY-MM-DD."
                )
            }), 400


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status = (
            str(
                data.get(
                    "status",
                    ""
                )
            )
            .strip()
            .lower()
        )


        if (
            status
            not in ALLOWED_ATTENDANCE_STATUS
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Status must be "
                    "present, absent or leave."
                )
            }), 400


        # ----------------------------------------------------
        # REMARKS
        # ----------------------------------------------------

        remarks = (
            str(
                data.get(
                    "remarks",
                    ""
                )
            )
            .strip()
        )


        # ----------------------------------------------------
        # GET TEACHER
        # ----------------------------------------------------

        teacher = db.session.get(
            Teacher,
            teacher_id
        )


        if not teacher:

            return jsonify({
                "success": False,
                "message": "Teacher not found"
            }), 404


        # ----------------------------------------------------
        # DEPARTMENT SECURITY
        # ----------------------------------------------------

        if (
            teacher.department_id
            != hod.department_id
        ):

            return jsonify({
                "success": False,
                "message": (
                    "You cannot mark attendance "
                    "for teachers from another "
                    "department"
                )
            }), 403


        # ----------------------------------------------------
        # TEACHER USER CHECK
        # ----------------------------------------------------

        if not teacher.user:

            return jsonify({
                "success": False,
                "message":
                    "Teacher login account not found"
            }), 404


        if (
            str(
                teacher.user.role or ""
            ).lower()
            != "teacher"
        ):

            return jsonify({
                "success": False,
                "message":
                    "Selected faculty is not a teacher"
            }), 400


        # ----------------------------------------------------
        # CHECK EXISTING ATTENDANCE
        #
        # Prevent duplicate teacher + date
        # ----------------------------------------------------

        attendance = (
            FacultyAttendance.query
            .filter_by(
                faculty_user_id=
                    teacher.user_id,
                date=
                    attendance_date
            )
            .first()
        )


        # ----------------------------------------------------
        # UPDATE EXISTING
        # ----------------------------------------------------

        if attendance:

            # Extra security
            if (
                attendance.department_id
                != hod.department_id
            ):

                return jsonify({
                    "success": False,
                    "message": (
                        "You cannot update attendance "
                        "from another department"
                    )
                }), 403


            attendance.status = (
                status
            )

            attendance.remarks = (
                remarks
                if remarks
                else None
            )

            attendance.department_id = (
                hod.department_id
            )

            attendance.marked_by = (
                user.id
            )


            db.session.commit()


            return jsonify({

                "success": True,

                "message": (
                    "Teacher attendance "
                    "updated successfully"
                ),

                "action":
                    "updated",

                "data":
                    attendance.to_dict()

            }), 200


        # ----------------------------------------------------
        # CREATE NEW ATTENDANCE
        # ----------------------------------------------------

        attendance = FacultyAttendance(

            faculty_user_id=
                teacher.user_id,

            department_id=
                hod.department_id,

            date=
                attendance_date,

            status=
                status,

            remarks=(
                remarks
                if remarks
                else None
            ),

            marked_by=
                user.id
        )


        db.session.add(
            attendance
        )

        db.session.commit()


        return jsonify({

            "success": True,

            "message": (
                "Teacher attendance "
                "marked successfully"
            ),

            "action":
                "created",

            "data":
                attendance.to_dict()

        }), 201


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to mark teacher attendance.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - UPDATE EXISTING TEACHER ATTENDANCE
#
# PATCH /api/faculty-attendance/hod/<attendance_id>
#
# JSON:
# {
#     "status": "absent",
#     "remarks": "Medical emergency"
# }
#
# ============================================================

@bp.patch("/hod/<int:attendance_id>")
@jwt_required()
def update_hod_teacher_attendance(
    attendance_id
):

    try:

        user, hod, error_response = (
            get_current_hod()
        )


        if error_response:

            return error_response


        attendance = db.session.get(
            FacultyAttendance,
            attendance_id
        )


        if not attendance:

            return jsonify({
                "success": False,
                "message":
                    "Attendance record not found"
            }), 404


        # ----------------------------------------------------
        # DEPARTMENT SECURITY
        # ----------------------------------------------------

        if (
            attendance.department_id
            != hod.department_id
        ):

            return jsonify({
                "success": False,
                "message": (
                    "You cannot update attendance "
                    "from another department"
                )
            }), 403


        # ----------------------------------------------------
        # TEACHER ROLE SECURITY
        # ----------------------------------------------------

        faculty_user = db.session.get(
            User,
            attendance.faculty_user_id
        )


        if not faculty_user:

            return jsonify({
                "success": False,
                "message":
                    "Faculty account not found"
            }), 404


        if (
            str(
                faculty_user.role or ""
            ).lower()
            != "teacher"
        ):

            return jsonify({
                "success": False,
                "message": (
                    "HOD can update only "
                    "teacher attendance"
                )
            }), 403


        teacher = (
            Teacher.query
            .filter_by(
                user_id=
                    faculty_user.id
            )
            .first()
        )


        if not teacher:

            return jsonify({
                "success": False,
                "message":
                    "Teacher profile not found"
            }), 404


        if (
            teacher.department_id
            != hod.department_id
        ):

            return jsonify({
                "success": False,
                "message": (
                    "You cannot update attendance "
                    "for teachers from another "
                    "department"
                )
            }), 403


        data = (
            request.get_json(
                silent=True
            )
            or {}
        )


        has_update = False


        # ----------------------------------------------------
        # STATUS UPDATE
        # ----------------------------------------------------

        if "status" in data:

            status = (
                str(
                    data.get(
                        "status",
                        ""
                    )
                )
                .strip()
                .lower()
            )


            if (
                status
                not in ALLOWED_ATTENDANCE_STATUS
            ):

                return jsonify({
                    "success": False,
                    "message": (
                        "Status must be present, "
                        "absent or leave."
                    )
                }), 400


            attendance.status = (
                status
            )

            has_update = True


        # ----------------------------------------------------
        # REMARKS UPDATE
        # ----------------------------------------------------

        if "remarks" in data:

            remarks = data.get(
                "remarks"
            )


            if remarks is None:

                attendance.remarks = None

            else:

                remarks = str(
                    remarks
                ).strip()

                attendance.remarks = (
                    remarks
                    if remarks
                    else None
                )


            has_update = True


        # ----------------------------------------------------
        # NOTHING TO UPDATE
        # ----------------------------------------------------

        if not has_update:

            return jsonify({
                "success": False,
                "message": (
                    "Provide status or remarks "
                    "to update"
                )
            }), 400


        attendance.marked_by = (
            user.id
        )


        db.session.commit()


        return jsonify({

            "success": True,

            "message": (
                "Teacher attendance "
                "updated successfully"
            ),

            "data":
                attendance.to_dict()

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message": (
                "Unable to update "
                "teacher attendance."
            ),

            "error":
                str(error)

        }), 500
