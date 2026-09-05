from datetime import datetime

from flask import Blueprint, jsonify, request

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

from ..extensions import db

from ..models import (
    Notice,
    User,
    Hod,
    Teacher,
    Notification,
)

# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "notices",
    __name__,
    url_prefix="/api/notices"
)


# ============================================================
# VALID VALUES
# ============================================================

VALID_CATEGORIES = (
    "general",
    "academic",
    "examination",
    "event",
    "placement",
)

VALID_AUDIENCES = (
    "all",
    "teacher",
    "hod",
    "student",
)

VALID_PRIORITIES = (
    "normal",
    "important",
    "urgent",
)

VALID_STATUSES = (
    "draft",
    "published",
    "archived",
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


# ============================================================
# HELPER - ADMIN NOTICE NOTIFICATIONS
# ============================================================

def create_admin_notice_notifications(
    notice,
    creator
):

    # Only Admin published notices generate notifications
    if not creator:
        return 0

    if (
        str(creator.role or "")
        .strip()
        .lower()
        != "admin"
    ):
        return 0

    if (
        str(notice.status or "")
        .strip()
        .lower()
        != "published"
    ):
        return 0


    audience = (
        str(notice.audience or "all")
        .strip()
        .lower()
    )


    # --------------------------------------------------------
    # TARGET ROLES
    # --------------------------------------------------------

    audience_roles = {

        "all": (
            "hod",
            "teacher",
            "student",
        ),

        "hod": (
            "hod",
        ),

        "teacher": (
            "teacher",
        ),

        "student": (
            "student",
        ),
    }


    target_roles = (
        audience_roles.get(
            audience,
            ()
        )
    )


    if not target_roles:
        return 0


    # --------------------------------------------------------
    # ACTIVE TARGET USERS
    # --------------------------------------------------------

    users = (
        User.query
        .filter(
            User.role.in_(
                target_roles
            ),
            User.is_active.is_(True)
        )
        .all()
    )


    notification_count = 0


    for target_user in users:

        notification = Notification(

            user_id=
                target_user.id,

            title=
                f"New Notice: {notice.title}",

            message=
                notice.message,

            category=
                "notice",

            link=
                None,

            is_read=
                False
        )


        db.session.add(
            notification
        )

        notification_count += 1


    return notification_count


def create_hod_teacher_notice_notifications(
    notice,
    hod
):

    if not hod or not hod.department_id:
        return 0

    if (
        str(notice.status or "")
        .strip()
        .lower()
        != "published"
    ):
        return 0

    if (
        str(notice.audience or "")
        .strip()
        .lower()
        not in ("all", "teacher")
    ):
        return 0

    teacher_profiles = (
        Teacher.query
        .filter_by(
            department_id=hod.department_id
        )
        .all()
    )

    notification_count = 0

    for teacher in teacher_profiles:
        teacher_user = db.session.get(
            User,
            teacher.user_id
        )

        if not teacher_user or not teacher_user.is_active:
            continue

        notification = Notification(
            user_id=teacher_user.id,
            title=f"New Department Notice: {notice.title}",
            message=notice.message,
            category="notice",
            link="/pages/teacher/notices.html",
            is_read=False
        )

        db.session.add(notification)
        notification_count += 1

    return notification_count

# ============================================================
# GET ALL NOTICES
# ============================================================

@bp.get("")
def get_notices():

    try:

        category = (
            request.args
            .get("category", "")
            .strip()
            .lower()
        )

        audience = (
            request.args
            .get("audience", "")
            .strip()
            .lower()
        )

        priority = (
            request.args
            .get("priority", "")
            .strip()
            .lower()
        )

        status = (
            request.args
            .get("status", "")
            .strip()
            .lower()
        )

        search = (
            request.args
            .get("search", "")
            .strip()
            .lower()
        )


        # ====================================================
        # BASE QUERY
        # ====================================================

        query = Notice.query


        # ====================================================
        # FILTERS
        # ====================================================

        if category:
            query = query.filter(
                Notice.category == category
            )


        if audience:
            query = query.filter(
                Notice.audience == audience
            )


        if priority:
            query = query.filter(
                Notice.priority == priority
            )


        if status:
            query = query.filter(
                Notice.status == status
            )


        # ====================================================
        # GET RECORDS
        # ====================================================

        notices = (
            query
            .order_by(
                Notice.created_at.desc(),
                Notice.id.desc()
            )
            .all()
        )


        data = []


        for notice in notices:

            item = notice.to_dict()


            # ================================================
            # SEARCH FILTER
            # ================================================

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
                            "message",
                            ""
                        ) or ""
                    ),

                    str(
                        item.get(
                            "category",
                            ""
                        ) or ""
                    ),

                    str(
                        item.get(
                            "audience",
                            ""
                        ) or ""
                    ),

                    str(
                        item.get(
                            "priority",
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


            data.append(item)


        # ====================================================
        # SUMMARY
        # ====================================================

        total = len(data)

        published = sum(
            1
            for item in data
            if str(
                item.get(
                    "status",
                    ""
                )
            ).lower() == "published"
        )

        draft = sum(
            1
            for item in data
            if str(
                item.get(
                    "status",
                    ""
                )
            ).lower() == "draft"
        )

        urgent = sum(
            1
            for item in data
            if str(
                item.get(
                    "priority",
                    ""
                )
            ).lower() == "urgent"
        )


        return jsonify({

            "success": True,

            "data": data,

            "summary": {
                "total": total,
                "published": published,
                "draft": draft,
                "urgent": urgent,
            }

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load notices.",

            "error":
                str(error),

        }), 500


# ============================================================
# GET SINGLE NOTICE
# ============================================================

@bp.get("/<int:notice_id>")
def get_notice(notice_id):

    try:

        notice = db.session.get(
            Notice,
            notice_id
        )


        if not notice:

            return jsonify({

                "success": False,

                "message":
                    "Notice not found.",

            }), 404


        return jsonify({

            "success": True,

            "data":
                notice.to_dict(),

        }), 200


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load notice.",

            "error":
                str(error),

        }), 500


# ============================================================
# CREATE NOTICE
# ============================================================

@bp.post("")
@jwt_required()
def create_notice():


    try:

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


        message = str(
            data.get(
                "message",
                ""
            ) or ""
        ).strip()


        category = str(
            data.get(
                "category",
                "general"
            ) or "general"
        ).strip().lower()


        audience = str(
            data.get(
                "audience",
                "all"
            ) or "all"
        ).strip().lower()


        priority = str(
            data.get(
                "priority",
                "normal"
            ) or "normal"
        ).strip().lower()


        status = str(
            data.get(
                "status",
                "published"
            ) or "published"
        ).strip().lower()


        expiry_date_value = str(
            data.get(
                "expiry_date",
                ""
            ) or ""
        ).strip()


        # ====================================================
        # CURRENT LOGGED-IN ADMIN
        # ====================================================

        identity = get_jwt_identity()

        try:
            user_id = int(identity)

        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "Invalid login session"
            }), 401


        creator = db.session.get(
            User,
            user_id
        )


        if not creator:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404


        if (
            str(creator.role or "")
            .strip()
            .lower()
            != "admin"
        ):
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403


        if not creator.is_active:
            return jsonify({
                "success": False,
                "message": "Admin account is inactive"
            }), 403


        created_by = creator.id


        # ====================================================
        # REQUIRED FIELDS
        # ====================================================

        if not title:

            return jsonify({

                "success": False,

                "message":
                    "Notice title is required.",

            }), 400


        if not message:

            return jsonify({

                "success": False,

                "message":
                    "Notice message is required.",

            }), 400


        # ====================================================
        # CATEGORY VALIDATION
        # ====================================================

        if category not in VALID_CATEGORIES:

            return jsonify({

                "success": False,

                "message":
                    "Invalid notice category.",

            }), 400


        # ====================================================
        # AUDIENCE VALIDATION
        # ====================================================

        if audience not in VALID_AUDIENCES:

            return jsonify({

                "success": False,

                "message":
                    "Invalid notice audience.",

            }), 400


        # ====================================================
        # PRIORITY VALIDATION
        # ====================================================

        if priority not in VALID_PRIORITIES:

            return jsonify({

                "success": False,

                "message":
                    "Invalid notice priority.",

            }), 400


        # ====================================================
        # STATUS VALIDATION
        # ====================================================

        if status not in VALID_STATUSES:

            return jsonify({

                "success": False,

                "message":
                    "Invalid notice status.",

            }), 400


        # ====================================================
        # EXPIRY DATE
        # ====================================================

        expiry_date = None


        if expiry_date_value:

            expiry_date = parse_date(
                expiry_date_value
            )


            if not expiry_date:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid expiry_date. Use YYYY-MM-DD.",

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
                        "created_by must be a valid user ID.",

                }), 400


            # Check user exists

            creator = db.session.get(
                User,
                created_by
            )


            if not creator:

                return jsonify({

                    "success": False,

                    "message":
                        "Creator user not found.",

                }), 400


        # ====================================================
        # CREATE NOTICE
        # ====================================================

        notice = Notice(
            title=title,
            message=message,
            category=category,
            audience=audience,
            priority=priority,
            status=status,
            expiry_date=expiry_date,
            created_by=created_by,
        )


        db.session.add(
            notice
        )

        # Generate notice ID before final commit
        db.session.flush()


        # ========================================================
        # CREATE NOTIFICATIONS
        # ========================================================

        notification_count = create_admin_notice_notifications(
            notice,
            creator
        )


        # ========================================================
        # SAVE NOTICE + NOTIFICATIONS TOGETHER
        # ========================================================

        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Notice created successfully.",


            "data":
                notice.to_dict(),

        }), 201


        return jsonify({

            "success": True,

            "message":
                "Notice created successfully.",

            "data":
                notice.to_dict(),

        }), 201


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to create notice.",

            "error":
                str(error),

        }), 500


# ============================================================
# UPDATE NOTICE
# ============================================================

@bp.put("/<int:notice_id>")
def update_notice(notice_id):

    try:

        notice = db.session.get(
            Notice,
            notice_id
        )


        if not notice:

            return jsonify({

                "success": False,

                "message":
                    "Notice not found.",

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
                        "Notice title cannot be empty.",

                }), 400


            notice.title = title


        # ====================================================
        # MESSAGE
        # ====================================================

        if "message" in data:

            message = str(
                data.get(
                    "message",
                    ""
                ) or ""
            ).strip()


            if not message:

                return jsonify({

                    "success": False,

                    "message":
                        "Notice message cannot be empty.",

                }), 400


            notice.message = message


        # ====================================================
        # CATEGORY
        # ====================================================

        if "category" in data:

            category = str(
                data.get(
                    "category",
                    ""
                ) or ""
            ).strip().lower()


            if category not in VALID_CATEGORIES:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid notice category.",

                }), 400


            notice.category = category


        # ====================================================
        # AUDIENCE
        # ====================================================

        if "audience" in data:

            audience = str(
                data.get(
                    "audience",
                    ""
                ) or ""
            ).strip().lower()


            if audience not in VALID_AUDIENCES:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid notice audience.",

                }), 400


            notice.audience = audience


        # ====================================================
        # PRIORITY
        # ====================================================

        if "priority" in data:

            priority = str(
                data.get(
                    "priority",
                    ""
                ) or ""
            ).strip().lower()


            if priority not in VALID_PRIORITIES:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid notice priority.",

                }), 400


            notice.priority = priority


        # ====================================================
        # STATUS
        # ====================================================

        if "status" in data:

            status = str(
                data.get(
                    "status",
                    ""
                ) or ""
            ).strip().lower()


            if status not in VALID_STATUSES:

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid notice status.",

                }), 400


            notice.status = status


        # ====================================================
        # EXPIRY DATE
        # ====================================================

        if "expiry_date" in data:

            expiry_date_value = str(
                data.get(
                    "expiry_date",
                    ""
                ) or ""
            ).strip()


            if not expiry_date_value:

                notice.expiry_date = None


            else:

                expiry_date = parse_date(
                    expiry_date_value
                )


                if not expiry_date:

                    return jsonify({

                        "success": False,

                        "message":
                            "Invalid expiry_date. Use YYYY-MM-DD.",

                    }), 400


                notice.expiry_date = expiry_date


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

                notice.created_by = None


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
                            "created_by must be a valid user ID.",

                    }), 400


                creator = db.session.get(
                    User,
                    created_by
                )


                if not creator:

                    return jsonify({

                        "success": False,

                        "message":
                            "Creator user not found.",

                    }), 400


                notice.created_by = created_by


        # ====================================================
        # SAVE
        # ====================================================

        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Notice updated successfully.",

            "data":
                notice.to_dict(),

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to update notice.",

            "error":
                str(error),

        }), 500


# ============================================================
# DELETE NOTICE
# ============================================================

@bp.delete("/<int:notice_id>")
def delete_notice(notice_id):

    try:

        notice = db.session.get(
            Notice,
            notice_id
        )


        if not notice:

            return jsonify({

                "success": False,

                "message":
                    "Notice not found.",

            }), 404


        db.session.delete(
            notice
        )


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Notice deleted successfully.",

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to delete notice.",

            "error":
                str(error),

        }), 500


# ============================================================
# TEACHER NOTICE HELPER
# ============================================================

def get_current_teacher_for_notices():

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
# TEACHER - GET NOTICES
#
# GET /api/notices/teacher/me
#
# Teacher can see only:
# 1. Published, non-expired notices
# 2. Audience all or teacher
# 3. Admin/System notices
# 4. Same-department HOD notices
# ============================================================

@bp.get("/teacher/me")
@jwt_required()
def get_teacher_notices():

    try:

        user, teacher, error_response = (
            get_current_teacher_for_notices()
        )

        if error_response:
            return error_response

        category = (
            request.args
            .get("category", "")
            .strip()
            .lower()
        )

        priority = (
            request.args
            .get("priority", "")
            .strip()
            .lower()
        )

        search = (
            request.args
            .get("search", "")
            .strip()
            .lower()
        )

        query = (
            Notice.query
            .filter(
                Notice.status == "published",
                Notice.audience.in_(("all", "teacher"))
            )
        )

        if category:
            query = query.filter(
                Notice.category == category
            )

        if priority:
            query = query.filter(
                Notice.priority == priority
            )

        notices = (
            query
            .order_by(
                Notice.created_at.desc(),
                Notice.id.desc()
            )
            .all()
        )

        today = datetime.now().date()
        data = []

        for notice in notices:

            if notice.expiry_date and notice.expiry_date < today:
                continue

            creator = notice.creator
            include_notice = False
            source = "system"

            if creator is None:
                include_notice = True

            else:
                creator_role = (
                    str(creator.role or "")
                    .strip()
                    .lower()
                )

                if creator_role == "admin":
                    include_notice = True
                    source = "admin"

                elif creator_role == "hod":
                    creator_hod = (
                        Hod.query
                        .filter_by(user_id=creator.id)
                        .first()
                    )

                    if (
                        creator_hod
                        and creator_hod.department_id
                        == teacher.department_id
                    ):
                        include_notice = True
                        source = "department"

            if not include_notice:
                continue

            item = notice.to_dict()

            if search:
                searchable_text = " ".join([
                    str(item.get("title", "") or ""),
                    str(item.get("message", "") or ""),
                    str(item.get("category", "") or ""),
                    str(item.get("priority", "") or ""),
                ]).lower()

                if search not in searchable_text:
                    continue

            item["source"] = source
            item["can_edit"] = False
            item["can_delete"] = False
            data.append(item)

        summary = {
            "total": len(data),
            "published": len(data),
            "urgent": sum(
                1 for item in data
                if str(item.get("priority", "")).lower() == "urgent"
            ),
            "important": sum(
                1 for item in data
                if str(item.get("priority", "")).lower() == "important"
            ),
            "normal": sum(
                1 for item in data
                if str(item.get("priority", "")).lower() == "normal"
            ),
            "admin_notices": sum(
                1 for item in data
                if item.get("source") in ("admin", "system")
            ),
            "department_notices": sum(
                1 for item in data
                if item.get("source") == "department"
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
            "message": "Unable to load Teacher notices.",
            "error": str(error)
        }), 500


# ============================================================
# HOD NOTICE HELPER
# ============================================================

def get_current_hod_for_notices():

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
# HOD - GET NOTICES
#
# GET /api/notices/hod
#
# HOD can see:
# 1. Global Admin/System notices for all or HOD
# 2. Notices created by this HOD
# 3. Same-department HOD notices
# ============================================================

@bp.get("/hod")
@jwt_required()
def get_hod_notices():

    try:

        user, hod, error_response = (
            get_current_hod_for_notices()
        )


        if error_response:

            return error_response


        notices = (
            Notice.query
            .order_by(
                Notice.created_at.desc(),
                Notice.id.desc()
            )
            .all()
        )


        today = (
            datetime.now().date()
        )


        data = []


        for notice in notices:

            is_own_notice = (
                notice.created_by
                == user.id
            )


            include_notice = False


            # =================================================
            # OWN HOD NOTICE
            #
            # Own drafts / published / archived are visible
            # so HOD can manage them later.
            # =================================================

            if is_own_notice:

                include_notice = True


            else:

                notice_status = (
                    str(
                        notice.status or ""
                    )
                    .strip()
                    .lower()
                )


                notice_audience = (
                    str(
                        notice.audience or ""
                    )
                    .strip()
                    .lower()
                )


                # ---------------------------------------------
                # Other notices must be published
                # ---------------------------------------------

                if (
                    notice_status
                    != "published"
                ):

                    continue


                # ---------------------------------------------
                # HOD only receives all/hod notices
                # ---------------------------------------------

                if (
                    notice_audience
                    not in (
                        "all",
                        "hod",
                    )
                ):

                    continue


                # ---------------------------------------------
                # Ignore expired notices
                # ---------------------------------------------

                if (
                    notice.expiry_date
                    and
                    notice.expiry_date
                    < today
                ):

                    continue


                creator = (
                    notice.creator
                )


                # ---------------------------------------------
                # SYSTEM NOTICE
                # ---------------------------------------------

                if creator is None:

                    include_notice = True


                else:

                    creator_role = (
                        str(
                            creator.role or ""
                        )
                        .strip()
                        .lower()
                    )


                    # -----------------------------------------
                    # ADMIN NOTICE = GLOBAL
                    # -----------------------------------------

                    if (
                        creator_role
                        == "admin"
                    ):

                        include_notice = True


                    # -----------------------------------------
                    # HOD NOTICE =
                    # ONLY SAME DEPARTMENT
                    # -----------------------------------------

                    elif (
                        creator_role
                        == "hod"
                    ):

                        creator_hod = (
                            Hod.query
                            .filter_by(
                                user_id=
                                    creator.id
                            )
                            .first()
                        )


                        if (
                            creator_hod
                            and
                            creator_hod.department_id
                            == hod.department_id
                        ):

                            include_notice = True


            if not include_notice:

                continue


            item = (
                notice.to_dict()
            )


            # =================================================
            # EXTRA HOD INFORMATION
            # =================================================

            item["is_own"] = (
                is_own_notice
            )


            item["can_edit"] = (
                is_own_notice
            )


            item["can_delete"] = (
                is_own_notice
            )


            item["source"] = (
                "department"
                if is_own_notice
                else "system"
            )


            data.append(
                item
            )


        # ====================================================
        # SUMMARY
        # ====================================================

        summary = {

            "total":
                len(data),

            "published":
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
                        == "published"
                    )
                ),

            "draft":
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
                        == "draft"
                    )
                ),

            "urgent":
                sum(
                    1
                    for item in data
                    if (
                        str(
                            item.get(
                                "priority",
                                ""
                            )
                        ).lower()
                        == "urgent"
                    )
                ),

            "created_by_me":
                sum(
                    1
                    for item in data
                    if item.get(
                        "is_own"
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

            "message":
                "Unable to load HOD notices.",

            "error":
                str(error)

        }), 500



# ============================================================
# HOD - CREATE NOTICE
#
# POST /api/notices/hod
# ============================================================

@bp.post("/hod")
@jwt_required()
def create_hod_notice():

    try:

        user, hod, error_response = (
            get_current_hod_for_notices()
        )

        if error_response:
            return error_response


        data = get_json_data()


        # ----------------------------------------------------
        # BASIC VALUES
        # ----------------------------------------------------

        title = str(
            data.get(
                "title",
                ""
            ) or ""
        ).strip()


        message = str(
            data.get(
                "message",
                ""
            ) or ""
        ).strip()


        category = str(
            data.get(
                "category",
                "general"
            ) or "general"
        ).strip().lower()


        audience = str(
            data.get(
                "audience",
                "all"
            ) or "all"
        ).strip().lower()


        priority = str(
            data.get(
                "priority",
                "normal"
            ) or "normal"
        ).strip().lower()


        status = str(
            data.get(
                "status",
                "published"
            ) or "published"
        ).strip().lower()


        expiry_date_value = str(
            data.get(
                "expiry_date",
                ""
            ) or ""
        ).strip()


        # ----------------------------------------------------
        # REQUIRED
        # ----------------------------------------------------

        if not title:

            return jsonify({
                "success": False,
                "message":
                    "Notice title is required."
            }), 400


        if not message:

            return jsonify({
                "success": False,
                "message":
                    "Notice message is required."
            }), 400


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if category not in VALID_CATEGORIES:

            return jsonify({
                "success": False,
                "message":
                    "Invalid notice category."
            }), 400


        if audience not in VALID_AUDIENCES:

            return jsonify({
                "success": False,
                "message":
                    "Invalid notice audience."
            }), 400


        if priority not in VALID_PRIORITIES:

            return jsonify({
                "success": False,
                "message":
                    "Invalid notice priority."
            }), 400


        if status not in VALID_STATUSES:

            return jsonify({
                "success": False,
                "message":
                    "Invalid notice status."
            }), 400


        # ----------------------------------------------------
        # EXPIRY DATE
        # ----------------------------------------------------

        expiry_date = None


        if expiry_date_value:

            expiry_date = parse_date(
                expiry_date_value
            )


            if not expiry_date:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid expiry_date. Use YYYY-MM-DD."
                }), 400


        # ----------------------------------------------------
        # IMPORTANT:
        # created_by comes from JWT.
        # HOD cannot send another user id.
        # ----------------------------------------------------

        notice = Notice(

            title=title,

            message=message,

            category=category,

            audience=audience,

            priority=priority,

            status=status,

            expiry_date=expiry_date,

            created_by=user.id
        )


        db.session.add(
            notice
        )

        db.session.flush()

        notification_count = (
            create_hod_teacher_notice_notifications(
                notice,
                hod
            )
        )

        db.session.commit()


        item = notice.to_dict()

        item["is_own"] = True
        item["can_edit"] = True
        item["can_delete"] = True
        item["source"] = "department"


        return jsonify({

            "success": True,

            "message":
                "HOD notice created successfully.",

            "department_id":
                hod.department_id,

            "department":
                (
                    hod.department.name
                    if hod.department
                    else None
                ),

            "notification_count":
                notification_count,

            "data":
                item

        }), 201


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to create HOD notice.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - UPDATE OWN NOTICE
#
# PATCH /api/notices/hod/<notice_id>
# ============================================================

@bp.patch("/hod/<int:notice_id>")
@jwt_required()
def update_hod_notice(
    notice_id
):

    try:

        user, hod, error_response = (
            get_current_hod_for_notices()
        )

        if error_response:
            return error_response


        notice = db.session.get(
            Notice,
            notice_id
        )


        if not notice:

            return jsonify({
                "success": False,
                "message":
                    "Notice not found."
            }), 404


        # ----------------------------------------------------
        # HOD CAN UPDATE ONLY OWN NOTICE
        # ----------------------------------------------------

        if notice.created_by != user.id:

            return jsonify({
                "success": False,
                "message":
                    "You can only update notices created by you."
            }), 403


        data = get_json_data()


        if not data:

            return jsonify({
                "success": False,
                "message":
                    "No notice data provided."
            }), 400


        previous_status = (
            str(notice.status or "")
            .strip()
            .lower()
        )

        previous_audience = (
            str(notice.audience or "")
            .strip()
            .lower()
        )


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

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
                        "Notice title cannot be empty."
                }), 400


            notice.title = title


        # ----------------------------------------------------
        # MESSAGE
        # ----------------------------------------------------

        if "message" in data:

            message = str(
                data.get(
                    "message",
                    ""
                ) or ""
            ).strip()


            if not message:

                return jsonify({
                    "success": False,
                    "message":
                        "Notice message cannot be empty."
                }), 400


            notice.message = message


        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        if "category" in data:

            category = str(
                data.get(
                    "category",
                    ""
                ) or ""
            ).strip().lower()


            if category not in VALID_CATEGORIES:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid notice category."
                }), 400


            notice.category = category


        # ----------------------------------------------------
        # AUDIENCE
        # ----------------------------------------------------

        if "audience" in data:

            audience = str(
                data.get(
                    "audience",
                    ""
                ) or ""
            ).strip().lower()


            if audience not in VALID_AUDIENCES:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid notice audience."
                }), 400


            notice.audience = audience


        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        if "priority" in data:

            priority = str(
                data.get(
                    "priority",
                    ""
                ) or ""
            ).strip().lower()


            if priority not in VALID_PRIORITIES:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid notice priority."
                }), 400


            notice.priority = priority


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if "status" in data:

            status = str(
                data.get(
                    "status",
                    ""
                ) or ""
            ).strip().lower()


            if status not in VALID_STATUSES:

                return jsonify({
                    "success": False,
                    "message":
                        "Invalid notice status."
                }), 400


            notice.status = status


        # ----------------------------------------------------
        # EXPIRY DATE
        # ----------------------------------------------------

        if "expiry_date" in data:

            expiry_date_value = str(
                data.get(
                    "expiry_date",
                    ""
                ) or ""
            ).strip()


            if not expiry_date_value:

                notice.expiry_date = None

            else:

                expiry_date = parse_date(
                    expiry_date_value
                )


                if not expiry_date:

                    return jsonify({
                        "success": False,
                        "message":
                            "Invalid expiry_date. Use YYYY-MM-DD."
                    }), 400


                notice.expiry_date = (
                    expiry_date
                )


        current_status = (
            str(notice.status or "")
            .strip()
            .lower()
        )

        current_audience = (
            str(notice.audience or "")
            .strip()
            .lower()
        )

        became_teacher_visible = (
            current_status == "published"
            and current_audience in ("all", "teacher")
            and (
                previous_status != "published"
                or previous_audience not in ("all", "teacher")
            )
        )

        notification_count = 0

        if became_teacher_visible:
            notification_count = (
                create_hod_teacher_notice_notifications(
                    notice,
                    hod
                )
            )

        db.session.commit()


        item = notice.to_dict()

        item["is_own"] = True
        item["can_edit"] = True
        item["can_delete"] = True
        item["source"] = "department"


        return jsonify({

            "success": True,

            "message":
                "HOD notice updated successfully.",

            "notification_count":
                notification_count,

            "data":
                item

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to update HOD notice.",

            "error":
                str(error)

        }), 500


# ============================================================
# HOD - DELETE OWN NOTICE
#
# DELETE /api/notices/hod/<notice_id>
# ============================================================

@bp.delete("/hod/<int:notice_id>")
@jwt_required()
def delete_hod_notice(
    notice_id
):

    try:

        user, hod, error_response = (
            get_current_hod_for_notices()
        )

        if error_response:
            return error_response


        notice = db.session.get(
            Notice,
            notice_id
        )


        if not notice:

            return jsonify({
                "success": False,
                "message":
                    "Notice not found."
            }), 404


        # ----------------------------------------------------
        # HOD CAN DELETE ONLY OWN NOTICE
        # ----------------------------------------------------

        if notice.created_by != user.id:

            return jsonify({
                "success": False,
                "message":
                    "You can only delete notices created by you."
            }), 403


        db.session.delete(
            notice
        )

        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "HOD notice deleted successfully."

        }), 200


    except Exception as error:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                "Unable to delete HOD notice.",

            "error":
                str(error)

        }), 500
