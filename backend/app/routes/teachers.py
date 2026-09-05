import os
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import (
    AcademicEvent,
    AuditLog,
    FaceEncoding,
    FacultyAttendance,
    Hod,
    LeaveRequest,
    Notice,
    Notification,
    PerformanceRecord,
    Subject,
    Teacher,
    Timetable,
    User,
)


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "teacher",
    __name__,
    url_prefix="/api/teachers"
)


# ============================================================
# GET REQUEST DATA
# Supports FormData + JSON
# ============================================================

def get_request_data():

    if request.form:
        return request.form

    return request.get_json(
        silent=True
    ) or {}


# ============================================================
# DATE PARSER
# ============================================================

def parse_date(value):

    if not value:
        return None

    return datetime.strptime(
        value,
        "%Y-%m-%d"
    ).date()


# ============================================================
# AUDIT LOG
#
# Audit failure will NOT break working Teacher CRUD.
# ============================================================

def write_audit_log(
    action,
    entity_id,
    details
):

    try:

        forwarded_ip = request.headers.get(
            "X-Forwarded-For"
        )

        ip_address = (
            forwarded_ip.split(",")[0].strip()
            if forwarded_ip
            else request.remote_addr
        )


        log = AuditLog(

            user_id=None,

            action=action,

            entity="teacher",

            entity_id=entity_id,

            details=details,

            ip_address=ip_address

        )


        db.session.add(log)

        db.session.commit()


    except Exception as error:

        db.session.rollback()

        print(
            "Audit Log Error:",
            error
        )


# ============================================================
# PHOTO HELPER
# ============================================================

def save_teacher_photo(
    photo,
    user_id
):

    if (
        not photo
        or not photo.filename
    ):
        return None


    upload_folder = os.path.join(
        os.getcwd(),
        "uploads",
        "teachers"
    )


    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    original_filename = secure_filename(
        photo.filename
    )


    filename = (
        f"{user_id}_{original_filename}"
    )


    photo.save(
        os.path.join(
            upload_folder,
            filename
        )
    )


    return (
        f"/uploads/teachers/{filename}"
    )


# ============================================================
# GET ALL TEACHERS
# ============================================================

@bp.get("")
def get_teachers():

    try:

        teachers = (
            Teacher.query
            .order_by(
                Teacher.id.desc()
            )
            .all()
        )


        return jsonify({

            "success": True,

            "data": [
                teacher.to_dict()
                for teacher in teachers
            ]

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500


# ============================================================
# GET SINGLE TEACHER
# ============================================================

@bp.get("/<int:teacher_id>")
def get_teacher(teacher_id):

    teacher = Teacher.query.get(
        teacher_id
    )


    if not teacher:

        return jsonify({

            "success": False,

            "message":
                "Teacher not found"

        }), 404


    return jsonify({

        "success": True,

        "data":
            teacher.to_dict()

    })


# ============================================================
# ADD TEACHER
# ============================================================

@bp.post("")
def add_teacher():

    data = get_request_data()


    # --------------------------------------------------------
    # FORM VALUES
    # --------------------------------------------------------

    teacher_code = (
        data.get("teacher_code")
        or data.get("teacher_id")
    )


    full_name = data.get(
        "full_name"
    )


    email = data.get(
        "email"
    )


    username = data.get(
        "username"
    )


    password = data.get(
        "password"
    )


    phone = data.get(
        "phone"
    )


    gender = data.get(
        "gender"
    )


    dob = data.get(
        "dob"
    )


    blood_group = data.get(
        "blood_group"
    )


    address = data.get(
        "address"
    )


    department_id = data.get(
        "department_id"
    )


    designation = data.get(
        "designation"
    )


    qualification = data.get(
        "qualification"
    )


    experience_years = (
        data.get("experience_years")
        or data.get("experience")
        or 0
    )


    salary = data.get(
        "salary"
    )


    joining_date = data.get(
        "joining_date"
    )


    status = data.get(
        "status",
        "active"
    )


    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    if not all([

        teacher_code,
        full_name,
        email,
        username,
        password

    ]):

        return jsonify({

            "success": False,

            "message":
                "Required fields are missing"

        }), 400


    # ========================================================
    # DUPLICATE USERNAME
    # ========================================================

    if User.query.filter_by(
        username=username
    ).first():

        return jsonify({

            "success": False,

            "message":
                "Username already exists"

        }), 409


    # ========================================================
    # DUPLICATE EMAIL
    # ========================================================

    if User.query.filter_by(
        email=email
    ).first():

        return jsonify({

            "success": False,

            "message":
                "Email already exists"

        }), 409


    # ========================================================
    # DUPLICATE TEACHER CODE
    # ========================================================

    if Teacher.query.filter_by(
        teacher_code=teacher_code
    ).first():

        return jsonify({

            "success": False,

            "message":
                "Teacher ID already exists"

        }), 409


    try:

        # ====================================================
        # CREATE USER
        # ====================================================

        user = User(

            username=username,

            email=email,

            role="teacher",

            is_active=(
                str(status).lower()
                == "active"
            )

        )


        user.set_password(
            password
        )


        db.session.add(user)

        db.session.flush()


        # ====================================================
        # CREATE TEACHER
        # ====================================================

        teacher = Teacher(

            user_id=user.id,

            teacher_code=
                teacher_code,

            full_name=
                full_name,

            phone=
                phone,

            gender=
                gender,

            blood_group=
                blood_group,

            address=
                address,

            department_id=(
                int(department_id)
                if department_id
                else None
            ),

            designation=
                designation,

            qualification=
                qualification,

            experience_years=(
                int(experience_years)
                if experience_years
                else 0
            ),

            salary=(
                Decimal(str(salary))
                if salary
                else None
            ),

            status=
                str(status).lower()

        )


        # ====================================================
        # DATE OF BIRTH
        # ====================================================

        if dob:

            teacher.dob = parse_date(
                dob
            )


        # ====================================================
        # JOINING DATE
        # ====================================================

        if joining_date:

            teacher.joining_date = (
                parse_date(
                    joining_date
                )
            )


        # ====================================================
        # PHOTO
        # ====================================================

        photo = request.files.get(
            "photo"
        )


        if (
            photo
            and photo.filename
        ):

            teacher.photo_url = (
                save_teacher_photo(
                    photo,
                    user.id
                )
            )


        # ====================================================
        # SAVE TEACHER
        # ====================================================

        db.session.add(
            teacher
        )


        db.session.commit()


        # ====================================================
        # REAL AUDIT LOG
        # ====================================================

        write_audit_log(

            action="CREATE",

            entity_id=
                teacher.id,

            details=(
                f"Teacher added: "
                f"{teacher.full_name} "
                f"({teacher.teacher_code})"
            )

        )


        return jsonify({

            "success": True,

            "message":
                "Teacher added successfully",

            "data":
                teacher.to_dict()

        }), 201


    except (
        ValueError,
        InvalidOperation
    ) as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                f"Invalid data: {str(error)}"

        }), 400


    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500


# ============================================================
# UPDATE TEACHER
# ============================================================

@bp.put("/<int:teacher_id>")
def update_teacher(teacher_id):

    teacher = Teacher.query.get(
        teacher_id
    )


    if not teacher:

        return jsonify({

            "success": False,

            "message":
                "Teacher not found"

        }), 404


    data = get_request_data()


    try:

        # ====================================================
        # TEACHER CODE
        # ====================================================

        new_teacher_code = (

            data.get(
                "teacher_code"
            )

            or

            data.get(
                "teacher_id"
            )

        )


        if new_teacher_code:

            duplicate_code = (
                Teacher.query
                .filter(
                    Teacher.teacher_code
                    == new_teacher_code,

                    Teacher.id
                    != teacher.id
                )
                .first()
            )


            if duplicate_code:

                return jsonify({

                    "success": False,

                    "message":
                        "Teacher ID already exists"

                }), 409


            teacher.teacher_code = (
                new_teacher_code
            )


        # ====================================================
        # BASIC DETAILS
        # ====================================================

        if data.get(
            "full_name"
        ) is not None:

            teacher.full_name = (
                data.get(
                    "full_name"
                )
            )


        if data.get(
            "phone"
        ) is not None:

            teacher.phone = (
                data.get(
                    "phone"
                )
            )


        if data.get(
            "gender"
        ) is not None:

            teacher.gender = (
                data.get(
                    "gender"
                )
            )


        if data.get(
            "blood_group"
        ) is not None:

            teacher.blood_group = (
                data.get(
                    "blood_group"
                )
            )


        if data.get(
            "address"
        ) is not None:

            teacher.address = (
                data.get(
                    "address"
                )
            )


        if data.get(
            "designation"
        ) is not None:

            teacher.designation = (
                data.get(
                    "designation"
                )
            )


        if data.get(
            "qualification"
        ) is not None:

            teacher.qualification = (
                data.get(
                    "qualification"
                )
            )


        # ====================================================
        # DEPARTMENT
        # ====================================================

        if "department_id" in data:

            department_id = (
                data.get(
                    "department_id"
                )
            )


            teacher.department_id = (

                int(department_id)

                if department_id

                else None

            )


        # ====================================================
        # EXPERIENCE
        # ====================================================

        experience_value = (
            data.get(
                "experience_years"
            )
        )


        if experience_value is None:

            experience_value = (
                data.get(
                    "experience"
                )
            )


        if experience_value is not None:

            teacher.experience_years = (

                int(experience_value)

                if experience_value

                else 0

            )


        # ====================================================
        # SALARY
        # ====================================================

        if "salary" in data:

            salary = data.get(
                "salary"
            )


            teacher.salary = (

                Decimal(
                    str(salary)
                )

                if salary

                else None

            )


        # ====================================================
        # DATE OF BIRTH
        # ====================================================

        if "dob" in data:

            dob = data.get(
                "dob"
            )


            teacher.dob = (

                parse_date(
                    dob
                )

                if dob

                else None

            )


        # ====================================================
        # JOINING DATE
        # ====================================================

        if "joining_date" in data:

            joining_date = (
                data.get(
                    "joining_date"
                )
            )


            teacher.joining_date = (

                parse_date(
                    joining_date
                )

                if joining_date

                else None

            )


        # ====================================================
        # EMAIL
        # ====================================================

        email = data.get(
            "email"
        )


        if (
            email is not None
            and teacher.user
        ):

            duplicate_email = (
                User.query
                .filter(
                    User.email == email,
                    User.id
                    != teacher.user.id
                )
                .first()
            )


            if duplicate_email:

                return jsonify({

                    "success": False,

                    "message":
                        "Email already exists"

                }), 409


            teacher.user.email = (
                email
            )


        # ====================================================
        # USERNAME
        # ====================================================

        username = data.get(
            "username"
        )


        if (
            username is not None
            and teacher.user
        ):

            duplicate_username = (
                User.query
                .filter(
                    User.username
                    == username,

                    User.id
                    != teacher.user.id
                )
                .first()
            )


            if duplicate_username:

                return jsonify({

                    "success": False,

                    "message":
                        "Username already exists"

                }), 409


            teacher.user.username = (
                username
            )


        # ====================================================
        # PASSWORD
        # ====================================================

        password = data.get(
            "password"
        )


        if (
            password
            and teacher.user
        ):

            teacher.user.set_password(
                password
            )


        # ====================================================
        # STATUS
        # ====================================================

        status = data.get(
            "status"
        )


        if status is not None:

            teacher.status = (
                str(status).lower()
            )


            if teacher.user:

                teacher.user.is_active = (
                    teacher.status
                    == "active"
                )


        # ====================================================
        # PHOTO UPDATE
        # ====================================================

        photo = request.files.get(
            "photo"
        )


        if (
            photo
            and photo.filename
        ):

            teacher.photo_url = (
                save_teacher_photo(
                    photo,
                    teacher.user_id
                )
            )


        # ====================================================
        # SAVE UPDATE
        # ====================================================

        db.session.commit()


        # ====================================================
        # REAL AUDIT LOG
        # ====================================================

        write_audit_log(

            action="UPDATE",

            entity_id=
                teacher.id,

            details=(
                f"Teacher updated: "
                f"{teacher.full_name} "
                f"({teacher.teacher_code})"
            )

        )


        return jsonify({

            "success": True,

            "message":
                "Teacher updated successfully",

            "data":
                teacher.to_dict()

        })


    except (
        ValueError,
        InvalidOperation
    ) as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                f"Invalid data: {str(error)}"

        }), 400


    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500


# ============================================================
# DELETE TEACHER
# ============================================================

@bp.delete("/<int:teacher_id>")
def delete_teacher(teacher_id):

    teacher = Teacher.query.get(
        teacher_id
    )


    if not teacher:

        return jsonify({

            "success": False,

            "message":
                "Teacher not found"

        }), 404


    try:

        # Save details before deletion

        deleted_id = (
            teacher.id
        )


        deleted_name = (
            teacher.full_name
        )


        deleted_code = (
            teacher.teacher_code
        )


        user = teacher.user


        # ====================================================
        # DELETE TEACHER
        # ====================================================

        db.session.delete(
            teacher
        )


        # Also remove linked login user

        if user:

            db.session.delete(
                user
            )


        db.session.commit()


        # ====================================================
        # REAL AUDIT LOG
        # ====================================================

        write_audit_log(

            action="DELETE",

            entity_id=
                deleted_id,

            details=(
                f"Teacher deleted: "
                f"{deleted_name} "
                f"({deleted_code})"
            )

        )


        return jsonify({

            "success": True,

            "message":
                "Teacher deleted successfully"

        })


    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500


# ============================================================
# TEACHER DASHBOARD
#
# GET /api/teachers/me/dashboard
#
# This is deliberately isolated from Admin/HOD Teacher CRUD.
# It only reads data belonging to the logged-in teacher.
# ============================================================

def get_logged_in_teacher():

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


    teacher = (
        Teacher.query
        .filter_by(
            user_id=user.id
        )
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


    return user, teacher, None


# ============================================================
# TEACHER SELF PROFILE
#
# GET   /api/teachers/me/profile
# PATCH /api/teachers/me/profile
# ============================================================

@bp.get("/me/profile")
@jwt_required()
def get_teacher_profile():

    try:

        user, teacher, error_response = (
            get_logged_in_teacher()
        )

        if error_response:
            return error_response

        return jsonify({
            "success": True,
            "data": {
                "user": user.to_dict(),
                "teacher": teacher.to_dict(),
                "editable_fields": [
                    "full_name",
                    "email",
                    "phone",
                    "gender",
                    "dob",
                    "blood_group",
                    "address",
                    "qualification",
                    "photo",
                ],
                "read_only_fields": [
                    "teacher_code",
                    "username",
                    "department_id",
                    "department",
                    "designation",
                    "experience_years",
                    "salary",
                    "joining_date",
                    "status",
                ],
            }
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Unable to load Teacher profile",
            "error": str(error)
        }), 500


@bp.patch("/me/profile")
@jwt_required()
def update_teacher_profile():

    try:

        user, teacher, error_response = (
            get_logged_in_teacher()
        )

        if error_response:
            return error_response

        data = get_request_data()

        if "full_name" in data:
            full_name = str(
                data.get("full_name", "") or ""
            ).strip()

            if not full_name:
                return jsonify({
                    "success": False,
                    "message": "Full name cannot be empty"
                }), 400

            if len(full_name) > 140:
                return jsonify({
                    "success": False,
                    "message": "Full name cannot exceed 140 characters"
                }), 400

            teacher.full_name = full_name

        if "email" in data:
            email = str(
                data.get("email", "") or ""
            ).strip().lower()

            if not email or "@" not in email or len(email) > 160:
                return jsonify({
                    "success": False,
                    "message": "Enter a valid email address"
                }), 400

            duplicate_email = (
                User.query
                .filter(
                    func.lower(User.email) == email,
                    User.id != user.id
                )
                .first()
            )

            if duplicate_email:
                return jsonify({
                    "success": False,
                    "message": "Email already exists"
                }), 409

            user.email = email

        if "phone" in data:
            phone = str(
                data.get("phone", "") or ""
            ).strip()

            if len(phone) > 20:
                return jsonify({
                    "success": False,
                    "message": "Phone number cannot exceed 20 characters"
                }), 400

            teacher.phone = phone or None

        if "gender" in data:
            gender = str(
                data.get("gender", "") or ""
            ).strip()

            if len(gender) > 20:
                return jsonify({
                    "success": False,
                    "message": "Gender value is too long"
                }), 400

            teacher.gender = gender or None

        if "dob" in data:
            dob_value = str(
                data.get("dob", "") or ""
            ).strip()

            teacher_dob = (
                parse_date(dob_value)
                if dob_value
                else None
            )

            if teacher_dob and teacher_dob > date.today():
                return jsonify({
                    "success": False,
                    "message": "Date of birth cannot be in the future"
                }), 400

            teacher.dob = teacher_dob

        if "blood_group" in data:
            blood_group = str(
                data.get("blood_group", "") or ""
            ).strip().upper()

            if len(blood_group) > 10:
                return jsonify({
                    "success": False,
                    "message": "Blood group value is too long"
                }), 400

            teacher.blood_group = blood_group or None

        if "address" in data:
            address = str(
                data.get("address", "") or ""
            ).strip()

            teacher.address = address or None

        if "qualification" in data:
            qualification = str(
                data.get("qualification", "") or ""
            ).strip()

            if len(qualification) > 140:
                return jsonify({
                    "success": False,
                    "message": "Qualification cannot exceed 140 characters"
                }), 400

            teacher.qualification = qualification or None

        photo = request.files.get("photo")

        if photo and photo.filename:
            extension = (
                photo.filename
                .rsplit(".", 1)[-1]
                .lower()
                if "." in photo.filename
                else ""
            )

            if extension not in {"png", "jpg", "jpeg", "webp"}:
                return jsonify({
                    "success": False,
                    "message": "Only PNG, JPG, JPEG and WEBP photos are allowed"
                }), 400

            photo.stream.seek(0, os.SEEK_END)
            photo_size = photo.stream.tell()
            photo.stream.seek(0)

            if photo_size > 5 * 1024 * 1024:
                return jsonify({
                    "success": False,
                    "message": "Profile photo must be 5 MB or smaller"
                }), 400

            teacher.photo_url = save_teacher_photo(
                photo,
                user.id
            )

        db.session.commit()

        write_audit_log(
            action="SELF_PROFILE_UPDATE",
            entity_id=teacher.id,
            details=(
                f"Teacher updated own profile: "
                f"{teacher.full_name} ({teacher.teacher_code})"
            )
        )

        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "user": user.to_dict(),
                "teacher": teacher.to_dict(),
            }
        }), 200

    except ValueError:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Invalid date. Use YYYY-MM-DD."
        }), 400

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to update Teacher profile",
            "error": str(error)
        }), 500


def calculate_performance_percentage(records):

    earned_marks = 0.0
    maximum_marks = 0.0


    for record in records:

        if (
            record.score is None
            or record.max_score is None
        ):
            continue


        maximum = float(record.max_score)

        if maximum <= 0:
            continue


        earned_marks += float(record.score)
        maximum_marks += maximum


    if maximum_marks == 0:
        return None


    return round(
        (earned_marks / maximum_marks) * 100,
        2
    )


@bp.get("/me/dashboard")
@jwt_required()
def get_teacher_dashboard():

    try:

        user, teacher, error_response = (
            get_logged_in_teacher()
        )


        if error_response:
            return error_response


        today = date.today()
        today_name = today.strftime("%A")


        # ----------------------------------------------------
        # ASSIGNED SUBJECTS AND CLASS SCHEDULE
        # ----------------------------------------------------

        assigned_subjects = (
            Subject.query
            .filter_by(
                teacher_id=teacher.id
            )
            .order_by(
                Subject.name.asc()
            )
            .all()
        )


        weekly_classes_count = (
            Timetable.query
            .filter_by(
                teacher_id=teacher.id
            )
            .count()
        )


        today_schedule = (
            Timetable.query
            .filter(
                Timetable.teacher_id == teacher.id,
                func.lower(Timetable.day_of_week)
                == today_name.lower()
            )
            .order_by(
                Timetable.start_time.asc()
            )
            .all()
        )


        # ----------------------------------------------------
        # OWN FACULTY ATTENDANCE
        # ----------------------------------------------------

        # Use the same automatic attendance rules as the
        # Teacher Attendance, HOD and Performance endpoints.
        # This excludes Sundays/holidays and treats an
        # unmarked working day as absent.
        from .faculty_attendance import (
            get_individual_attendance_data,
            get_non_working_reason,
        )


        attendance_data = get_individual_attendance_data(
            faculty_user_id=user.id,
            department_id=teacher.department_id,
            teacher_id=teacher.id
        )


        attendance_summary_data = attendance_data["summary"]
        attendance_history = attendance_data["records"]


        today_attendance_record = (
            FacultyAttendance.query
            .filter_by(
                faculty_user_id=user.id,
                date=today
            )
            .first()
        )


        today_non_working_reason = get_non_working_reason(
            today,
            teacher.department_id
        )


        if today_non_working_reason:

            today_attendance = {
                "id": None,
                "date": today.isoformat(),
                "status": "holiday",
                "remarks": today_non_working_reason,
                "non_working_reason": today_non_working_reason,
                "inferred": True
            }


        elif today_attendance_record:

            today_attendance = (
                today_attendance_record.to_dict()
            )

            today_attendance["inferred"] = False


        else:

            today_attendance = {
                "id": None,
                "date": today.isoformat(),
                "status": "pending",
                "remarks": "Attendance not marked yet",
                "non_working_reason": None,
                "inferred": True
            }


        # ----------------------------------------------------
        # LEAVE REQUESTS
        # ----------------------------------------------------

        recent_leaves = (
            LeaveRequest.query
            .filter_by(
                teacher_id=teacher.id
            )
            .order_by(
                LeaveRequest.created_at.desc()
            )
            .limit(5)
            .all()
        )


        pending_leave_count = (
            LeaveRequest.query
            .filter(
                LeaveRequest.teacher_id == teacher.id,
                func.lower(LeaveRequest.status) == "pending"
            )
            .count()
        )


        # ----------------------------------------------------
        # PERFORMANCE
        # ----------------------------------------------------

        performance_records = (
            PerformanceRecord.query
            .filter_by(
                user_id=user.id
            )
            .order_by(
                PerformanceRecord.created_at.desc()
            )
            .limit(10)
            .all()
        )


        performance_percentage = (
            calculate_performance_percentage(
                performance_records
            )
        )


        # ----------------------------------------------------
        # NOTIFICATIONS AND NOTICE BOARD
        # ----------------------------------------------------

        notifications = (
            Notification.query
            .filter_by(
                user_id=user.id
            )
            .order_by(
                Notification.created_at.desc()
            )
            .limit(8)
            .all()
        )


        unread_notification_count = (
            Notification.query
            .filter_by(
                user_id=user.id,
                is_read=False
            )
            .count()
        )


        notice_candidates = (
            Notice.query
            .filter(
                func.lower(Notice.status) == "published",
                func.lower(Notice.audience).in_([
                    "all",
                    "teacher"
                ]),
                or_(
                    Notice.expiry_date.is_(None),
                    Notice.expiry_date >= today
                )
            )
            .order_by(
                Notice.created_at.desc()
            )
            .all()
        )


        notices = []


        for notice in notice_candidates:

            include_notice = False


            if notice.created_by is None:
                include_notice = True


            else:

                creator = db.session.get(
                    User,
                    notice.created_by
                )


                creator_role = str(
                    creator.role if creator else ""
                ).strip().lower()


                if creator_role == "admin":
                    include_notice = True


                elif creator_role == "hod":

                    creator_hod = (
                        Hod.query
                        .filter_by(
                            user_id=notice.created_by
                        )
                        .first()
                    )


                    include_notice = bool(
                        creator_hod
                        and creator_hod.department_id
                        == teacher.department_id
                    )


            if include_notice:
                notices.append(notice)


            if len(notices) == 8:
                break


        # ----------------------------------------------------
        # ACADEMIC CALENDAR
        # Global events + teacher's department events only.
        # ----------------------------------------------------

        academic_events = (
            AcademicEvent.query
            .filter(
                or_(
                    AcademicEvent.department_id.is_(None),
                    AcademicEvent.department_id
                    == teacher.department_id
                ),
                or_(
                    AcademicEvent.start_date >= today,
                    AcademicEvent.end_date >= today
                )
            )
            .order_by(
                AcademicEvent.start_date.asc(),
                AcademicEvent.id.asc()
            )
            .limit(10)
            .all()
        )


        face_registered = (
            FaceEncoding.query
            .filter_by(
                user_id=user.id
            )
            .first()
            is not None
        )


        return jsonify({

            "success": True,

            "data": {

                "generated_at": datetime.utcnow().isoformat(),

                "today": {
                    "date": today.isoformat(),
                    "day": today_name
                },

                "user": user.to_dict(),

                "teacher": teacher.to_dict(),

                "stats": {
                    "today_classes": len(today_schedule),
                    "weekly_classes": weekly_classes_count,
                    "assigned_subjects": len(assigned_subjects),
                    "pending_leave_requests": pending_leave_count,
                    "unread_notifications": unread_notification_count,
                    "performance_percentage": performance_percentage,
                    "attendance_percentage": (
                        attendance_summary_data[
                            "attendance_percentage"
                        ]
                    )
                },

                "subjects": [
                    subject.to_dict()
                    for subject in assigned_subjects
                ],

                "today_schedule": [
                    entry.to_dict()
                    for entry in today_schedule
                ],

                "today_attendance": today_attendance,

                "attendance_summary": {
                    "from_date": (
                        attendance_history[-1]["date"]
                        if attendance_history
                        else None
                    ),
                    "to_date": today.isoformat(),
                    "marked_days": (
                        attendance_summary_data["working_days"]
                    ),
                    "recorded_records": (
                        attendance_summary_data["recorded_records"]
                    ),
                    "working_days": (
                        attendance_summary_data["working_days"]
                    ),
                    "present": attendance_summary_data["present"],
                    "absent": attendance_summary_data["absent"],
                    "leave": attendance_summary_data["leave"],
                    "inferred_absent": (
                        attendance_summary_data["inferred_absent"]
                    ),
                    "percentage": (
                        attendance_summary_data[
                            "attendance_percentage"
                        ]
                    )
                },

                "attendance_history": attendance_history,

                "performance": {
                    "percentage": performance_percentage,
                    "records": [
                        record.to_dict()
                        for record in performance_records
                    ]
                },

                "recent_leaves": [
                    leave.to_dict()
                    for leave in recent_leaves
                ],

                "notifications": [
                    notification.to_dict()
                    for notification in notifications
                ],

                "notices": [
                    notice.to_dict()
                    for notice in notices
                ],

                "academic_events": [
                    event.to_dict()
                    for event in academic_events
                ],

                "face_registered": face_registered
            }

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message": "Unable to load teacher dashboard",

            "error": str(error)

        }), 500


# ============================================================
# TEACHER TIMETABLE
#
# GET /api/teachers/me/timetable
#
# Read-only endpoint for the logged-in Teacher Panel. Existing
# Admin/HOD timetable create, update and delete routes remain
# completely separate and unchanged.
# ============================================================

@bp.get("/me/timetable")
@jwt_required()
def get_teacher_timetable():

    try:

        user, teacher, error_response = (
            get_logged_in_teacher()
        )


        if error_response:
            return error_response


        today = date.today()
        now = datetime.now()
        today_name = today.strftime("%A")


        timetable_entries = (
            Timetable.query
            .filter_by(
                teacher_id=teacher.id
            )
            .all()
        )


        day_order = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }


        timetable_entries.sort(
            key=lambda entry: (
                day_order.get(
                    str(entry.day_of_week or "")
                    .strip()
                    .lower(),
                    7
                ),
                entry.start_time,
                entry.id
            )
        )


        def serialize_entry(entry):

            item = entry.to_dict()


            start_datetime = datetime.combine(
                today,
                entry.start_time
            )


            end_datetime = datetime.combine(
                today,
                entry.end_time
            )


            duration_minutes = max(
                0,
                int(
                    (
                        end_datetime
                        - start_datetime
                    ).total_seconds()
                    // 60
                )
            )


            entry_day = str(
                entry.day_of_week or ""
            ).strip().lower()


            if entry_day != today_name.lower():
                status = "scheduled"

            elif now.time() >= entry.end_time:
                status = "completed"

            elif (
                entry.start_time
                <= now.time()
                < entry.end_time
            ):
                status = "current"

            else:
                status = "upcoming"


            item["duration_minutes"] = duration_minutes
            item["status"] = status


            return item


        serialized_entries = [
            serialize_entry(entry)
            for entry in timetable_entries
        ]


        today_schedule = [
            item
            for item in serialized_entries
            if str(item.get("day_of_week") or "")
            .strip()
            .lower() == today_name.lower()
        ]


        completed_classes = sum(
            1
            for item in today_schedule
            if item["status"] == "completed"
        )


        remaining_classes = sum(
            1
            for item in today_schedule
            if item["status"] in {
                "current",
                "upcoming"
            }
        )


        teaching_minutes = sum(
            item["duration_minutes"]
            for item in today_schedule
        )


        current_class = next(
            (
                item
                for item in today_schedule
                if item["status"] == "current"
            ),
            None
        )


        weekly_schedule = {
            day: []
            for day in (
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday"
            )
        }


        for item in serialized_entries:

            day_key = str(
                item.get("day_of_week") or ""
            ).strip().lower()


            weekly_schedule.setdefault(
                day_key,
                []
            ).append(item)


        unique_subject_ids = {
            item["subject_id"]
            for item in serialized_entries
            if item.get("subject_id") is not None
        }


        weekly_minutes = sum(
            item["duration_minutes"]
            for item in serialized_entries
        )


        return jsonify({

            "success": True,

            "data": {

                "generated_at": now.isoformat(),

                "today": {
                    "date": today.isoformat(),
                    "day": today_name
                },

                "user": user.to_dict(),

                "teacher": teacher.to_dict(),

                "stats": {
                    "today_classes": len(today_schedule),
                    "completed_classes": completed_classes,
                    "remaining_classes": remaining_classes,
                    "today_teaching_minutes": teaching_minutes,
                    "today_teaching_hours": round(
                        teaching_minutes / 60,
                        2
                    ),
                    "weekly_classes": len(serialized_entries),
                    "weekly_teaching_minutes": weekly_minutes,
                    "weekly_teaching_hours": round(
                        weekly_minutes / 60,
                        2
                    ),
                    "assigned_subjects": len(
                        unique_subject_ids
                    )
                },

                "current_class": current_class,

                "today_schedule": today_schedule,

                "weekly_schedule": weekly_schedule,

                "schedule": serialized_entries
            }

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message": (
                "Unable to load teacher timetable"
            ),

            "error": str(error)

        }), 500
