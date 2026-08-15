from datetime import datetime

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Notice, User


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


        created_by = data.get(
            "created_by"
        )


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


        db.session.commit()


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