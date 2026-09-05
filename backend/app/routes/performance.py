from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func, or_

from ..models import (
    AcademicEvent,
    FacultyAttendance,
    LeaveRequest,
    PerformanceRecord,
    Teacher,
    Timetable,
    User,
)


bp = Blueprint(
    "performance",
    __name__,
    url_prefix="/api/performance"
)


def calculate_percentage(record):
    if record.score is None or record.max_score is None:
        return 0.0

    score = float(record.score)
    max_score = float(record.max_score)

    if max_score <= 0:
        return 0.0

    return round((score / max_score) * 100, 2)


def get_performance_band(percentage, evaluated=True):
    if not evaluated:
        return "not_evaluated"
    if percentage >= 80:
        return "excellent"
    if percentage >= 60:
        return "good"
    if percentage >= 40:
        return "average"
    return "poor"


def get_current_teacher():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None, None, (
            jsonify({
                "success": False,
                "message": "Invalid login session."
            }),
            401,
        )

    user = User.query.get(user_id)

    if not user or user.role != "teacher" or not user.is_active:
        return None, None, (
            jsonify({
                "success": False,
                "message": "Teacher access is required."
            }),
            403,
        )

    teacher = Teacher.query.filter_by(user_id=user.id).first()

    if not teacher:
        return None, None, (
            jsonify({
                "success": False,
                "message": "Teacher profile was not found."
            }),
            404,
        )

    return user, teacher, None


def month_key(year, month):
    return f"{year:04d}-{month:02d}"


def recent_months(total=6):
    today = date.today()
    months = []

    for offset in range(total - 1, -1, -1):
        number = today.year * 12 + today.month - 1 - offset
        year, zero_based_month = divmod(number, 12)
        month = zero_based_month + 1
        months.append({
            "key": month_key(year, month),
            "label": date(year, month, 1).strftime("%b %Y"),
        })

    return months


def is_non_working_day(attendance_date, department_id=None):
    if attendance_date.weekday() == 6:
        return True

    department_filter = AcademicEvent.department_id.is_(None)

    if department_id is not None:
        department_filter = or_(
            AcademicEvent.department_id.is_(None),
            AcademicEvent.department_id == department_id,
        )

    holiday = (
        AcademicEvent.query
        .filter(
            AcademicEvent.start_date <= attendance_date,
            or_(
                AcademicEvent.end_date.is_(None),
                AcademicEvent.end_date >= attendance_date,
            ),
            department_filter,
            or_(
                func.lower(AcademicEvent.event_type).in_([
                    "holiday",
                    "vacation",
                    "college_closed",
                    "college closed",
                ]),
                func.lower(AcademicEvent.title).like("%holiday%"),
            ),
        )
        .first()
    )

    return holiday is not None


def get_teacher_attendance_summary(user_id, teacher):
    attendance_records = (
        FacultyAttendance.query
        .filter_by(faculty_user_id=user_id)
        .order_by(FacultyAttendance.date.asc())
        .all()
    )

    empty_summary = {
        "attendance_percentage": 0.0,
        "present_days": 0,
        "absent_days": 0,
        "leave_days": 0,
        "working_days": 0,
        "attendance_records": 0,
        "recorded_attendance_records": 0,
        "inferred_absent_days": 0,
    }

    if not attendance_records:
        return empty_summary, attendance_records, []

    record_by_date = {
        item.date: item
        for item in attendance_records
        if item.date
    }

    today = date.today()
    approved_leave_dates = set()

    approved_leaves = (
        LeaveRequest.query
        .filter(
            LeaveRequest.teacher_id == teacher.id,
            func.lower(LeaveRequest.status) == "approved",
            LeaveRequest.end_date >= attendance_records[0].date,
            LeaveRequest.start_date <= today,
        )
        .all()
    )

    for leave_request in approved_leaves:
        leave_date = leave_request.start_date

        while leave_date <= leave_request.end_date and leave_date <= today:
            approved_leave_dates.add(leave_date)
            leave_date += timedelta(days=1)

    include_today = (
        today in record_by_date
        or today in approved_leave_dates
    )
    calculation_end = (
        today
        if include_today
        else today - timedelta(days=1)
    )
    calculation_start = attendance_records[0].date

    working_dates = []
    current_date = calculation_start

    while current_date <= calculation_end:
        if not is_non_working_day(
            current_date,
            teacher.department_id,
        ):
            working_dates.append(current_date)

        current_date += timedelta(days=1)

    present_days = 0
    absent_days = 0
    leave_days = 0
    inferred_absent_days = 0

    for working_date in working_dates:
        record = record_by_date.get(working_date)
        status = (
            str(record.status or "").lower()
            if record
            else None
        )

        if status == "present":
            present_days += 1
        elif status == "leave" or working_date in approved_leave_dates:
            leave_days += 1
        else:
            absent_days += 1

            if record is None:
                inferred_absent_days += 1

    working_day_count = len(working_dates)
    attendance_percentage = (
        round((present_days / working_day_count) * 100, 2)
        if working_day_count
        else 0.0
    )

    return {
        "attendance_percentage": attendance_percentage,
        "present_days": present_days,
        "absent_days": absent_days,
        "leave_days": leave_days,
        "working_days": working_day_count,
        "attendance_records": working_day_count,
        "recorded_attendance_records": len(attendance_records),
        "inferred_absent_days": inferred_absent_days,
    }, attendance_records, working_dates


# Existing Admin/HOD-compatible endpoint. Its response is unchanged.
@bp.get("")
def get_performance_records():
    try:
        user_id = request.args.get("user_id", type=int)
        term = request.args.get("term", "").strip()

        query = PerformanceRecord.query

        if user_id:
            query = query.filter(PerformanceRecord.user_id == user_id)

        if term:
            query = query.filter(PerformanceRecord.term == term)

        records = query.order_by(PerformanceRecord.id.desc()).all()
        data = []

        for record in records:
            item = record.to_dict()
            percentage = calculate_percentage(record)
            item["percentage"] = percentage
            item["performance_band"] = get_performance_band(percentage)
            data.append(item)

        latest_by_user = {}
        for record in records:
            if record.user_id not in latest_by_user:
                latest_by_user[record.user_id] = record

        latest_records = list(latest_by_user.values())
        percentages = [
            calculate_percentage(record)
            for record in latest_records
        ]

        bands = {
            "excellent": 0,
            "good": 0,
            "average": 0,
            "poor": 0,
        }

        for percentage in percentages:
            bands[get_performance_band(percentage)] += 1

        total_faculty = len(latest_records)
        overall_average = (
            round(sum(percentages) / total_faculty, 2)
            if total_faculty
            else 0.0
        )

        return jsonify({
            "success": True,
            "data": data,
            "summary": {
                "total_records": len(data),
                "total_faculty": total_faculty,
                "overall_average": overall_average,
                **bands,
            },
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Unable to load performance records.",
            "error": str(error),
        }), 500


# Logged-in Teacher Performance
@bp.get("/teacher/me")
@jwt_required()
def get_teacher_performance():
    try:
        user, teacher, error_response = get_current_teacher()

        if error_response:
            return error_response

        requested_term = request.args.get("term", "").strip()

        all_records = (
            PerformanceRecord.query
            .filter_by(user_id=user.id)
            .order_by(PerformanceRecord.id.desc())
            .all()
        )

        available_terms = []
        for record in all_records:
            if record.term and record.term not in available_terms:
                available_terms.append(record.term)

        selected_term = requested_term or (
            available_terms[0] if available_terms else None
        )

        term_records = [
            record
            for record in all_records
            if not selected_term or record.term == selected_term
        ]

        latest_by_subject = {}
        general_records = []

        for record in term_records:
            if record.subject_id is None:
                general_records.append(record)
            elif record.subject_id not in latest_by_subject:
                latest_by_subject[record.subject_id] = record

        evaluation_records = (
            list(latest_by_subject.values()) + general_records[:1]
        )
        percentages = [
            calculate_percentage(record)
            for record in evaluation_records
        ]
        evaluated = bool(percentages)
        overall_percentage = (
            round(sum(percentages) / len(percentages), 2)
            if percentages
            else 0.0
        )

        (
            attendance_summary,
            attendance_records,
            working_dates,
        ) = get_teacher_attendance_summary(
            user.id,
            teacher,
        )

        timetable_entries = (
            Timetable.query
            .filter_by(teacher_id=teacher.id)
            .order_by(Timetable.day_of_week, Timetable.start_time)
            .all()
        )

        subject_map = {}
        for entry in timetable_entries:
            if entry.subject:
                subject_map[entry.subject.id] = entry.subject

        for record in all_records:
            if record.subject:
                subject_map[record.subject.id] = record.subject

        subject_rows = []
        for subject_id, subject in subject_map.items():
            record = latest_by_subject.get(subject_id)
            scheduled_classes = sum(
                1 for entry in timetable_entries
                if entry.subject_id == subject_id
            )

            subject_rows.append({
                "subject_id": subject.id,
                "subject": subject.name,
                "code": subject.code,
                "semester": subject.semester,
                "credits": subject.credits,
                "weekly_scheduled_classes": scheduled_classes,
                "score": float(record.score) if record and record.score is not None else None,
                "max_score": float(record.max_score) if record and record.max_score is not None else None,
                "percentage": calculate_percentage(record) if record else None,
                "grade": record.grade if record else None,
                "remarks": record.remarks if record else None,
                "performance_band": (
                    get_performance_band(calculate_percentage(record))
                    if record
                    else "not_evaluated"
                ),
            })

        subject_rows.sort(key=lambda item: item["subject"].lower())

        months = recent_months()
        trend = []

        for month in months:
            monthly_working_dates = [
                working_date
                for working_date in working_dates
                if working_date.strftime("%Y-%m") == month["key"]
            ]
            monthly_present = sum(
                1
                for working_date in monthly_working_dates
                for item in attendance_records
                if item.date == working_date
                and str(item.status or "").lower() == "present"
            )
            monthly_attendance_percentage = (
                round(
                    (monthly_present / len(monthly_working_dates)) * 100,
                    2,
                )
                if monthly_working_dates
                else None
            )

            monthly_performance = [
                calculate_percentage(record)
                for record in all_records
                if record.created_at
                and record.created_at.strftime("%Y-%m") == month["key"]
            ]

            trend.append({
                "month": month["key"],
                "label": month["label"],
                "performance": (
                    round(
                        sum(monthly_performance) / len(monthly_performance),
                        2,
                    )
                    if monthly_performance
                    else None
                ),
                "attendance": monthly_attendance_percentage,
            })

        activities = []
        for record in all_records[:10]:
            activities.append({
                "id": record.id,
                "type": "performance_evaluation",
                "subject": record.subject.name if record.subject else "Overall Performance",
                "term": record.term,
                "percentage": calculate_percentage(record),
                "grade": record.grade,
                "remarks": record.remarks,
                "created_at": (
                    record.created_at.isoformat()
                    if record.created_at
                    else None
                ),
            })

        return jsonify({
            "success": True,
            "data": {
                "teacher": {
                    "id": teacher.id,
                    "user_id": user.id,
                    "teacher_code": teacher.teacher_code,
                    "full_name": teacher.full_name,
                    "designation": teacher.designation,
                    "department": (
                        teacher.department.name
                        if teacher.department
                        else None
                    ),
                    "photo_url": teacher.photo_url,
                },
                "selected_term": selected_term,
                "available_terms": available_terms,
                "summary": {
                    "overall_percentage": overall_percentage,
                    "performance_band": get_performance_band(
                        overall_percentage,
                        evaluated,
                    ),
                    "evaluated": evaluated,
                    "evaluation_records": len(evaluation_records),
                    **attendance_summary,
                    "assigned_subjects": len(subject_rows),
                    "weekly_scheduled_classes": len(timetable_entries),
                },
                "subjects": subject_rows,
                "trend": trend,
                "activities": activities,
            },
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Unable to load teacher performance.",
            "error": str(error),
        }), 500
