from flask import Blueprint, jsonify, request

from ..models import PerformanceRecord


# ============================================================
# BLUEPRINT
# ============================================================

bp = Blueprint(
    "performance",
    __name__,
    url_prefix="/api/performance"
)


# ============================================================
# HELPER - CALCULATE PERCENTAGE
# ============================================================

def calculate_percentage(record):

    if (
        record.score is None
        or record.max_score is None
    ):
        return 0.0

    score = float(record.score)
    max_score = float(record.max_score)

    if max_score <= 0:
        return 0.0

    return round(
        (score / max_score) * 100,
        2
    )


# ============================================================
# HELPER - PERFORMANCE BAND
# ============================================================

def get_performance_band(percentage):

    if percentage >= 80:
        return "excellent"

    if percentage >= 60:
        return "good"

    if percentage >= 40:
        return "average"

    return "poor"


# ============================================================
# GET ALL PERFORMANCE RECORDS
# ============================================================

@bp.get("")
def get_performance_records():

    try:

        user_id = request.args.get(
            "user_id",
            type=int
        )

        term = (
            request.args
            .get("term", "")
            .strip()
        )


        query = PerformanceRecord.query


        # ----------------------------------------------------
        # USER FILTER
        # ----------------------------------------------------

        if user_id:

            query = query.filter(
                PerformanceRecord.user_id
                == user_id
            )


        # ----------------------------------------------------
        # TERM FILTER
        # ----------------------------------------------------

        if term:

            query = query.filter(
                PerformanceRecord.term
                == term
            )


        records = (
            query
            .order_by(
                PerformanceRecord.id.desc()
            )
            .all()
        )


        # ====================================================
        # SERIALIZE RECORDS
        # ====================================================

        data = []


        for record in records:

            item = record.to_dict()

            percentage = (
                calculate_percentage(record)
            )

            item["percentage"] = (
                percentage
            )

            item["performance_band"] = (
                get_performance_band(
                    percentage
                )
            )

            data.append(item)


        # ====================================================
        # LATEST RECORD PER FACULTY
        #
        # Dashboard should count faculty,
        # not duplicate semester records.
        # ====================================================

        latest_by_user = {}


        for record in records:

            if (
                record.user_id
                not in latest_by_user
            ):

                latest_by_user[
                    record.user_id
                ] = record


        latest_records = list(
            latest_by_user.values()
        )


        # ====================================================
        # PERFORMANCE DISTRIBUTION
        # ====================================================

        excellent = 0
        good = 0
        average = 0
        poor = 0


        percentages = []


        for record in latest_records:

            percentage = (
                calculate_percentage(record)
            )


            percentages.append(
                percentage
            )


            band = (
                get_performance_band(
                    percentage
                )
            )


            if band == "excellent":

                excellent += 1


            elif band == "good":

                good += 1


            elif band == "average":

                average += 1


            else:

                poor += 1


        total_faculty = len(
            latest_records
        )


        overall_average = (

            round(
                sum(percentages)
                / total_faculty,
                2
            )

            if total_faculty > 0

            else 0.0

        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "data": data,

            "summary": {

                "total_records":
                    len(data),

                "total_faculty":
                    total_faculty,

                "overall_average":
                    overall_average,

                "excellent":
                    excellent,

                "good":
                    good,

                "average":
                    average,

                "poor":
                    poor

            }

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Unable to load performance records.",

            "error":
                str(error)

        }), 500