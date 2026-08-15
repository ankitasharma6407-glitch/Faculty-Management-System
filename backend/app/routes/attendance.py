from datetime import datetime

from flask import Blueprint, jsonify, request

from ..models import FacultyAttendance


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "faculty_attendance",
    __name__,
    url_prefix="/api/faculty-attendance"
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

    except ValueError:
        return None


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
                FacultyAttendance.status == status
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
                        "department_id must be an integer."
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


        if from_date_value and not from_date:

            return jsonify({
                "success": False,
                "message": (
                    "Invalid from_date. "
                    "Use YYYY-MM-DD."
                )
            }), 400


        if to_date_value and not to_date:

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
                    "from_date cannot be after to_date."
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
        # ROLE FILTER
        # Teacher / HOD only
        # ----------------------------------------------------

        records = query.order_by(
            FacultyAttendance.date.desc(),
            FacultyAttendance.id.desc()
        ).all()


        data = []


        for attendance in records:

            item = attendance.to_dict()


            # -----------------------------------------------
            # ROLE FILTER
            # -----------------------------------------------

            if role:

                if role not in (
                    "teacher",
                    "hod"
                ):

                    return jsonify({
                        "success": False,
                        "message": (
                            "Role must be teacher or hod."
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


            # -----------------------------------------------
            # SEARCH FILTER
            # Faculty name / code / department
            # -----------------------------------------------

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

                "total": total_records,

                "present": present_records,

                "absent": absent_records,

                "leave": leave_records
            }

        }), 200


    except Exception as error:

        return jsonify({
            "success": False,
            "message": (
                "Unable to load faculty attendance."
            ),
            "error": str(error)
        }), 500


# ============================================================
# GET SINGLE ATTENDANCE RECORD
# ============================================================

@bp.get("/<int:attendance_id>")
def get_single_attendance(
    attendance_id
):

    try:

        attendance = (
            FacultyAttendance.query
            .get(attendance_id)
        )


        if not attendance:

            return jsonify({
                "success": False,
                "message": (
                    "Attendance record not found."
                )
            }), 404


        return jsonify({

            "success": True,

            "data": attendance.to_dict()

        }), 200


    except Exception as error:

        return jsonify({
            "success": False,
            "message": (
                "Unable to load attendance record."
            ),
            "error": str(error)
        }), 500