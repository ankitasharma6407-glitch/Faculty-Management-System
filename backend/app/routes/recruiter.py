from datetime import datetime

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import text
import os

from ..extensions import db
from ..models import User, Recruiter, AuditLog


bp = Blueprint(
    "recruiter",
    __name__,
    url_prefix="/api/recruiters"
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

        ip_address = request.headers.get(
            "X-Forwarded-For",
            request.remote_addr
        )

        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        audit = AuditLog(
            user_id=None,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address
        )

        db.session.add(audit)

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "Audit Log Error:",
            e
        )


# ============================================================
# GET ALL RECRUITERS
# ============================================================

@bp.get("")
def get_recruiters():

    recruiters = Recruiter.query.order_by(
        Recruiter.id.desc()
    ).all()

    return jsonify({
        "success": True,
        "data": [
            recruiter.to_dict()
            for recruiter in recruiters
        ]
    })


# ============================================================
# DEBUG DATABASE CONNECTION
# ============================================================

@bp.get("/debug-db")
def debug_database():

    database_name = db.session.execute(
        text("SELECT DATABASE()")
    ).scalar()

    mysql_host = db.session.execute(
        text("SELECT @@hostname")
    ).scalar()

    mysql_port = db.session.execute(
        text("SELECT @@port")
    ).scalar()

    recruiter_count = db.session.execute(
        text("SELECT COUNT(*) FROM recruiters")
    ).scalar()

    recruiters = db.session.execute(
        text("""
            SELECT
                id,
                recruiter_code,
                company_name,
                full_name
            FROM recruiters
        """)
    ).mappings().all()

    return jsonify({
        "success": True,
        "database": database_name,
        "mysql_host": mysql_host,
        "mysql_port": mysql_port,
        "recruiter_count": recruiter_count,
        "rows": [
            dict(row)
            for row in recruiters
        ]
    })


# ============================================================
# GET SINGLE RECRUITER
# ============================================================

@bp.get("/<int:recruiter_id>")
def get_recruiter(recruiter_id):

    recruiter = Recruiter.query.get(
        recruiter_id
    )

    if not recruiter:

        return jsonify({
            "success": False,
            "message": "Recruiter not found"
        }), 404

    return jsonify({
        "success": True,
        "data": recruiter.to_dict()
    })


# ============================================================
# ADD RECRUITER
# ============================================================

@bp.post("")
def add_recruiter():

    data = request.form

    recruiter_code = data.get("recruiter_code")
    company_name = data.get("company_name")
    full_name = data.get("full_name")

    email = data.get("email")
    phone = data.get("phone")
    website = data.get("website")

    industry_type = data.get("industry_type")
    company_size = data.get("company_size")
    hiring_role = data.get("hiring_role")
    package_offered = data.get("package_offered")
    hiring_date = data.get("hiring_date")

    address = data.get("address")

    designation = data.get(
        "designation",
        "HR"
    )

    username = data.get("username")
    password = data.get("password")

    status = data.get(
        "status",
        "active"
    )


    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    if not all([
        recruiter_code,
        company_name,
        full_name,
        email,
        username,
        password
    ]):

        return jsonify({
            "success": False,
            "message": "Required fields are missing"
        }), 400


    # ========================================================
    # DUPLICATE USERNAME
    # ========================================================

    if User.query.filter_by(
        username=username
    ).first():

        return jsonify({
            "success": False,
            "message": "Username already exists"
        }), 409


    # ========================================================
    # DUPLICATE EMAIL
    # ========================================================

    if User.query.filter_by(
        email=email
    ).first():

        return jsonify({
            "success": False,
            "message": "Email already exists"
        }), 409


    # ========================================================
    # DUPLICATE RECRUITER ID
    # ========================================================

    if Recruiter.query.filter_by(
        recruiter_code=recruiter_code
    ).first():

        return jsonify({
            "success": False,
            "message": "Recruiter ID already exists"
        }), 409


    try:

        # ====================================================
        # CREATE USER
        # ====================================================

        user = User(
            username=username,
            email=email,
            role="recruiter",
            is_active=(
                str(status).lower() == "active"
            )
        )

        user.set_password(password)

        db.session.add(user)

        db.session.flush()


        # ====================================================
        # CREATE RECRUITER
        # ====================================================

        recruiter = Recruiter(

            user_id=user.id,

            recruiter_code=recruiter_code,

            full_name=full_name,

            phone=phone,

            company_name=company_name,

            designation=designation,

            website=website,

            industry_type=industry_type,

            company_size=company_size,

            hiring_role=hiring_role,

            package_offered=package_offered,

            address=address,

            status=str(status).lower()
        )


        # ====================================================
        # HIRING DATE
        # ====================================================

        if hiring_date:

            recruiter.hiring_date = datetime.strptime(
                hiring_date,
                "%Y-%m-%d"
            ).date()


        # ====================================================
        # COMPANY LOGO
        # ====================================================

        logo = request.files.get("photo")

        if logo and logo.filename:

            upload_folder = os.path.join(
                os.getcwd(),
                "uploads",
                "recruiters"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            filename = secure_filename(
                logo.filename
            )

            filename = (
                f"{user.id}_{filename}"
            )

            logo.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            recruiter.photo_url = (
                f"/uploads/recruiters/{filename}"
            )


        # ====================================================
        # SAVE
        # ====================================================

        db.session.add(recruiter)

        db.session.commit()


        # ====================================================
        # AUDIT LOG - CREATE
        # ====================================================

        write_audit_log(
            action="CREATE",
            entity="recruiter",
            entity_id=recruiter.id,
            details=(
                f"Recruiter added: "
                f"{recruiter.full_name} "
                f"({recruiter.recruiter_code})"
            )
        )


        return jsonify({

            "success": True,

            "message": "Recruiter added successfully",

            "data": recruiter.to_dict()

        }), 201


    except ValueError as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": f"Invalid hiring date: {str(e)}"

        }), 400


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ============================================================
# UPDATE RECRUITER
# ============================================================

@bp.put("/<int:recruiter_id>")
def update_recruiter(recruiter_id):

    recruiter = Recruiter.query.get(
        recruiter_id
    )

    if not recruiter:

        return jsonify({
            "success": False,
            "message": "Recruiter not found"
        }), 404


    data = request.form


    try:

        # ====================================================
        # RECRUITER CODE
        # ====================================================

        recruiter_code = data.get(
            "recruiter_code"
        )

        if (
            recruiter_code is not None and
            recruiter_code != recruiter.recruiter_code
        ):

            existing_recruiter = Recruiter.query.filter(
                Recruiter.recruiter_code == recruiter_code,
                Recruiter.id != recruiter.id
            ).first()

            if existing_recruiter:

                return jsonify({
                    "success": False,
                    "message": "Recruiter ID already exists"
                }), 409

            recruiter.recruiter_code = (
                recruiter_code
            )


        # ====================================================
        # BASIC DETAILS
        # ====================================================

        if data.get("full_name") is not None:

            recruiter.full_name = data.get(
                "full_name"
            )


        if data.get("phone") is not None:

            recruiter.phone = data.get(
                "phone"
            )


        if data.get("company_name") is not None:

            recruiter.company_name = data.get(
                "company_name"
            )


        if data.get("designation") is not None:

            recruiter.designation = data.get(
                "designation"
            )


        if data.get("website") is not None:

            recruiter.website = data.get(
                "website"
            )


        if data.get("industry_type") is not None:

            recruiter.industry_type = data.get(
                "industry_type"
            )


        if data.get("company_size") is not None:

            recruiter.company_size = data.get(
                "company_size"
            )


        if data.get("hiring_role") is not None:

            recruiter.hiring_role = data.get(
                "hiring_role"
            )


        if data.get("package_offered") is not None:

            recruiter.package_offered = data.get(
                "package_offered"
            )


        if data.get("address") is not None:

            recruiter.address = data.get(
                "address"
            )


        # ====================================================
        # HIRING DATE
        # ====================================================

        if "hiring_date" in data:

            hiring_date = data.get(
                "hiring_date"
            )

            if hiring_date:

                recruiter.hiring_date = datetime.strptime(
                    hiring_date,
                    "%Y-%m-%d"
                ).date()

            else:

                recruiter.hiring_date = None


        # ====================================================
        # EMAIL
        # ====================================================

        email = data.get("email")

        if email is not None and recruiter.user:

            existing_user = User.query.filter(
                User.email == email,
                User.id != recruiter.user.id
            ).first()

            if existing_user:

                return jsonify({
                    "success": False,
                    "message": "Email already exists"
                }), 409

            recruiter.user.email = email


        # ====================================================
        # USERNAME
        # ====================================================

        username = data.get("username")

        if username is not None and recruiter.user:

            existing_user = User.query.filter(
                User.username == username,
                User.id != recruiter.user.id
            ).first()

            if existing_user:

                return jsonify({
                    "success": False,
                    "message": "Username already exists"
                }), 409

            recruiter.user.username = username


        # ====================================================
        # PASSWORD
        # ====================================================

        password = data.get("password")

        if password and recruiter.user:

            recruiter.user.set_password(
                password
            )


        # ====================================================
        # STATUS
        # ====================================================

        status = data.get("status")

        if status is not None:

            recruiter.status = (
                status.lower()
            )

            if recruiter.user:

                recruiter.user.is_active = (
                    recruiter.status == "active"
                )


        # ====================================================
        # COMPANY LOGO
        # ====================================================

        logo = request.files.get("photo")

        if logo and logo.filename:

            upload_folder = os.path.join(
                os.getcwd(),
                "uploads",
                "recruiters"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            filename = secure_filename(
                logo.filename
            )

            filename = (
                f"{recruiter.user_id}_{filename}"
            )

            logo.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            recruiter.photo_url = (
                f"/uploads/recruiters/{filename}"
            )


        # ====================================================
        # SAVE
        # ====================================================

        db.session.commit()


        # ====================================================
        # AUDIT LOG - UPDATE
        # ====================================================

        write_audit_log(
            action="UPDATE",
            entity="recruiter",
            entity_id=recruiter.id,
            details=(
                f"Recruiter updated: "
                f"{recruiter.full_name} "
                f"({recruiter.recruiter_code})"
            )
        )


        return jsonify({

            "success": True,

            "message": "Recruiter updated successfully",

            "data": recruiter.to_dict()

        })


    except ValueError as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": f"Invalid hiring date: {str(e)}"

        }), 400


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ============================================================
# DELETE RECRUITER
# ============================================================

@bp.delete("/<int:recruiter_id>")
def delete_recruiter(recruiter_id):

    recruiter = Recruiter.query.get(
        recruiter_id
    )

    if not recruiter:

        return jsonify({
            "success": False,
            "message": "Recruiter not found"
        }), 404


    try:

        # ====================================================
        # SAVE DETAILS BEFORE DELETE
        # ====================================================

        deleted_recruiter_id = recruiter.id

        deleted_recruiter_name = (
            recruiter.full_name
        )

        deleted_recruiter_code = (
            recruiter.recruiter_code
        )


        user = recruiter.user


        # ====================================================
        # DELETE
        # ====================================================

        db.session.delete(
            recruiter
        )

        if user:

            db.session.delete(
                user
            )

        db.session.commit()


        # ====================================================
        # AUDIT LOG - DELETE
        # ====================================================

        write_audit_log(
            action="DELETE",
            entity="recruiter",
            entity_id=deleted_recruiter_id,
            details=(
                f"Recruiter deleted: "
                f"{deleted_recruiter_name} "
                f"({deleted_recruiter_code})"
            )
        )


        return jsonify({

            "success": True,

            "message": "Recruiter deleted successfully"

        })


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500