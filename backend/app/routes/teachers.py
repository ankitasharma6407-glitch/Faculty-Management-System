import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import User, Teacher, AuditLog


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