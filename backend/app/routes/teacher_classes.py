from datetime import date

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Subject, Teacher, Timetable, User


bp = Blueprint(
    "teacher_classes",
    __name__,
    url_prefix="/api/teachers"
)


def logged_in_teacher():
    try:
        user_id = int(get_jwt_identity())
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

    if str(user.role or "").strip().lower() != "teacher":
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

    teacher = Teacher.query.filter_by(user_id=user.id).first()

    if not teacher:
        return None, None, (
            jsonify({
                "success": False,
                "message": "Teacher profile not found"
            }),
            404
        )

    return user, teacher, None


@bp.get("/me/classes")
@jwt_required()
def get_my_classes():
    try:
        user, teacher, error = logged_in_teacher()

        if error:
            return error

        subjects = (
            Subject.query
            .filter_by(teacher_id=teacher.id)
            .order_by(Subject.name.asc())
            .all()
        )

        timetable = (
            Timetable.query
            .filter_by(teacher_id=teacher.id)
            .all()
        )

        timetable.sort(
            key=lambda item: (
                item.day_of_week or "",
                item.start_time,
                item.id
            )
        )

        classes = {}

        for subject in subjects:
            classes[subject.id] = {
                "subject_id": subject.id,
                "subject_name": subject.name,
                "subject_code": subject.code,
                "semester": subject.semester,
                "credits": subject.credits,
                "sections": set(),
                "rooms": set(),
                "class_types": set(),
                "schedule": []
            }

        for entry in timetable:
            subject = entry.subject

            if not subject:
                continue

            if subject.id not in classes:
                classes[subject.id] = {
                    "subject_id": subject.id,
                    "subject_name": subject.name,
                    "subject_code": subject.code,
                    "semester": subject.semester or entry.semester,
                    "credits": subject.credits,
                    "sections": set(),
                    "rooms": set(),
                    "class_types": set(),
                    "schedule": []
                }

            item = classes[subject.id]

            if entry.section:
                item["sections"].add(entry.section)
            if entry.room:
                item["rooms"].add(entry.room)
            if entry.class_type:
                item["class_types"].add(entry.class_type)

            item["schedule"].append(entry.to_dict())

        result = []

        for item in classes.values():
            result.append({
                "subject_id": item["subject_id"],
                "subject_name": item["subject_name"],
                "subject_code": item["subject_code"],
                "semester": item["semester"],
                "credits": item["credits"],
                "sections": sorted(item["sections"]),
                "rooms": sorted(item["rooms"]),
                "class_types": sorted(item["class_types"]),
                "weekly_classes": len(item["schedule"]),
                "status": (
                    "scheduled" if item["schedule"] else "assigned"
                ),
                "schedule": item["schedule"]
            })

        result.sort(
            key=lambda item: (
                str(item.get("semester") or ""),
                str(item.get("subject_name") or "").lower()
            )
        )

        today_name = date.today().strftime("%A").lower()
        today_classes = sum(
            1
            for entry in timetable
            if str(entry.day_of_week or "").strip().lower() == today_name
        )

        return jsonify({
            "success": True,
            "data": {
                "user": user.to_dict(),
                "teacher": teacher.to_dict(),
                "stats": {
                    "assigned_subjects": len(result),
                    "today_classes": today_classes,
                    "weekly_classes": len(timetable),
                    "department": (
                        teacher.department.name
                        if teacher.department
                        else None
                    )
                },
                "classes": result
            }
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Unable to load teacher classes",
            "error": str(error)
        }), 500
