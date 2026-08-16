from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

import os
from datetime import datetime

from ..extensions import db

from ..models import (
    User,
    Hod,
    Teacher,
    Student,
    AuditLog,
    PerformanceRecord,
    Subject,
    FacultyAttendance,
    LeaveRequest,
)

# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "hod",
    __name__,
    url_prefix="/api/hods"
)


# ============================================================
# HELPER - CLEAN TEXT
# ============================================================

def clean_text(value):

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


# ============================================================
# HELPER - INTEGER
# ============================================================

def parse_int(
    value,
    default=None
):

    value = clean_text(value)

    if value is None:
        return default

    return int(value)


# ============================================================
# HELPER - FLOAT
# ============================================================

def parse_float(
    value,
    default=None
):

    value = clean_text(value)

    if value is None:
        return default

    return float(value)


# ============================================================
# HELPER - DATE
# ============================================================

def parse_date(value):

    value = clean_text(value)

    if value is None:
        return None

    return datetime.strptime(
        value,
        "%Y-%m-%d"
    ).date()


# ============================================================
# HELPER - SAVE HOD PHOTO
# ============================================================

def save_hod_photo(
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
        "hods"
    )


    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    filename = secure_filename(
        photo.filename
    )


    if not filename:

        return None


    filename = (
        f"{user_id}_{filename}"
    )


    photo_path = os.path.join(
        upload_folder,
        filename
    )


    photo.save(
        photo_path
    )


    return (
        f"/uploads/hods/{filename}"
    )


# ============================================================
# AUDIT LOG HELPER
# ============================================================

def write_audit_log(
    action,
    entity,
    entity_id=None,
    details=None
):

    try:

        ip_address = (
            request.headers.get(
                "X-Forwarded-For",
                request.remote_addr
            )
        )


        if (
            ip_address
            and "," in ip_address
        ):

            ip_address = (
                ip_address
                .split(",")[0]
                .strip()
            )


        audit = AuditLog(

            user_id=None,

            action=action,

            entity=entity,

            entity_id=entity_id,

            details=details,

            ip_address=ip_address
        )


        db.session.add(
            audit
        )


        db.session.commit()


    except Exception as error:

        db.session.rollback()


        print(
            "Audit Log Error:",
            error
        )


# ============================================================
# HOD DASHBOARD
# ============================================================

@bp.get("/dashboard")
@jwt_required()
def get_hod_dashboard():

    try:

        # ----------------------------------------------------
        # GET CURRENT JWT USER ID
        # ----------------------------------------------------

        identity = (
            get_jwt_identity()
        )


        try:

            user_id = int(
                identity
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({

                "success": False,

                "message":
                    "Invalid login session"

            }), 401


        # ----------------------------------------------------
        # GET CURRENT USER
        # ----------------------------------------------------

        user = db.session.get(
            User,
            user_id
        )


        if not user:

            return jsonify({

                "success": False,

                "message":
                    "User not found"

            }), 404


        # ----------------------------------------------------
        # ROLE CHECK
        # ----------------------------------------------------

        user_role = (
            str(
                user.role
                or ""
            )
            .strip()
            .lower()
        )


        if user_role != "hod":

            return jsonify({

                "success": False,

                "message":
                    "HOD access required"

            }), 403


        # ----------------------------------------------------
        # ACTIVE ACCOUNT CHECK
        # ----------------------------------------------------

        if not user.is_active:

            return jsonify({

                "success": False,

                "message":
                    "HOD account is inactive"

            }), 403


        # ----------------------------------------------------
        # GET HOD PROFILE
        # ----------------------------------------------------

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

                "message":
                    "HOD profile not found"

            }), 404


        # ----------------------------------------------------
        # HOD DEPARTMENT
        # ----------------------------------------------------

        department_id = (
            hod.department_id
        )


        # ----------------------------------------------------
        # NO DEPARTMENT ASSIGNED
        # ----------------------------------------------------

        if not department_id:

            return jsonify({

                "success": True,

                "data": {

                    "hod":
                        hod.to_dict(),

                    "department_id":
                        None,

                    "department":
                        None,

                    "total_teachers":
                        0,

                    "total_students":
                        0,

                    "total_departments":
                        0
                }

            }), 200


        # ----------------------------------------------------
        # TEACHERS IN HOD DEPARTMENT
        # ----------------------------------------------------

        total_teachers = (

            Teacher.query

            .filter(
                Teacher.department_id
                == department_id
            )

            .count()
        )


        # ----------------------------------------------------
        # STUDENTS IN HOD DEPARTMENT
        # ----------------------------------------------------

        total_students = (

            Student.query

            .filter(
                Student.department_id
                == department_id
            )

            .count()
        )


        # ----------------------------------------------------
        # DEPARTMENT NAME
        # ----------------------------------------------------

        department_name = (

            hod.department.name

            if hod.department

            else None
        )


        # ----------------------------------------------------
        # SUCCESS RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "data": {

                "hod":
                    hod.to_dict(),

                "department_id":
                    department_id,

                "department":
                    department_name,

                "total_teachers":
                    total_teachers,

                "total_students":
                    total_students,

                "total_departments":
                    1
            }

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load HOD dashboard.",

            "error":
                str(error)

        }), 500

# ============================================================
# HOD - GET OWN DEPARTMENT TEACHERS
# ============================================================

@bp.get("/teachers")
@jwt_required()
def get_hod_department_teachers():

    try:

        # ----------------------------------------------------
        # CURRENT USER
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # ROLE CHECK
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # ACTIVE ACCOUNT CHECK
        # ----------------------------------------------------

        if not user.is_active:

            return jsonify({
                "success": False,
                "message": "HOD account is inactive"
            }), 403


        # ----------------------------------------------------
        # HOD PROFILE
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # NO DEPARTMENT ASSIGNED
        # ----------------------------------------------------

        if not hod.department_id:

            return jsonify({
                "success": True,
                "department_id": None,
                "department": None,
                "total": 0,
                "data": []
            }), 200


        # ----------------------------------------------------
        # OWN DEPARTMENT TEACHERS ONLY
        # ----------------------------------------------------

        teachers = (
            Teacher.query
            .filter(
                Teacher.department_id
                == hod.department_id
            )
            .order_by(
                Teacher.full_name.asc()
            )
            .all()
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

            "total":
                len(teachers),

            "data": [
                teacher.to_dict()
                for teacher in teachers
            ]

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load department teachers.",

            "error":
                str(error)

        }), 500


# # ============================================================
# # HOD - ADD TEACHER TO OWN DEPARTMENT
# # ============================================================

# @bp.post("/teachers")
# @jwt_required()
# def add_hod_department_teacher():

#     try:
#         # ----------------------------------------------------
#         # CURRENT LOGGED-IN USER
#         # ----------------------------------------------------

#         identity = get_jwt_identity()

#         try:
#             user_id = int(identity)

#         except (TypeError, ValueError):
#             return jsonify({
#                 "success": False,
#                 "message": "Invalid login session"
#             }), 401


#         current_user = db.session.get(
#             User,
#             user_id
#         )


#         if not current_user:
#             return jsonify({
#                 "success": False,
#                 "message": "User not found"
#             }), 404


#         if (
#             str(current_user.role or "")
#             .strip()
#             .lower()
#             != "hod"
#         ):
#             return jsonify({
#                 "success": False,
#                 "message": "HOD access required"
#             }), 403


#         if not current_user.is_active:
#             return jsonify({
#                 "success": False,
#                 "message": "HOD account is inactive"
#             }), 403


#         # ----------------------------------------------------
#         # HOD PROFILE
#         # ----------------------------------------------------

#         hod = (
#             Hod.query
#             .filter_by(user_id=current_user.id)
#             .first()
#         )


#         if not hod:
#             return jsonify({
#                 "success": False,
#                 "message": "HOD profile not found"
#             }), 404


#         if not hod.department_id:
#             return jsonify({
#                 "success": False,
#                 "message": "No department is assigned to this HOD"
#             }), 403


#         # Supports JSON and FormData
#         data = (
#             request.form
#             if request.form
#             else request.get_json(silent=True) or {}
#         )


#         teacher_code = clean_text(
#             data.get("teacher_code")
#             or data.get("teacher_id")
#         )

#         full_name = clean_text(
#             data.get("full_name")
#         )

#         email = clean_text(
#             data.get("email")
#         )

#         username = clean_text(
#             data.get("username")
#         )

#         password = data.get("password")

#         phone = clean_text(
#             data.get("phone")
#         )

#         designation = clean_text(
#             data.get("designation")
#         )

#         qualification = clean_text(
#             data.get("qualification")
#         )

#         joining_date_value = clean_text(
#             data.get("joining_date")
#         )

#         status = (
#             clean_text(data.get("status"))
#             or "active"
#         ).lower()


#         # ----------------------------------------------------
#         # REQUIRED FIELDS
#         # ----------------------------------------------------

#         if not all([
#             teacher_code,
#             full_name,
#             email,
#             username,
#             password
#         ]):
#             return jsonify({
#                 "success": False,
#                 "message": (
#                     "Teacher ID, full name, email, "
#                     "username and password are required"
#                 )
#             }), 400


#         if status not in ("active", "inactive"):
#             return jsonify({
#                 "success": False,
#                 "message": "Status must be active or inactive"
#             }), 400


#         # ----------------------------------------------------
#         # DUPLICATE CHECKS
#         # ----------------------------------------------------

#         if User.query.filter_by(username=username).first():
#             return jsonify({
#                 "success": False,
#                 "message": "Username already exists"
#             }), 409


#         if User.query.filter_by(email=email).first():
#             return jsonify({
#                 "success": False,
#                 "message": "Email already exists"
#             }), 409


#         if Teacher.query.filter_by(
#             teacher_code=teacher_code
#         ).first():
#             return jsonify({
#                 "success": False,
#                 "message": "Teacher ID already exists"
#             }), 409


#         joining_date = (
#             parse_date(joining_date_value)
#             if joining_date_value
#             else None
#         )


#         # ----------------------------------------------------
#         # CREATE TEACHER LOGIN ACCOUNT
#         # ----------------------------------------------------

#         teacher_user = User(
#             username=username,
#             email=email,
#             role="teacher",
#             is_active=(status == "active")
#         )

#         teacher_user.set_password(
#             password
#         )

#         db.session.add(
#             teacher_user
#         )

#         db.session.flush()


#         # ----------------------------------------------------
#         # CREATE TEACHER PROFILE
#         # Department is automatically taken from logged-in HOD
#         # ----------------------------------------------------

#         teacher = Teacher(
#             user_id=teacher_user.id,
#             teacher_code=teacher_code,
#             full_name=full_name,
#             phone=phone,
#             department_id=hod.department_id,
#             designation=designation,
#             qualification=qualification,
#             joining_date=joining_date,
#             status=status
#         )


#         db.session.add(
#             teacher
#         )

#         db.session.commit()


#         write_audit_log(
#             action="CREATE",
#             entity="teacher",
#             entity_id=teacher.id,
#             details=(
#                 f"HOD {hod.full_name} added teacher "
#                 f"{teacher.full_name} "
#                 f"({teacher.teacher_code})"
#             )
#         )


#         return jsonify({
#             "success": True,
#             "message": "Teacher added successfully",
#             "data": teacher.to_dict()
#         }), 201


#     except ValueError as error:

#         db.session.rollback()

#         return jsonify({
#             "success": False,
#             "message": f"Invalid data: {str(error)}"
#         }), 400


#     except Exception as error:

#         db.session.rollback()

#         return jsonify({
#             "success": False,
#             "message": "Unable to add teacher",
#             "error": str(error)
#         }), 500



# ============================================================
# HOD - GET SINGLE TEACHER OF OWN DEPARTMENT
# ============================================================

@bp.get("/teachers/<int:teacher_id>")
@jwt_required()
def get_hod_department_teacher(
    teacher_id
):

    try:

        # ----------------------------------------------------
        # CURRENT USER
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # ROLE CHECK
        # ----------------------------------------------------

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


        if not user.is_active:

            return jsonify({
                "success": False,
                "message": "HOD account is inactive"
            }), 403


        # ----------------------------------------------------
        # HOD PROFILE
        # ----------------------------------------------------

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
                "message":
                    "No department is assigned to this HOD"
            }), 403


        # ----------------------------------------------------
        # TEACHER
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
        # DEPARTMENT SECURITY CHECK
        # ----------------------------------------------------

        if (
            teacher.department_id
            != hod.department_id
        ):

            return jsonify({
                "success": False,
                "message":
                    "You cannot access teachers from another department"
            }), 403


        return jsonify({

            "success": True,

            "data":
                teacher.to_dict()

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load teacher details.",

            "error":
                str(error)

        }), 500

# ============================================================
# HOD - GET OWN DEPARTMENT STUDENTS
# ============================================================

@bp.get("/students")
@jwt_required()
def get_hod_department_students():

    try:

        # ----------------------------------------------------
        # CURRENT LOGGED IN USER
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # HOD ROLE CHECK
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # ACTIVE ACCOUNT CHECK
        # ----------------------------------------------------

        if not user.is_active:

            return jsonify({
                "success": False,
                "message": "HOD account is inactive"
            }), 403


        # ----------------------------------------------------
        # HOD PROFILE
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # NO DEPARTMENT ASSIGNED
        # ----------------------------------------------------

        if not hod.department_id:

            return jsonify({
                "success": True,
                "department_id": None,
                "department": None,
                "total": 0,
                "data": []
            }), 200


        # ----------------------------------------------------
        # OWN DEPARTMENT STUDENTS ONLY
        # ----------------------------------------------------

        students = (
            Student.query
            .filter(
                Student.department_id
                == hod.department_id
            )
            .order_by(
                Student.full_name.asc()
            )
            .all()
        )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

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

            "total":
                len(students),

            "data": [
                student.to_dict()
                for student in students
            ]

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load department students.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - GET SINGLE STUDENT OF OWN DEPARTMENT
# ============================================================

@bp.get("/students/<int:student_id>")
@jwt_required()
def get_hod_department_student(
    student_id
):

    try:

        # ----------------------------------------------------
        # CURRENT LOGGED IN USER
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # HOD ROLE CHECK
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # ACTIVE ACCOUNT CHECK
        # ----------------------------------------------------

        if not user.is_active:

            return jsonify({
                "success": False,
                "message": "HOD account is inactive"
            }), 403


        # ----------------------------------------------------
        # HOD PROFILE
        # ----------------------------------------------------

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
                "message":
                    "No department is assigned to this HOD"
            }), 403


        # ----------------------------------------------------
        # GET STUDENT
        # ----------------------------------------------------

        student = db.session.get(
            Student,
            student_id
        )


        if not student:

            return jsonify({
                "success": False,
                "message": "Student not found"
            }), 404


        # ----------------------------------------------------
        # DEPARTMENT SECURITY CHECK
        # ----------------------------------------------------

        if (
            student.department_id
            != hod.department_id
        ):

            return jsonify({
                "success": False,
                "message":
                    "You cannot access students from another department"
            }), 403


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "data":
                student.to_dict()

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load student details.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD PERFORMANCE HELPERS
# ============================================================

def get_logged_in_hod_for_performance():

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
                "message":
                    "No department is assigned to this HOD"
            }),
            403
        )


    return user, hod, None


# ============================================================
# HOD - DEPARTMENT REPORT SUMMARY
#
# GET /api/hods/reports/summary
# ============================================================

@bp.get("/reports/summary")
@jwt_required()
def get_hod_report_summary():

    try:

        user, hod, error_response = (
            get_logged_in_hod_for_performance()
        )

        if error_response:
            return error_response


        department_id = (
            hod.department_id
        )


        # ====================================================
        # TEACHERS
        # ====================================================

        teachers = (
            Teacher.query
            .filter(
                Teacher.department_id
                == department_id
            )
            .all()
        )


        teacher_ids = [
            teacher.id
            for teacher in teachers
        ]


        teacher_user_ids = [
            teacher.user_id
            for teacher in teachers
            if teacher.user_id
        ]


        total_teachers = len(
            teachers
        )


        # ====================================================
        # STUDENTS
        # ====================================================

        total_students = (
            Student.query
            .filter(
                Student.department_id
                == department_id
            )
            .count()
        )


        # ====================================================
        # FACULTY ATTENDANCE
        # ====================================================

        if teacher_user_ids:

            attendance_records = (
                FacultyAttendance.query
                .filter(
                    FacultyAttendance.department_id
                    == department_id,
                    FacultyAttendance.faculty_user_id
                    .in_(teacher_user_ids)
                )
                .all()
            )

        else:

            attendance_records = []


        attendance_total = len(
            attendance_records
        )


        attendance_present = sum(
            1
            for record
            in attendance_records
            if (
                str(
                    record.status or ""
                ).lower()
                == "present"
            )
        )


        attendance_absent = sum(
            1
            for record
            in attendance_records
            if (
                str(
                    record.status or ""
                ).lower()
                == "absent"
            )
        )


        attendance_leave = sum(
            1
            for record
            in attendance_records
            if (
                str(
                    record.status or ""
                ).lower()
                == "leave"
            )
        )


        attendance_percentage = (

            round(
                (
                    attendance_present
                    / attendance_total
                )
                * 100,
                1
            )

            if attendance_total > 0

            else 0
        )


        # ====================================================
        # PERFORMANCE
        # ====================================================

        if teacher_user_ids:

            performance_records = (
                PerformanceRecord.query
                .filter(
                    PerformanceRecord.user_id
                    .in_(teacher_user_ids)
                )
                .all()
            )

        else:

            performance_records = []


        performance_total = len(
            performance_records
        )


        excellent = 0
        good = 0
        average = 0
        poor = 0

        performance_percentages = []


        for record in performance_records:

            percentage, band = (
                calculate_hod_performance_band(
                    record.score,
                    record.max_score
                )
            )


            performance_percentages.append(
                percentage
            )


            if band == "Excellent":

                excellent += 1

            elif band == "Good":

                good += 1

            elif band == "Average":

                average += 1

            else:

                poor += 1


        average_performance = (

            round(
                sum(
                    performance_percentages
                )
                / len(
                    performance_percentages
                ),
                1
            )

            if performance_percentages

            else 0
        )


        # ====================================================
        # LEAVE REQUESTS
        # ====================================================

        if teacher_ids:

            leave_requests = (
                LeaveRequest.query
                .filter(
                    LeaveRequest.teacher_id
                    .in_(teacher_ids)
                )
                .all()
            )

        else:

            leave_requests = []


        leave_total = len(
            leave_requests
        )


        leave_pending = sum(
            1
            for leave
            in leave_requests
            if (
                str(
                    leave.status or ""
                ).lower()
                == "pending"
            )
        )


        leave_approved = sum(
            1
            for leave
            in leave_requests
            if (
                str(
                    leave.status or ""
                ).lower()
                == "approved"
            )
        )


        leave_rejected = sum(
            1
            for leave
            in leave_requests
            if (
                str(
                    leave.status or ""
                ).lower()
                == "rejected"
            )
        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "department_id":
                department_id,

            "department":
                (
                    hod.department.name
                    if hod.department
                    else None
                ),

            "faculty": {

                "total_teachers":
                    total_teachers,

                "total_students":
                    total_students
            },

            "attendance": {

                "total":
                    attendance_total,

                "present":
                    attendance_present,

                "absent":
                    attendance_absent,

                "leave":
                    attendance_leave,

                "attendance_percentage":
                    attendance_percentage
            },

            "performance": {

                "total_records":
                    performance_total,

                "average_percentage":
                    average_performance,

                "excellent":
                    excellent,

                "good":
                    good,

                "average":
                    average,

                "poor":
                    poor
            },

            "leave_requests": {

                "total":
                    leave_total,

                "pending":
                    leave_pending,

                "approved":
                    leave_approved,

                "rejected":
                    leave_rejected
            }

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to generate HOD report summary.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - DEPARTMENT ANALYTICS
#
# GET /api/hods/analytics
# ============================================================

@bp.get("/analytics")
@jwt_required()
def get_hod_department_analytics():

    try:

        user, hod, error_response = (
            get_logged_in_hod_for_performance()
        )


        if error_response:

            return error_response


        department_id = (
            hod.department_id
        )


        # ====================================================
        # DEPARTMENT TEACHERS
        # ====================================================

        teachers = (
            Teacher.query
            .filter(
                Teacher.department_id
                == department_id
            )
            .order_by(
                Teacher.full_name.asc()
            )
            .all()
        )


        teacher_ids = [
            teacher.id
            for teacher in teachers
        ]


        teacher_user_ids = [
            teacher.user_id
            for teacher in teachers
            if teacher.user_id
        ]


        teacher_by_user_id = {

            teacher.user_id:
                teacher

            for teacher in teachers

            if teacher.user_id
        }


        # ====================================================
        # STUDENTS
        # ====================================================

        total_students = (
            Student.query
            .filter(
                Student.department_id
                == department_id
            )
            .count()
        )


        # ====================================================
        # ATTENDANCE RECORDS
        # ====================================================

        if teacher_user_ids:

            attendance_records = (
                FacultyAttendance.query
                .filter(
                    FacultyAttendance.department_id
                    == department_id,
                    FacultyAttendance.faculty_user_id
                    .in_(teacher_user_ids)
                )
                .order_by(
                    FacultyAttendance.date.asc()
                )
                .all()
            )

        else:

            attendance_records = []


        # ====================================================
        # ATTENDANCE TOTALS
        # ====================================================

        attendance_total = len(
            attendance_records
        )


        attendance_present = sum(

            1

            for record
            in attendance_records

            if (
                str(
                    record.status or ""
                )
                .strip()
                .lower()
                == "present"
            )
        )


        attendance_absent = sum(

            1

            for record
            in attendance_records

            if (
                str(
                    record.status or ""
                )
                .strip()
                .lower()
                == "absent"
            )
        )


        attendance_leave = sum(

            1

            for record
            in attendance_records

            if (
                str(
                    record.status or ""
                )
                .strip()
                .lower()
                == "leave"
            )
        )


        attendance_percentage = (

            round(
                (
                    attendance_present
                    / attendance_total
                )
                * 100,
                1
            )

            if attendance_total > 0

            else 0
        )


        # ====================================================
        # ATTENDANCE TREND BY DATE
        #
        # Example:
        # [
        #   {
        #     "date": "2026-08-15",
        #     "present": 1,
        #     "absent": 0,
        #     "leave": 0,
        #     "total": 1
        #   }
        # ]
        # ====================================================

        attendance_date_map = {}


        for record in attendance_records:

            if not record.date:

                continue


            date_key = (
                record.date.isoformat()
            )


            if (
                date_key
                not in attendance_date_map
            ):

                attendance_date_map[
                    date_key
                ] = {

                    "date":
                        date_key,

                    "present":
                        0,

                    "absent":
                        0,

                    "leave":
                        0,

                    "total":
                        0
                }


            status = (
                str(
                    record.status or ""
                )
                .strip()
                .lower()
            )


            attendance_date_map[
                date_key
            ]["total"] += 1


            if status == "present":

                attendance_date_map[
                    date_key
                ]["present"] += 1


            elif status == "absent":

                attendance_date_map[
                    date_key
                ]["absent"] += 1


            elif status == "leave":

                attendance_date_map[
                    date_key
                ]["leave"] += 1


        attendance_trend = [

            attendance_date_map[
                date_key
            ]

            for date_key
            in sorted(
                attendance_date_map.keys()
            )
        ]


        # ====================================================
        # PERFORMANCE RECORDS
        # ====================================================

        if teacher_user_ids:

            performance_records = (
                PerformanceRecord.query
                .filter(
                    PerformanceRecord.user_id
                    .in_(teacher_user_ids)
                )
                .order_by(
                    PerformanceRecord.id.asc()
                )
                .all()
            )

        else:

            performance_records = []


        # ====================================================
        # PERFORMANCE DISTRIBUTION
        # ====================================================

        excellent = 0
        good = 0
        average = 0
        poor = 0

        all_performance_percentages = []


        # Stores percentages teacher-wise
        teacher_performance_map = {}


        for record in performance_records:

            percentage, band = (
                calculate_hod_performance_band(
                    record.score,
                    record.max_score
                )
            )


            all_performance_percentages.append(
                percentage
            )


            # -----------------------------------------------
            # BAND COUNT
            # -----------------------------------------------

            if band == "Excellent":

                excellent += 1

            elif band == "Good":

                good += 1

            elif band == "Average":

                average += 1

            else:

                poor += 1


            # -----------------------------------------------
            # TEACHER-WISE DATA
            # -----------------------------------------------

            if (
                record.user_id
                not in teacher_performance_map
            ):

                teacher = (
                    teacher_by_user_id
                    .get(
                        record.user_id
                    )
                )


                teacher_performance_map[
                    record.user_id
                ] = {

                    "teacher_id":
                        (
                            teacher.id
                            if teacher
                            else None
                        ),

                    "teacher_user_id":
                        record.user_id,

                    "teacher_code":
                        (
                            teacher.teacher_code
                            if teacher
                            else None
                        ),

                    "teacher_name":
                        (
                            teacher.full_name
                            if teacher
                            else None
                        ),

                    "percentages":
                        []
                }


            teacher_performance_map[
                record.user_id
            ]["percentages"].append(
                percentage
            )


        # ====================================================
        # TEACHER-WISE AVERAGE PERFORMANCE
        # ====================================================

        teacher_performance = []


        for (
            teacher_user_id,
            item
        ) in teacher_performance_map.items():

            percentages = (
                item["percentages"]
            )


            average_percentage = (

                round(
                    sum(percentages)
                    / len(percentages),
                    1
                )

                if percentages

                else 0
            )


            _, performance_band = (
                calculate_hod_performance_band(
                    average_percentage,
                    100
                )
            )


            teacher_performance.append({

                "teacher_id":
                    item["teacher_id"],

                "teacher_user_id":
                    teacher_user_id,

                "teacher_code":
                    item["teacher_code"],

                "teacher_name":
                    item["teacher_name"],

                "record_count":
                    len(percentages),

                "average_percentage":
                    average_percentage,

                "band":
                    performance_band
            })


        teacher_performance.sort(

            key=lambda item:
                item.get(
                    "average_percentage",
                    0
                ),

            reverse=True
        )


        # ====================================================
        # OVERALL PERFORMANCE AVERAGE
        # ====================================================

        average_performance = (

            round(
                sum(
                    all_performance_percentages
                )
                / len(
                    all_performance_percentages
                ),
                1
            )

            if all_performance_percentages

            else 0
        )


        # ====================================================
        # LEAVE ANALYTICS
        # ====================================================

        if teacher_ids:

            leave_records = (
                LeaveRequest.query
                .filter(
                    LeaveRequest.teacher_id
                    .in_(teacher_ids)
                )
                .all()
            )

        else:

            leave_records = []


        leave_pending = 0
        leave_approved = 0
        leave_rejected = 0


        for leave in leave_records:

            status = (
                str(
                    leave.status or ""
                )
                .strip()
                .lower()
            )


            if status == "pending":

                leave_pending += 1

            elif status == "approved":

                leave_approved += 1

            elif status == "rejected":

                leave_rejected += 1


        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "department_id":
                department_id,

            "department":
                (
                    hod.department.name
                    if hod.department
                    else None
                ),


            # -----------------------------------------------
            # TOP CARDS
            # -----------------------------------------------

            "summary": {

                "total_teachers":
                    len(teachers),

                "total_students":
                    total_students,

                "attendance_percentage":
                    attendance_percentage,

                "average_performance":
                    average_performance,

                "pending_leave_requests":
                    leave_pending
            },


            # -----------------------------------------------
            # ATTENDANCE CHART
            # -----------------------------------------------

            "attendance": {

                "total":
                    attendance_total,

                "present":
                    attendance_present,

                "absent":
                    attendance_absent,

                "leave":
                    attendance_leave,

                "percentage":
                    attendance_percentage,

                "trend":
                    attendance_trend
            },


            # -----------------------------------------------
            # PERFORMANCE CHARTS
            # -----------------------------------------------

            "performance": {

                "total_records":
                    len(
                        performance_records
                    ),

                "average_percentage":
                    average_performance,

                "distribution": {

                    "excellent":
                        excellent,

                    "good":
                        good,

                    "average":
                        average,

                    "poor":
                        poor
                },

                "teachers":
                    teacher_performance
            },


            # -----------------------------------------------
            # LEAVE CHART
            # -----------------------------------------------

            "leave_requests": {

                "total":
                    len(
                        leave_records
                    ),

                "pending":
                    leave_pending,

                "approved":
                    leave_approved,

                "rejected":
                    leave_rejected
            }

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load HOD analytics.",

            "error":
                str(error)

        }), 500


# ============================================================
# PERFORMANCE PERCENTAGE + BAND
# Same rule used by Admin performance report
# ============================================================

def calculate_hod_performance_band(
    score,
    max_score
):

    try:

        score_value = float(
            score
        )

        max_value = float(
            max_score
        )

    except (
        TypeError,
        ValueError
    ):

        return 0.0, "Poor"


    if max_value <= 0:

        return 0.0, "Poor"


    percentage = (
        score_value
        / max_value
        * 100
    )


    if percentage >= 80:

        band = "Excellent"

    elif percentage >= 60:

        band = "Good"

    elif percentage >= 40:

        band = "Average"

    else:

        band = "Poor"


    return round(
        percentage,
        1
    ), band


# ============================================================
# PERFORMANCE JSON FOR HOD
# ============================================================

def hod_performance_to_dict(
    performance,
    teacher=None
):

    if teacher is None:

        teacher = (
            Teacher.query
            .filter_by(
                user_id=
                    performance.user_id
            )
            .first()
        )


    item = performance.to_dict()


    percentage, band = (
        calculate_hod_performance_band(
            performance.score,
            performance.max_score
        )
    )


    item.update({

        "teacher_id":
            teacher.id
            if teacher
            else None,

        "teacher_user_id":
            teacher.user_id
            if teacher
            else performance.user_id,

        "teacher_code":
            teacher.teacher_code
            if teacher
            else None,

        "teacher_name":
            teacher.full_name
            if teacher
            else None,

        "department_id":
            teacher.department_id
            if teacher
            else None,

        "department":
            (
                teacher.department.name
                if teacher
                and teacher.department
                else None
            ),

        "percentage":
            percentage,

        "band":
            band
    })


    return item


# ============================================================
# HOD - GET OWN DEPARTMENT PERFORMANCE
#
# GET /api/hods/performance
#
# Optional:
# ?teacher_id=1
# ?term=Semester 1
# ?subject_id=2
# ============================================================

@bp.get("/performance")
@jwt_required()
def get_hod_department_performance():

    try:

        user, hod, error_response = (
            get_logged_in_hod_for_performance()
        )


        if error_response:

            return error_response


        teacher_id_value = (
            request.args
            .get(
                "teacher_id",
                ""
            )
            .strip()
        )


        term = (
            request.args
            .get(
                "term",
                ""
            )
            .strip()
        )


        subject_id_value = (
            request.args
            .get(
                "subject_id",
                ""
            )
            .strip()
        )


        # ----------------------------------------------------
        # BASE QUERY
        # Only teachers of HOD department
        # ----------------------------------------------------

        query = (
            db.session
            .query(
                PerformanceRecord,
                Teacher
            )
            .join(
                Teacher,
                PerformanceRecord.user_id
                == Teacher.user_id
            )
            .filter(
                Teacher.department_id
                == hod.department_id
            )
        )


        # ----------------------------------------------------
        # TEACHER FILTER
        # ----------------------------------------------------

        if teacher_id_value:

            try:

                teacher_id = int(
                    teacher_id_value
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message":
                        "teacher_id must be an integer"
                }), 400


            query = query.filter(
                Teacher.id
                == teacher_id
            )


        # ----------------------------------------------------
        # TERM FILTER
        # ----------------------------------------------------

        if term:

            query = query.filter(
                PerformanceRecord.term
                == term
            )


        # ----------------------------------------------------
        # SUBJECT FILTER
        # ----------------------------------------------------

        if subject_id_value:

            try:

                subject_id = int(
                    subject_id_value
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message":
                        "subject_id must be an integer"
                }), 400


            query = query.filter(
                PerformanceRecord.subject_id
                == subject_id
            )


        rows = (
            query
            .order_by(
                PerformanceRecord.id.desc()
            )
            .all()
        )


        data = [

            hod_performance_to_dict(
                performance,
                teacher
            )

            for performance, teacher
            in rows
        ]


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        summary = {

            "total":
                len(data),

            "excellent":
                sum(
                    1
                    for item in data
                    if item.get("band")
                    == "Excellent"
                ),

            "good":
                sum(
                    1
                    for item in data
                    if item.get("band")
                    == "Good"
                ),

            "average":
                sum(
                    1
                    for item in data
                    if item.get("band")
                    == "Average"
                ),

            "poor":
                sum(
                    1
                    for item in data
                    if item.get("band")
                    == "Poor"
                )
        }


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

            "data":
                data

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load department performance.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - ADD TEACHER PERFORMANCE
#
# POST /api/hods/performance
#
# JSON:
# {
#     "teacher_id": 1,
#     "subject_id": null,
#     "term": "Semester 1",
#     "score": 82,
#     "max_score": 100,
#     "grade": "A",
#     "remarks": "Good performance"
# }
# ============================================================

@bp.post("/performance")
@jwt_required()
def add_hod_teacher_performance():

    try:

        user, hod, error_response = (
            get_logged_in_hod_for_performance()
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
        # TEACHER
        # ----------------------------------------------------

        try:

            teacher_id = int(
                data.get(
                    "teacher_id"
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "success": False,
                "message":
                    "Valid teacher_id is required"
            }), 400


        teacher = db.session.get(
            Teacher,
            teacher_id
        )


        if not teacher:

            return jsonify({
                "success": False,
                "message":
                    "Teacher not found"
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
                    "You cannot add performance "
                    "for teachers from another department"
                )
            }), 403


        if not teacher.user_id:

            return jsonify({
                "success": False,
                "message":
                    "Teacher login account not found"
            }), 404


        # ----------------------------------------------------
        # TERM
        # ----------------------------------------------------

        term = clean_text(
            data.get(
                "term"
            )
        )


        if not term:

            return jsonify({
                "success": False,
                "message":
                    "Performance term is required"
            }), 400


        # ----------------------------------------------------
        # SUBJECT
        # Optional
        # ----------------------------------------------------

        subject_id = None


        if (
            data.get("subject_id")
            is not None
            and str(
                data.get("subject_id")
            ).strip()
            != ""
        ):

            try:

                subject_id = int(
                    data.get(
                        "subject_id"
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "subject_id must be an integer"
                }), 400


            subject = db.session.get(
                Subject,
                subject_id
            )


            if not subject:

                return jsonify({
                    "success": False,
                    "message":
                        "Subject not found"
                }), 404


            if (
                subject.department_id
                != hod.department_id
            ):

                return jsonify({
                    "success": False,
                    "message": (
                        "You cannot use a subject "
                        "from another department"
                    )
                }), 403


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        try:

            score = parse_float(
                data.get(
                    "score"
                )
            )

            max_score = parse_float(
                data.get(
                    "max_score"
                ),
                100
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "success": False,
                "message":
                    "Score values must be numeric"
            }), 400


        if score is None:

            return jsonify({
                "success": False,
                "message":
                    "Performance score is required"
            }), 400


        if (
            max_score is None
            or max_score <= 0
        ):

            return jsonify({
                "success": False,
                "message":
                    "max_score must be greater than 0"
            }), 400


        if score < 0:

            return jsonify({
                "success": False,
                "message":
                    "Score cannot be negative"
            }), 400


        if score > max_score:

            return jsonify({
                "success": False,
                "message":
                    "Score cannot exceed max_score"
            }), 400


        # ----------------------------------------------------
        # OPTIONAL VALUES
        # ----------------------------------------------------

        grade = clean_text(
            data.get(
                "grade"
            )
        )


        remarks = clean_text(
            data.get(
                "remarks"
            )
        )


        # ----------------------------------------------------
        # PREVENT SAME PERFORMANCE DUPLICATE
        # Teacher + Subject + Term
        # ----------------------------------------------------

        existing = (
            PerformanceRecord.query
            .filter(
                PerformanceRecord.user_id
                == teacher.user_id,
                PerformanceRecord.subject_id
                == subject_id,
                PerformanceRecord.term
                == term
            )
            .first()
        )


        if existing:

            return jsonify({
                "success": False,
                "message": (
                    "Performance record already exists "
                    "for this teacher, subject and term"
                ),
                "data":
                    hod_performance_to_dict(
                        existing,
                        teacher
                    )
            }), 409


        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        performance = PerformanceRecord(

            user_id=
                teacher.user_id,

            subject_id=
                subject_id,

            term=
                term,

            score=
                score,

            max_score=
                max_score,

            grade=
                grade,

            remarks=
                remarks
        )


        db.session.add(
            performance
        )

        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Teacher performance added successfully",

            "data":
                hod_performance_to_dict(
                    performance,
                    teacher
                )

        }), 201


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to add teacher performance.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - UPDATE TEACHER PERFORMANCE
#
# PATCH /api/hods/performance/<performance_id>
# ============================================================

@bp.patch(
    "/performance/<int:performance_id>"
)
@jwt_required()
def update_hod_teacher_performance(
    performance_id
):

    try:

        user, hod, error_response = (
            get_logged_in_hod_for_performance()
        )


        if error_response:

            return error_response


        performance = db.session.get(
            PerformanceRecord,
            performance_id
        )


        if not performance:

            return jsonify({
                "success": False,
                "message":
                    "Performance record not found"
            }), 404


        # ----------------------------------------------------
        # FIND TEACHER
        # ----------------------------------------------------

        teacher = (
            Teacher.query
            .filter_by(
                user_id=
                    performance.user_id
            )
            .first()
        )


        if not teacher:

            return jsonify({
                "success": False,
                "message":
                    "Teacher profile not found"
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
                    "You cannot update performance "
                    "for teachers from another department"
                )
            }), 403


        data = (
            request.get_json(
                silent=True
            )
            or {}
        )


        if not data:

            return jsonify({
                "success": False,
                "message":
                    "No performance data provided"
            }), 400


        # ----------------------------------------------------
        # SUBJECT
        # ----------------------------------------------------

        new_subject_id = (
            performance.subject_id
        )


        if "subject_id" in data:

            if (
                data.get("subject_id")
                is None
                or str(
                    data.get("subject_id")
                ).strip()
                == ""
            ):

                new_subject_id = None

            else:

                try:

                    new_subject_id = int(
                        data.get(
                            "subject_id"
                        )
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return jsonify({
                        "success": False,
                        "message":
                            "subject_id must be an integer"
                    }), 400


                subject = db.session.get(
                    Subject,
                    new_subject_id
                )


                if not subject:

                    return jsonify({
                        "success": False,
                        "message":
                            "Subject not found"
                    }), 404


                if (
                    subject.department_id
                    != hod.department_id
                ):

                    return jsonify({
                        "success": False,
                        "message": (
                            "You cannot use a subject "
                            "from another department"
                        )
                    }), 403


        # ----------------------------------------------------
        # TERM
        # ----------------------------------------------------

        new_term = (
            performance.term
        )


        if "term" in data:

            new_term = clean_text(
                data.get(
                    "term"
                )
            )


            if not new_term:

                return jsonify({
                    "success": False,
                    "message":
                        "Performance term cannot be empty"
                }), 400


        # ----------------------------------------------------
        # SCORE / MAX SCORE
        # ----------------------------------------------------

        try:

            new_score = (
                parse_float(
                    data.get(
                        "score"
                    )
                )
                if "score" in data
                else float(
                    performance.score
                )
            )


            new_max_score = (
                parse_float(
                    data.get(
                        "max_score"
                    )
                )
                if "max_score" in data
                else float(
                    performance.max_score
                )
            )


        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "success": False,
                "message":
                    "Score values must be numeric"
            }), 400


        if new_score is None:

            return jsonify({
                "success": False,
                "message":
                    "Score cannot be empty"
            }), 400


        if (
            new_max_score is None
            or new_max_score <= 0
        ):

            return jsonify({
                "success": False,
                "message":
                    "max_score must be greater than 0"
            }), 400


        if new_score < 0:

            return jsonify({
                "success": False,
                "message":
                    "Score cannot be negative"
            }), 400


        if (
            new_score
            > new_max_score
        ):

            return jsonify({
                "success": False,
                "message":
                    "Score cannot exceed max_score"
            }), 400


        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------

        duplicate = (
            PerformanceRecord.query
            .filter(
                PerformanceRecord.id
                != performance.id,
                PerformanceRecord.user_id
                == performance.user_id,
                PerformanceRecord.subject_id
                == new_subject_id,
                PerformanceRecord.term
                == new_term
            )
            .first()
        )


        if duplicate:

            return jsonify({
                "success": False,
                "message": (
                    "Another performance record already "
                    "exists for this teacher, subject and term"
                )
            }), 409


        # ----------------------------------------------------
        # APPLY VALUES
        # ----------------------------------------------------

        performance.subject_id = (
            new_subject_id
        )

        performance.term = (
            new_term
        )

        performance.score = (
            new_score
        )

        performance.max_score = (
            new_max_score
        )


        if "grade" in data:

            performance.grade = clean_text(
                data.get(
                    "grade"
                )
            )


        if "remarks" in data:

            performance.remarks = clean_text(
                data.get(
                    "remarks"
                )
            )


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Teacher performance updated successfully",

            "data":
                hod_performance_to_dict(
                    performance,
                    teacher
                )

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to update teacher performance.",

            "error":
                str(error)

        }), 500

# ============================================================
# GET ALL HODS
# ============================================================

@bp.get("")
def get_hods():

    try:

        hods = (

            Hod.query

            .order_by(
                Hod.id.desc()
            )

            .all()
        )


        return jsonify({

            "success": True,

            "data": [

                hod.to_dict()

                for hod in hods
            ]

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load HOD records.",

            "error":
                str(error)

        }), 500


# ============================================================
# GET SINGLE HOD
# ============================================================

@bp.get("/<int:hod_id>")
def get_hod(
    hod_id
):

    try:

        hod = db.session.get(
            Hod,
            hod_id
        )


        if not hod:

            return jsonify({

                "success": False,

                "message":
                    "HOD not found"

            }), 404


        return jsonify({

            "success": True,

            "data":
                hod.to_dict()

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load HOD.",

            "error":
                str(error)

        }), 500


# ============================================================
# ADD HOD
# ============================================================

@bp.post("")
def add_hod():

    data = request.form


    # --------------------------------------------------------
    # BASIC DETAILS
    # --------------------------------------------------------

    hod_code = clean_text(
        data.get(
            "hod_code"
        )
    )


    full_name = clean_text(
        data.get(
            "full_name"
        )
    )


    email = clean_text(
        data.get(
            "email"
        )
    )


    phone = clean_text(
        data.get(
            "phone"
        )
    )


    gender = clean_text(
        data.get(
            "gender"
        )
    )


    qualification = clean_text(
        data.get(
            "qualification"
        )
    )


    address = clean_text(
        data.get(
            "address"
        )
    )


    username = clean_text(
        data.get(
            "username"
        )
    )


    password = data.get(
        "password"
    )


    status = (

        clean_text(
            data.get(
                "status"
            )
        )

        or "active"

    ).lower()


    # --------------------------------------------------------
    # REQUIRED FIELDS
    # --------------------------------------------------------

    if not all([

        hod_code,

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


    # --------------------------------------------------------
    # VALID STATUS
    # --------------------------------------------------------

    if status not in (
        "active",
        "inactive"
    ):

        return jsonify({

            "success": False,

            "message":
                "Status must be active or inactive"

        }), 400


    # --------------------------------------------------------
    # DUPLICATE USERNAME
    # --------------------------------------------------------

    if (
        User.query
        .filter_by(
            username=username
        )
        .first()
    ):

        return jsonify({

            "success": False,

            "message":
                "Username already exists"

        }), 409


    # --------------------------------------------------------
    # DUPLICATE EMAIL
    # --------------------------------------------------------

    if (
        User.query
        .filter_by(
            email=email
        )
        .first()
    ):

        return jsonify({

            "success": False,

            "message":
                "Email already exists"

        }), 409


    # --------------------------------------------------------
    # DUPLICATE HOD ID
    # --------------------------------------------------------

    if (
        Hod.query
        .filter_by(
            hod_code=hod_code
        )
        .first()
    ):

        return jsonify({

            "success": False,

            "message":
                "HOD ID already exists"

        }), 409


    try:

        # ----------------------------------------------------
        # OPTIONAL VALUES
        # ----------------------------------------------------

        department_id = parse_int(

            data.get(
                "department_id"
            ),

            None
        )


        experience_years = parse_int(

            data.get(
                "experience_years"
            ),

            0
        )


        dob = parse_date(
            data.get(
                "dob"
            )
        )


        joining_date = parse_date(
            data.get(
                "joining_date"
            )
        )


        # ----------------------------------------------------
        # CREATE USER ACCOUNT
        # ----------------------------------------------------

        user = User(

            username=
                username,

            email=
                email,

            role=
                "hod",

            is_active=(
                status
                == "active"
            )
        )


        user.set_password(
            password
        )


        db.session.add(
            user
        )


        db.session.flush()


        # ----------------------------------------------------
        # CREATE HOD PROFILE
        # ----------------------------------------------------

        hod = Hod(

            user_id=
                user.id,

            hod_code=
                hod_code,

            full_name=
                full_name,

            phone=
                phone,

            gender=
                gender,

            dob=
                dob,

            address=
                address,

            department_id=
                department_id,

            qualification=
                qualification,

            experience_years=
                experience_years,

            joining_date=
                joining_date,

            status=
                status
        )


        # ----------------------------------------------------
        # OPTIONAL SALARY
        # Only if field exists in model
        # ----------------------------------------------------

        if hasattr(
            Hod,
            "salary"
        ):

            salary = parse_float(
                data.get(
                    "salary"
                ),
                None
            )

            hod.salary = salary


        # ----------------------------------------------------
        # OPTIONAL OFFICE ROOM
        # Only if field exists in model
        # ----------------------------------------------------

        if hasattr(
            Hod,
            "office_room_no"
        ):

            hod.office_room_no = (
                clean_text(
                    data.get(
                        "office_room_no"
                    )
                )
            )


        # ----------------------------------------------------
        # PHOTO
        # ----------------------------------------------------

        photo = request.files.get(
            "photo"
        )


        photo_url = save_hod_photo(
            photo,
            user.id
        )


        if photo_url:

            hod.photo_url = (
                photo_url
            )


        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        db.session.add(
            hod
        )


        db.session.commit()


        # ----------------------------------------------------
        # AUDIT LOG
        # ----------------------------------------------------

        write_audit_log(

            action=
                "CREATE",

            entity=
                "hod",

            entity_id=
                hod.id,

            details=(

                f"HOD added: "

                f"{hod.full_name} "

                f"({hod.hod_code})"
            )
        )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "message":
                "HOD added successfully",

            "data":
                hod.to_dict()

        }), 201


    except ValueError as error:

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

            "message":
                str(error)

        }), 500


# ============================================================
# DELETE HOD
# ============================================================

@bp.delete("/<int:hod_id>")
def delete_hod(
    hod_id
):

    hod = db.session.get(
        Hod,
        hod_id
    )


    if not hod:

        return jsonify({

            "success": False,

            "message":
                "HOD not found"

        }), 404


    try:

        # ----------------------------------------------------
        # SAVE DETAILS BEFORE DELETE
        # ----------------------------------------------------

        deleted_hod_id = (
            hod.id
        )


        deleted_hod_name = (
            hod.full_name
        )


        deleted_hod_code = (
            hod.hod_code
        )


        user = (
            hod.user
        )


        # ----------------------------------------------------
        # DELETE
        # ----------------------------------------------------

        if user:

            # User -> HOD relationship already uses
            # delete-orphan cascade.

            db.session.delete(
                user
            )

        else:

            db.session.delete(
                hod
            )


        db.session.commit()


        # ----------------------------------------------------
        # AUDIT LOG
        # ----------------------------------------------------

        write_audit_log(

            action=
                "DELETE",

            entity=
                "hod",

            entity_id=
                deleted_hod_id,

            details=(

                f"HOD deleted: "

                f"{deleted_hod_name} "

                f"({deleted_hod_code})"
            )
        )


        return jsonify({

            "success": True,

            "message":
                "HOD deleted successfully"

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


# ============================================================
# UPDATE HOD
# ============================================================

@bp.put("/<int:hod_id>")
def update_hod(
    hod_id
):

    hod = db.session.get(
        Hod,
        hod_id
    )


    if not hod:

        return jsonify({

            "success": False,

            "message":
                "HOD not found"

        }), 404


    data = request.form


    try:

        # ----------------------------------------------------
        # FULL NAME
        # ----------------------------------------------------

        if "full_name" in data:

            full_name = clean_text(
                data.get(
                    "full_name"
                )
            )


            if not full_name:

                return jsonify({

                    "success":
                        False,

                    "message":
                        "Full name is required"

                }), 400


            hod.full_name = (
                full_name
            )


        # ----------------------------------------------------
        # PHONE
        # ----------------------------------------------------

        if "phone" in data:

            hod.phone = clean_text(
                data.get(
                    "phone"
                )
            )


        # ----------------------------------------------------
        # GENDER
        # ----------------------------------------------------

        if "gender" in data:

            hod.gender = clean_text(
                data.get(
                    "gender"
                )
            )


        # ----------------------------------------------------
        # ADDRESS
        # ----------------------------------------------------

        if "address" in data:

            hod.address = clean_text(
                data.get(
                    "address"
                )
            )


        # ----------------------------------------------------
        # QUALIFICATION
        # ----------------------------------------------------

        if "qualification" in data:

            hod.qualification = clean_text(
                data.get(
                    "qualification"
                )
            )


        # ----------------------------------------------------
        # EMAIL
        # ----------------------------------------------------

        if (
            "email" in data
            and hod.user
        ):

            email = clean_text(
                data.get(
                    "email"
                )
            )


            if not email:

                return jsonify({

                    "success":
                        False,

                    "message":
                        "Email is required"

                }), 400


            existing_email = (

                User.query

                .filter(
                    User.email == email,
                    User.id != hod.user.id
                )

                .first()
            )


            if existing_email:

                return jsonify({

                    "success":
                        False,

                    "message":
                        "Email already exists"

                }), 409


            hod.user.email = (
                email
            )


        # ----------------------------------------------------
        # USERNAME
        # ----------------------------------------------------

        if (
            "username" in data
            and hod.user
        ):

            username = clean_text(
                data.get(
                    "username"
                )
            )


            if not username:

                return jsonify({

                    "success":
                        False,

                    "message":
                        "Username is required"

                }), 400


            existing_username = (

                User.query

                .filter(
                    User.username
                    == username,

                    User.id
                    != hod.user.id
                )

                .first()
            )


            if existing_username:

                return jsonify({

                    "success":
                        False,

                    "message":
                        "Username already exists"

                }), 409


            hod.user.username = (
                username
            )


        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        password = data.get(
            "password"
        )


        if (
            password
            and hod.user
        ):

            hod.user.set_password(
                password
            )


        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        if "department_id" in data:

            hod.department_id = parse_int(

                data.get(
                    "department_id"
                ),

                None
            )


        # ----------------------------------------------------
        # EXPERIENCE
        # ----------------------------------------------------

        if "experience_years" in data:

            hod.experience_years = parse_int(

                data.get(
                    "experience_years"
                ),

                0
            )


        # ----------------------------------------------------
        # SALARY
        # Only if model has salary
        # ----------------------------------------------------

        if (
            "salary" in data
            and hasattr(
                Hod,
                "salary"
            )
        ):

            hod.salary = parse_float(

                data.get(
                    "salary"
                ),

                None
            )


        # ----------------------------------------------------
        # OFFICE ROOM
        # Only if model has office_room_no
        # ----------------------------------------------------

        if (
            "office_room_no" in data
            and hasattr(
                Hod,
                "office_room_no"
            )
        ):

            hod.office_room_no = (
                clean_text(
                    data.get(
                        "office_room_no"
                    )
                )
            )


        # ----------------------------------------------------
        # DATE OF BIRTH
        # ----------------------------------------------------

        if "dob" in data:

            hod.dob = parse_date(
                data.get(
                    "dob"
                )
            )


        # ----------------------------------------------------
        # JOINING DATE
        # ----------------------------------------------------

        if "joining_date" in data:

            hod.joining_date = parse_date(
                data.get(
                    "joining_date"
                )
            )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if "status" in data:

            status = (

                clean_text(
                    data.get(
                        "status"
                    )
                )

                or "inactive"

            ).lower()


            if status not in (
                "active",
                "inactive"
            ):

                return jsonify({

                    "success":
                        False,

                    "message":
                        "Status must be active or inactive"

                }), 400


            hod.status = (
                status
            )


            if hod.user:

                hod.user.is_active = (
                    status
                    == "active"
                )


        # ----------------------------------------------------
        # PHOTO
        # ----------------------------------------------------

        photo = request.files.get(
            "photo"
        )


        if (
            photo
            and photo.filename
        ):

            photo_url = (
                save_hod_photo(
                    photo,
                    hod.user_id
                )
            )


            if photo_url:

                hod.photo_url = (
                    photo_url
                )


        # ----------------------------------------------------
        # SAVE UPDATE
        # ----------------------------------------------------

        db.session.commit()


        # ----------------------------------------------------
        # AUDIT LOG
        # ----------------------------------------------------

        write_audit_log(

            action=
                "UPDATE",

            entity=
                "hod",

            entity_id=
                hod.id,

            details=(

                f"HOD updated: "

                f"{hod.full_name} "

                f"({hod.hod_code})"
            )
        )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "message":
                "HOD updated successfully",

            "data":
                hod.to_dict()

        }), 200


    except ValueError as error:

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

            "message":
                str(error)

        }), 500
    

# ============================================================
# HOD - GET OWN PROFILE
#
# GET /api/hods/profile
# ============================================================

@bp.get("/profile")
@jwt_required()
def get_hod_own_profile():

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


        if not user.is_active:

            return jsonify({
                "success": False,
                "message": "HOD account is inactive"
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


        profile = hod.to_dict()


        # Account information
        profile["username"] = user.username
        profile["email"] = user.email
        profile["role"] = user.role
        profile["is_active"] = user.is_active


        # Department name
        profile["department"] = (
            hod.department.name
            if hod.department
            else None
        )


        return jsonify({

            "success": True,

            "data": profile

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load HOD profile.",

            "error":
                str(error)

        }), 500    


# ============================================================
# HOD - UPDATE OWN PROFILE
#
# PATCH /api/hods/profile
# ============================================================

@bp.patch("/profile")
@jwt_required()
def update_hod_own_profile():

    try:

        # ====================================================
        # CURRENT USER
        # ====================================================

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


        # ====================================================
        # ROLE CHECK
        # ====================================================

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


        if not user.is_active:

            return jsonify({
                "success": False,
                "message": "HOD account is inactive"
            }), 403


        # ====================================================
        # HOD PROFILE
        # ====================================================

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


        # ====================================================
        # JSON OR FORM DATA
        # ====================================================

        if request.is_json:

            data = (
                request.get_json(
                    silent=True
                )
                or {}
            )

        else:

            data = request.form


        # ====================================================
        # FULL NAME
        # ====================================================

        if "full_name" in data:

            full_name = clean_text(
                data.get(
                    "full_name"
                )
            )

            if not full_name:

                return jsonify({
                    "success": False,
                    "message":
                        "Full name cannot be empty"
                }), 400

            hod.full_name = full_name


        # ====================================================
        # PHONE
        # ====================================================

        if "phone" in data:

            hod.phone = clean_text(
                data.get(
                    "phone"
                )
            )


        # ====================================================
        # GENDER
        # ====================================================

        if "gender" in data:

            hod.gender = clean_text(
                data.get(
                    "gender"
                )
            )


        # ====================================================
        # DATE OF BIRTH
        # ====================================================

        if "dob" in data:

            dob_value = clean_text(
                data.get(
                    "dob"
                )
            )


            if dob_value:

                try:

                    hod.dob = parse_date(
                        dob_value
                    )

                except ValueError:

                    return jsonify({
                        "success": False,
                        "message":
                            "Invalid dob. Use YYYY-MM-DD."
                    }), 400

            else:

                hod.dob = None


        # ====================================================
        # ADDRESS
        # ====================================================

        if "address" in data:

            hod.address = clean_text(
                data.get(
                    "address"
                )
            )


        # ====================================================
        # QUALIFICATION
        # ====================================================

        if "qualification" in data:

            hod.qualification = clean_text(
                data.get(
                    "qualification"
                )
            )


        # ====================================================
        # PHOTO
        # Only works with FormData / multipart request
        # ====================================================

        photo = request.files.get(
            "photo"
        )


        if (
            photo
            and photo.filename
        ):

            photo_url = save_hod_photo(
                photo,
                user.id
            )


            if photo_url:

                hod.photo_url = photo_url


        # ====================================================
        # SAVE
        # ====================================================

        db.session.commit()


        # ====================================================
        # AUDIT LOG
        # ====================================================

        write_audit_log(

            action="UPDATE",

            entity="hod_profile",

            entity_id=hod.id,

            details=(
                f"HOD self profile updated: "
                f"{hod.full_name}"
            )
        )


        # ====================================================
        # RESPONSE
        # ====================================================

        profile = hod.to_dict()

        profile["username"] = user.username
        profile["email"] = user.email
        profile["role"] = user.role
        profile["is_active"] = user.is_active

        profile["department"] = (
            hod.department.name
            if hod.department
            else None
        )


        return jsonify({

            "success": True,

            "message":
                "HOD profile updated successfully.",

            "data":
                profile

        }), 200


    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                "Unable to update HOD profile.",

            "error":
                str(error)

        }), 500
    