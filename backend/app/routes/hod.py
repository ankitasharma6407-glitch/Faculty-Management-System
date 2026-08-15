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