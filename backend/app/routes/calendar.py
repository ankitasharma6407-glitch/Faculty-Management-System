from datetime import datetime, date

from flask import Blueprint, jsonify, request

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

from ..extensions import db

from ..models import (
    AcademicEvent,
    Department,
    User,
    Hod,
    Teacher,
)


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "calendar",
    __name__,
    url_prefix="/api/academic-events"
)


# ============================================================
# HELPERS
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


def get_json_data():

    return request.get_json(
        silent=True
    ) or {}


def get_event_status(event):

    today = date.today()

    start_date = event.start_date

    end_date = (
        event.end_date
        if event.end_date
        else event.start_date
    )


    if start_date > today:
        return "upcoming"


    if start_date <= today <= end_date:
        return "ongoing"


    return "completed"


def event_to_dict(event):

    item = event.to_dict()

    item["status"] = get_event_status(
        event
    )

    department = None

    if event.department_id:

        department = db.session.get(
            Department,
            event.department_id
        )

    item["department"] = (
        department.name
        if department
        else "All Departments"
    )

    return item

# ============================================================
# GET DEPARTMENTS FOR CALENDAR
# ============================================================

@bp.get("/departments")
def get_calendar_departments():

    try:

        departments = (
            Department.query
            .order_by(
                Department.name.asc()
            )
            .all()
        )

        return jsonify({

            "success": True,

            "data": [
                {
                    "id": department.id,
                    "name": department.name,
                    "code": department.code
                }
                for department in departments
            ]

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load departments.",

            "error":
                str(error)

        }), 500

# ============================================================
# GET ALL ACADEMIC EVENTS
# ============================================================

@bp.get("")
def get_academic_events():

    try:

        event_type = (
            request.args
            .get("event_type", "")
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
            .lower()
        )

        from_date = (
            request.args
            .get("from_date", "")
            .strip()
        )

        to_date = (
            request.args
            .get("to_date", "")
            .strip()
        )


        query = AcademicEvent.query


        # ====================================================
        # EVENT TYPE FILTER
        # ====================================================

        if event_type:

            query = query.filter(
                AcademicEvent.event_type == event_type
            )


        # ====================================================
        # DEPARTMENT FILTER
        # ====================================================

        if department_id:

            try:

                department_id = int(
                    department_id
                )

            except ValueError:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid department_id."

                }), 400


            query = query.filter(
                AcademicEvent.department_id ==
                department_id
            )


        # ====================================================
        # FROM DATE
        # ====================================================

        if from_date:

            parsed_from_date = parse_date(
                from_date
            )


            if not parsed_from_date:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid from_date. Use YYYY-MM-DD."

                }), 400


            query = query.filter(
                AcademicEvent.start_date >=
                parsed_from_date
            )


        # ====================================================
        # TO DATE
        # ====================================================

        if to_date:

            parsed_to_date = parse_date(
                to_date
            )


            if not parsed_to_date:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid to_date. Use YYYY-MM-DD."

                }), 400


            query = query.filter(
                AcademicEvent.start_date <=
                parsed_to_date
            )


        # ====================================================
        # GET EVENTS
        # ====================================================

        events = (
            query
            .order_by(
                AcademicEvent.start_date.asc(),
                AcademicEvent.id.asc()
            )
            .all()
        )


        data = []


        for event in events:

            item = event_to_dict(
                event
            )


            if search:

                searchable_text = " ".join([
                    str(
                        item.get(
                            "title",
                            ""
                        ) or ""
                    ),
                    str(
                        item.get(
                            "description",
                            ""
                        ) or ""
                    ),
                    str(
                        item.get(
                            "event_type",
                            ""
                        ) or ""
                    ),
                    str(
                        item.get(
                            "status",
                            ""
                        ) or ""
                    ),
                ]).lower()


                if search not in searchable_text:
                    continue


            data.append(
                item
            )


        # ====================================================
        # SUMMARY
        # ====================================================

        total = len(data)

        upcoming = sum(
            1
            for item in data
            if item.get("status") == "upcoming"
        )

        ongoing = sum(
            1
            for item in data
            if item.get("status") == "ongoing"
        )

        completed = sum(
            1
            for item in data
            if item.get("status") == "completed"
        )


        return jsonify({

            "success": True,

            "data": data,

            "summary": {
                "total": total,
                "upcoming": upcoming,
                "ongoing": ongoing,
                "completed": completed,
            }

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load academic events.",

            "error":
                str(error)

        }), 500


# ============================================================
# GET SINGLE EVENT
# ============================================================

@bp.get("/<int:event_id>")
def get_academic_event(event_id):

    try:

        event = db.session.get(
            AcademicEvent,
            event_id
        )


        if not event:

            return jsonify({

                "success": False,

                "message":
                    "Academic event not found."

            }), 404


        return jsonify({

            "success": True,

            "data":
                event_to_dict(event)

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load academic event.",

            "error":
                str(error)

        }), 500


# ============================================================
# CREATE EVENT
# ============================================================

@bp.post("")
def create_academic_event():

    try:

        data = get_json_data()


        title = str(
            data.get(
                "title",
                ""
            ) or ""
        ).strip()


        description = str(
            data.get(
                "description",
                ""
            ) or ""
        ).strip()


        event_type = str(
            data.get(
                "event_type",
                "event"
            ) or "event"
        ).strip().lower()


        start_date_value = str(
            data.get(
                "start_date",
                ""
            ) or ""
        ).strip()


        end_date_value = str(
            data.get(
                "end_date",
                ""
            ) or ""
        ).strip()


        department_id = data.get(
            "department_id"
        )


        created_by = data.get(
            "created_by"
        )


        # ====================================================
        # TITLE
        # ====================================================

        if not title:

            return jsonify({

                "success": False,

                "message":
                    "Event title is required."

            }), 400


        # ====================================================
        # START DATE
        # ====================================================

        if not start_date_value:

            return jsonify({

                "success": False,

                "message":
                    "Start date is required."

            }), 400


        start_date = parse_date(
            start_date_value
        )


        if not start_date:

            return jsonify({

                "success": False,

                "message":
                    "Invalid start_date. Use YYYY-MM-DD."

            }), 400


        # ====================================================
        # END DATE
        # ====================================================

        end_date = None


        if end_date_value:

            end_date = parse_date(
                end_date_value
            )


            if not end_date:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid end_date. Use YYYY-MM-DD."

                }), 400


            if end_date < start_date:

                return jsonify({

                    "success": False,

                    "message":
                        "End date cannot be before start date."

                }), 400


        # ====================================================
        # DEPARTMENT ID
        # ====================================================

        if department_id in (
            "",
            None
        ):

            department_id = None


        else:

            try:

                department_id = int(
                    department_id
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "department_id must be a valid number."

                }), 400


        # ====================================================
        # CREATED BY
        # ====================================================

        if created_by in (
            "",
            None
        ):

            created_by = None


        else:

            try:

                created_by = int(
                    created_by
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "created_by must be a valid user ID."

                }), 400


        # ====================================================
        # CREATE
        # ====================================================

        event = AcademicEvent(
            title=title,
            description=description,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            created_by=created_by,
        )


        db.session.add(
            event
        )


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Academic event created successfully.",

            "data":
                event_to_dict(event)

        }), 201


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to create academic event.",

            "error":
                str(error)

        }), 500


# ============================================================
# UPDATE EVENT
# ============================================================

@bp.put("/<int:event_id>")
def update_academic_event(event_id):

    try:

        event = db.session.get(
            AcademicEvent,
            event_id
        )


        if not event:

            return jsonify({

                "success": False,

                "message":
                    "Academic event not found."

            }), 404


        data = get_json_data()


        # ====================================================
        # TITLE
        # ====================================================

        if "title" in data:

            title = str(
                data.get(
                    "title",
                    ""
                ) or ""
            ).strip()


            if not title:

                return jsonify({

                    "success": False,

                    "message":
                        "Event title cannot be empty."

                }), 400


            event.title = title


        # ====================================================
        # DESCRIPTION
        # ====================================================

        if "description" in data:

            event.description = str(
                data.get(
                    "description",
                    ""
                ) or ""
            ).strip()


        # ====================================================
        # EVENT TYPE
        # ====================================================

        if "event_type" in data:

            event.event_type = str(
                data.get(
                    "event_type",
                    "event"
                ) or "event"
            ).strip().lower()


        # ====================================================
        # START DATE
        # ====================================================

        if "start_date" in data:

            start_date_value = str(
                data.get(
                    "start_date",
                    ""
                ) or ""
            ).strip()


            start_date = parse_date(
                start_date_value
            )


            if not start_date:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid start_date. Use YYYY-MM-DD."

                }), 400


            event.start_date = start_date


        # ====================================================
        # END DATE
        # ====================================================

        if "end_date" in data:

            end_date_value = str(
                data.get(
                    "end_date",
                    ""
                ) or ""
            ).strip()


            if not end_date_value:

                event.end_date = None


            else:

                end_date = parse_date(
                    end_date_value
                )


                if not end_date:

                    return jsonify({

                        "success": False,

                        "message":
                            "Invalid end_date. Use YYYY-MM-DD."

                    }), 400


                event.end_date = end_date


        # ====================================================
        # DATE VALIDATION
        # ====================================================

        if (
            event.end_date
            and event.end_date <
            event.start_date
        ):

            return jsonify({

                "success": False,

                "message":
                    "End date cannot be before start date."

            }), 400


        # ====================================================
        # DEPARTMENT
        # ====================================================

        if "department_id" in data:

            department_id = data.get(
                "department_id"
            )


            if department_id in (
                "",
                None
            ):

                event.department_id = None


            else:

                try:

                    event.department_id = int(
                        department_id
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return jsonify({

                        "success": False,

                        "message":
                            "department_id must be a valid number."

                    }), 400


        # ====================================================
        # CREATED BY
        # ====================================================

        if "created_by" in data:

            created_by = data.get(
                "created_by"
            )


            if created_by in (
                "",
                None
            ):

                event.created_by = None


            else:

                try:

                    event.created_by = int(
                        created_by
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return jsonify({

                        "success": False,

                        "message":
                            "created_by must be a valid user ID."

                    }), 400


        # ====================================================
        # SAVE
        # ====================================================

        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Academic event updated successfully.",

            "data":
                event_to_dict(event)

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to update academic event.",

            "error":
                str(error)

        }), 500


# ============================================================
# DELETE EVENT
# ============================================================

@bp.delete("/<int:event_id>")
def delete_academic_event(event_id):

    try:

        event = db.session.get(
            AcademicEvent,
            event_id
        )


        if not event:

            return jsonify({

                "success": False,

                "message":
                    "Academic event not found."

            }), 404


        db.session.delete(
            event
        )


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Academic event deleted successfully."

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to delete academic event.",

            "error":
                str(error)

        }), 500


# ============================================================
# TEACHER CALENDAR HELPER
# ============================================================

def get_current_teacher_for_calendar():

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
                "message": "No department is assigned to this Teacher"
            }),
            403
        )

    return user, teacher, None


# ============================================================
# TEACHER - GET ACADEMIC EVENTS
#
# GET /api/academic-events/teacher/me
#
# Teacher can see:
# 1. Global events (department_id = None)
# 2. Events from the Teacher's own department
# ============================================================

@bp.get("/teacher/me")
@jwt_required()
def get_teacher_academic_events():

    try:

        user, teacher, error_response = (
            get_current_teacher_for_calendar()
        )

        if error_response:
            return error_response

        event_type = (
            request.args
            .get("event_type", "")
            .strip()
            .lower()
        )

        search = (
            request.args
            .get("search", "")
            .strip()
            .lower()
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

        query = (
            AcademicEvent.query
            .filter(
                (
                    AcademicEvent.department_id
                    == teacher.department_id
                )
                |
                AcademicEvent.department_id.is_(None)
            )
        )

        if event_type:
            query = query.filter(
                AcademicEvent.event_type == event_type
            )

        if from_date_value:
            parsed_from_date = parse_date(from_date_value)

            if not parsed_from_date:
                return jsonify({
                    "success": False,
                    "message": "Invalid from_date. Use YYYY-MM-DD."
                }), 400

            query = query.filter(
                AcademicEvent.start_date >= parsed_from_date
            )

        if to_date_value:
            parsed_to_date = parse_date(to_date_value)

            if not parsed_to_date:
                return jsonify({
                    "success": False,
                    "message": "Invalid to_date. Use YYYY-MM-DD."
                }), 400

            query = query.filter(
                AcademicEvent.start_date <= parsed_to_date
            )

        events = (
            query
            .order_by(
                AcademicEvent.start_date.asc(),
                AcademicEvent.id.asc()
            )
            .all()
        )

        data = []

        for event in events:
            item = event_to_dict(event)

            if search:
                searchable_text = " ".join([
                    str(item.get("title", "") or ""),
                    str(item.get("description", "") or ""),
                    str(item.get("event_type", "") or ""),
                    str(item.get("status", "") or ""),
                    str(item.get("department", "") or ""),
                ]).lower()

                if search not in searchable_text:
                    continue

            item["scope"] = (
                "global"
                if event.department_id is None
                else "department"
            )
            item["can_edit"] = False
            item["can_delete"] = False
            data.append(item)

        summary = {
            "total": len(data),
            "upcoming": sum(
                1 for item in data
                if item.get("status") == "upcoming"
            ),
            "ongoing": sum(
                1 for item in data
                if item.get("status") == "ongoing"
            ),
            "completed": sum(
                1 for item in data
                if item.get("status") == "completed"
            ),
            "global_events": sum(
                1 for item in data
                if item.get("scope") == "global"
            ),
            "department_events": sum(
                1 for item in data
                if item.get("scope") == "department"
            ),
        }

        return jsonify({
            "success": True,
            "teacher": {
                "id": teacher.id,
                "teacher_code": teacher.teacher_code,
                "full_name": teacher.full_name,
                "department_id": teacher.department_id,
                "department": (
                    teacher.department.name
                    if teacher.department
                    else None
                ),
            },
            "summary": summary,
            "data": data,
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Unable to load Teacher academic events.",
            "error": str(error)
        }), 500


# ============================================================
# HOD CALENDAR HELPER
# ============================================================

def get_current_hod_for_calendar():

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
# HOD - GET ACADEMIC EVENTS
#
# GET /api/academic-events/hod
#
# HOD can see:
# 1. Global events (department_id = None)
# 2. Own department events
# ============================================================

@bp.get("/hod")
@jwt_required()
def get_hod_academic_events():

    try:

        user, hod, error_response = (
            get_current_hod_for_calendar()
        )


        if error_response:
            return error_response


        event_type = (
            request.args
            .get("event_type", "")
            .strip()
            .lower()
        )


        search = (
            request.args
            .get("search", "")
            .strip()
            .lower()
        )


        from_date = (
            request.args
            .get("from_date", "")
            .strip()
        )


        to_date = (
            request.args
            .get("to_date", "")
            .strip()
        )


        # ====================================================
        # BASE QUERY
        #
        # Global events OR own department events
        # ====================================================

        query = (
            AcademicEvent.query
            .filter(
                (
                    AcademicEvent.department_id
                    == hod.department_id
                )
                |
                (
                    AcademicEvent.department_id
                    .is_(None)
                )
            )
        )


        # ====================================================
        # EVENT TYPE FILTER
        # ====================================================

        if event_type:

            query = query.filter(
                AcademicEvent.event_type
                == event_type
            )


        # ====================================================
        # FROM DATE
        # ====================================================

        if from_date:

            parsed_from_date = parse_date(
                from_date
            )


            if not parsed_from_date:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid from_date. Use YYYY-MM-DD."
                }), 400


            query = query.filter(
                AcademicEvent.start_date
                >= parsed_from_date
            )


        # ====================================================
        # TO DATE
        # ====================================================

        if to_date:

            parsed_to_date = parse_date(
                to_date
            )


            if not parsed_to_date:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid to_date. Use YYYY-MM-DD."
                }), 400


            query = query.filter(
                AcademicEvent.start_date
                <= parsed_to_date
            )


        # ====================================================
        # GET EVENTS
        # ====================================================

        events = (
            query
            .order_by(
                AcademicEvent.start_date.asc(),
                AcademicEvent.id.asc()
            )
            .all()
        )


        data = []


        for event in events:

            item = event_to_dict(
                event
            )


            # =================================================
            # SEARCH
            # =================================================

            if search:

                searchable_text = " ".join([
                    str(
                        item.get(
                            "title",
                            ""
                        ) or ""
                    ),
                    str(
                        item.get(
                            "description",
                            ""
                        ) or ""
                    ),
                    str(
                        item.get(
                            "event_type",
                            ""
                        ) or ""
                    ),
                    str(
                        item.get(
                            "status",
                            ""
                        ) or ""
                    ),
                    str(
                        item.get(
                            "department",
                            ""
                        ) or ""
                    ),
                ]).lower()


                if search not in searchable_text:
                    continue


            # =================================================
            # HOD OWNERSHIP INFO
            # =================================================

            is_own = (
                event.created_by
                == user.id
            )


            item["is_own"] = is_own

            item["can_edit"] = is_own

            item["can_delete"] = is_own


            item["scope"] = (
                "global"
                if event.department_id is None
                else "department"
            )


            data.append(
                item
            )


        # ====================================================
        # SUMMARY
        # ====================================================

        total = len(data)


        upcoming = sum(
            1
            for item in data
            if item.get("status")
            == "upcoming"
        )


        ongoing = sum(
            1
            for item in data
            if item.get("status")
            == "ongoing"
        )


        completed = sum(
            1
            for item in data
            if item.get("status")
            == "completed"
        )


        created_by_me = sum(
            1
            for item in data
            if item.get("is_own")
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

            "summary": {
                "total":
                    total,

                "upcoming":
                    upcoming,

                "ongoing":
                    ongoing,

                "completed":
                    completed,

                "created_by_me":
                    created_by_me
            },

            "data":
                data

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load HOD academic events.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - CREATE ACADEMIC EVENT
#
# POST /api/academic-events/hod
# ============================================================

@bp.post("/hod")
@jwt_required()
def create_hod_academic_event():

    try:

        user, hod, error_response = (
            get_current_hod_for_calendar()
        )

        if error_response:
            return error_response


        data = get_json_data()


        # ====================================================
        # VALUES
        # ====================================================

        title = str(
            data.get(
                "title",
                ""
            ) or ""
        ).strip()


        description = str(
            data.get(
                "description",
                ""
            ) or ""
        ).strip()


        event_type = str(
            data.get(
                "event_type",
                "event"
            ) or "event"
        ).strip().lower()


        start_date_value = str(
            data.get(
                "start_date",
                ""
            ) or ""
        ).strip()


        end_date_value = str(
            data.get(
                "end_date",
                ""
            ) or ""
        ).strip()


        # ====================================================
        # TITLE
        # ====================================================

        if not title:

            return jsonify({
                "success": False,
                "message":
                    "Event title is required."
            }), 400


        # ====================================================
        # START DATE
        # ====================================================

        if not start_date_value:

            return jsonify({
                "success": False,
                "message":
                    "Start date is required."
            }), 400


        start_date = parse_date(
            start_date_value
        )


        if not start_date:

            return jsonify({
                "success": False,
                "message":
                    "Invalid start_date. Use YYYY-MM-DD."
            }), 400


        # ====================================================
        # END DATE
        # ====================================================

        end_date = None


        if end_date_value:

            end_date = parse_date(
                end_date_value
            )


            if not end_date:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid end_date. Use YYYY-MM-DD."
                }), 400


            if end_date < start_date:

                return jsonify({
                    "success": False,
                    "message":
                        "End date cannot be before start date."
                }), 400


        # ====================================================
        # IMPORTANT SECURITY
        #
        # department_id and created_by are NOT taken
        # from frontend.
        #
        # They come from logged-in HOD.
        # ====================================================

        event = AcademicEvent(

            title=title,

            description=description,

            event_type=event_type,

            start_date=start_date,

            end_date=end_date,

            department_id=
                hod.department_id,

            created_by=
                user.id
        )


        db.session.add(
            event
        )

        db.session.commit()


        item = event_to_dict(
            event
        )


        item["is_own"] = True
        item["can_edit"] = True
        item["can_delete"] = True
        item["scope"] = "department"


        return jsonify({

            "success": True,

            "message":
                "HOD academic event created successfully.",

            "department_id":
                hod.department_id,

            "department":
                (
                    hod.department.name
                    if hod.department
                    else None
                ),

            "data":
                item

        }), 201


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to create HOD academic event.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - UPDATE OWN ACADEMIC EVENT
#
# PATCH /api/academic-events/hod/<event_id>
# ============================================================

@bp.patch("/hod/<int:event_id>")
@jwt_required()
def update_hod_academic_event(event_id):

    try:

        user, hod, error_response = (
            get_current_hod_for_calendar()
        )

        if error_response:
            return error_response


        event = db.session.get(
            AcademicEvent,
            event_id
        )


        if not event:

            return jsonify({
                "success": False,
                "message":
                    "Academic event not found."
            }), 404


        # HOD can update only own event
        if event.created_by != user.id:

            return jsonify({
                "success": False,
                "message":
                    "You can only update events created by you."
            }), 403


        if event.department_id != hod.department_id:

            return jsonify({
                "success": False,
                "message":
                    "You cannot update events from another department."
            }), 403


        data = get_json_data()


        if not data:

            return jsonify({
                "success": False,
                "message":
                    "No event data provided."
            }), 400


        if "title" in data:

            title = str(
                data.get(
                    "title",
                    ""
                ) or ""
            ).strip()

            if not title:

                return jsonify({
                    "success": False,
                    "message":
                        "Event title cannot be empty."
                }), 400

            event.title = title


        if "description" in data:

            event.description = str(
                data.get(
                    "description",
                    ""
                ) or ""
            ).strip()


        if "event_type" in data:

            event.event_type = str(
                data.get(
                    "event_type",
                    "event"
                ) or "event"
            ).strip().lower()


        if "start_date" in data:

            start_date_value = str(
                data.get(
                    "start_date",
                    ""
                ) or ""
            ).strip()

            start_date = parse_date(
                start_date_value
            )

            if not start_date:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid start_date. Use YYYY-MM-DD."
                }), 400

            event.start_date = start_date


        if "end_date" in data:

            end_date_value = str(
                data.get(
                    "end_date",
                    ""
                ) or ""
            ).strip()

            if not end_date_value:

                event.end_date = None

            else:

                end_date = parse_date(
                    end_date_value
                )

                if not end_date:

                    return jsonify({
                        "success": False,
                        "message":
                            "Invalid end_date. Use YYYY-MM-DD."
                    }), 400

                event.end_date = end_date


        if (
            event.end_date
            and
            event.end_date
            < event.start_date
        ):

            return jsonify({
                "success": False,
                "message":
                    "End date cannot be before start date."
            }), 400


        db.session.commit()


        item = event_to_dict(
            event
        )

        item["is_own"] = True
        item["can_edit"] = True
        item["can_delete"] = True
        item["scope"] = "department"


        return jsonify({

            "success": True,

            "message":
                "HOD academic event updated successfully.",

            "data":
                item

        }), 200


    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                "Unable to update HOD academic event.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - DELETE OWN ACADEMIC EVENT
#
# DELETE /api/academic-events/hod/<event_id>
# ============================================================

@bp.delete("/hod/<int:event_id>")
@jwt_required()
def delete_hod_academic_event(event_id):

    try:

        user, hod, error_response = (
            get_current_hod_for_calendar()
        )

        if error_response:
            return error_response


        event = db.session.get(
            AcademicEvent,
            event_id
        )


        if not event:

            return jsonify({
                "success": False,
                "message":
                    "Academic event not found."
            }), 404


        # HOD can delete only own event
        if event.created_by != user.id:

            return jsonify({
                "success": False,
                "message":
                    "You can only delete events created by you."
            }), 403


        # Extra department protection
        if event.department_id != hod.department_id:

            return jsonify({
                "success": False,
                "message":
                    "You cannot delete events from another department."
            }), 403


        db.session.delete(
            event
        )

        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "HOD academic event deleted successfully."

        }), 200


    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                "Unable to delete HOD academic event.",

            "error":
                str(error)

        }), 500
