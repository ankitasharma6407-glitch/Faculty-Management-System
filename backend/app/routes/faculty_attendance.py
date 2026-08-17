from datetime import datetime
import math

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)

from ..extensions import db
from ..models import (
    FacultyAttendance,
    FaceEncoding,
    Hod,
    Teacher,
    User,
)


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "faculty_attendance",
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
# GET ALL FACULTY ATTENDANCE
# ADMIN ATTENDANCE REPORT
# ============================================================

@bp.get("")
def get_faculty_attendance():

    try:

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
        # OWN DEPARTMENT + TEACHERS ONLY
        # ----------------------------------------------------

        query = (
            FacultyAttendance.query
            .join(
                User,
                FacultyAttendance.faculty_user_id
                == User.id
            )
            .filter(
                FacultyAttendance.department_id
                == hod.department_id,
                User.role == "teacher"
            )
        )


        # ----------------------------------------------------
        # APPLY FILTERS
        # ----------------------------------------------------

        if status:

            query = query.filter(
                FacultyAttendance.status
                == status
            )


        if exact_date:

            query = query.filter(
                FacultyAttendance.date
                == exact_date
            )


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


        records = (
            query
            .order_by(
                FacultyAttendance.date.desc(),
                FacultyAttendance.id.desc()
            )
            .all()
        )


        # ----------------------------------------------------
        # SEARCH FILTER
        # ----------------------------------------------------

        data = []


        for attendance in records:

            item = attendance.to_dict()


            if search:

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
                    search
                    not in searchable_text
                ):

                    continue


            data.append(
                item
            )


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        summary = {

            "total":
                len(data),

            "present":
                sum(
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
                ),

            "absent":
                sum(
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
                ),

            "leave":
                sum(
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