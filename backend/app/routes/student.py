from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from ..extensions import db
from ..models import User, Student, AuditLog


bp = Blueprint(
    "student",
    __name__,
    url_prefix="/api/students"
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
# GET ALL STUDENTS
# ============================================================

@bp.get("")
def get_students():

    students = Student.query.order_by(
        Student.id.desc()
    ).all()

    return jsonify({
        "success": True,
        "data": [
            student.to_dict()
            for student in students
        ]
    })


# ============================================================
# GET SINGLE STUDENT
# ============================================================

@bp.get("/<int:student_id>")
def get_student(student_id):

    student = Student.query.get(
        student_id
    )

    if not student:

        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    return jsonify({
        "success": True,
        "data": student.to_dict()
    })


# ============================================================
# ADD STUDENT
# ============================================================

@bp.post("")
def add_student():

    data = request.form

    student_code = data.get(
        "student_code"
    )

    roll_number = data.get(
        "roll_number"
    )

    full_name = data.get(
        "full_name"
    )

    email = data.get("email")

    username = data.get(
        "username"
    )

    password = data.get(
        "password"
    )

    phone = data.get("phone")

    gender = data.get("gender")

    dob = data.get("dob")

    blood_group = data.get(
        "blood_group"
    )

    address = data.get(
        "address"
    )

    department_id = data.get(
        "department_id"
    )

    course = data.get(
        "course"
    )

    semester = data.get(
        "semester"
    )

    section = data.get(
        "section"
    )

    guardian_name = data.get(
        "guardian_name"
    )

    guardian_phone = data.get(
        "guardian_phone"
    )

    admission_date = data.get(
        "admission_date"
    )

    status = data.get(
        "status",
        "active"
    )


    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    if not all([
        student_code,
        roll_number,
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
    # DUPLICATE STUDENT CODE
    # ========================================================

    if Student.query.filter_by(
        student_code=student_code
    ).first():

        return jsonify({
            "success": False,
            "message": "Student ID already exists"
        }), 409


    # ========================================================
    # DUPLICATE ROLL NUMBER
    # ========================================================

    if Student.query.filter_by(
        roll_number=roll_number
    ).first():

        return jsonify({
            "success": False,
            "message": "Roll number already exists"
        }), 409


    try:

        # ====================================================
        # CREATE USER
        # ====================================================

        user = User(
            username=username,
            email=email,
            role="student",
            is_active=(
                str(status).lower()
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


        # ====================================================
        # CREATE STUDENT
        # ====================================================

        student = Student(

            user_id=user.id,

            student_code=student_code,

            roll_number=roll_number,

            full_name=full_name,

            phone=phone,

            gender=gender,

            department_id=(
                int(department_id)
                if department_id
                else None
            ),

            course=course,

            semester=semester,

            section=section,

            guardian_name=
                guardian_name,

            guardian_phone=
                guardian_phone,

            address=address,

            status=str(
                status
            ).lower()
        )


        # ====================================================
        # DATE OF BIRTH
        # ====================================================

        if dob:

            student.dob = datetime.strptime(
                dob,
                "%Y-%m-%d"
            ).date()


        # ====================================================
        # ADMISSION DATE
        # ====================================================

        if admission_date:

            student.admission_date = (
                datetime.strptime(
                    admission_date,
                    "%Y-%m-%d"
                ).date()
            )


        # ====================================================
        # PHOTO
        # ====================================================

        photo = request.files.get(
            "photo"
        )


        if photo and photo.filename:

            upload_folder = os.path.join(
                os.getcwd(),
                "uploads",
                "students"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )


            filename = secure_filename(
                photo.filename
            )


            filename = (
                f"{user.id}_{filename}"
            )


            photo.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )


            student.photo_url = (
                f"/uploads/students/{filename}"
            )


        # ====================================================
        # SAVE
        # ====================================================

        db.session.add(
            student
        )

        db.session.commit()


        # ====================================================
        # AUDIT LOG - CREATE
        # ====================================================

        write_audit_log(

            action="CREATE",

            entity="student",

            entity_id=student.id,

            details=(
                f"Student added: "
                f"{student.full_name} "
                f"({student.student_code})"
            )
        )


        return jsonify({

            "success": True,

            "message":
                "Student added successfully",

            "data":
                student.to_dict()

        }), 201


    except ValueError as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                f"Invalid data: {str(e)}"

        }), 400


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ============================================================
# UPDATE STUDENT
# ============================================================

@bp.put("/<int:student_id>")
def update_student(student_id):

    student = Student.query.get(
        student_id
    )

    if not student:

        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404


    data = request.form


    try:

        # ====================================================
        # BASIC DETAILS
        # ====================================================

        if (
            data.get("full_name")
            is not None
        ):

            student.full_name = (
                data.get(
                    "full_name"
                )
            )


        if (
            data.get("phone")
            is not None
        ):

            student.phone = (
                data.get(
                    "phone"
                )
            )


        if (
            data.get("gender")
            is not None
        ):

            student.gender = (
                data.get(
                    "gender"
                )
            )


        if (
            data.get("blood_group")
            is not None
        ):

            student.blood_group = (
                data.get(
                    "blood_group"
                )
            )


        if (
            data.get("address")
            is not None
        ):

            student.address = (
                data.get(
                    "address"
                )
            )


        if (
            data.get("course")
            is not None
        ):

            student.course = (
                data.get(
                    "course"
                )
            )


        if (
            data.get("semester")
            is not None
        ):

            student.semester = (
                data.get(
                    "semester"
                )
            )


        if (
            data.get("section")
            is not None
        ):

            student.section = (
                data.get(
                    "section"
                )
            )


        if (
            data.get("guardian_name")
            is not None
        ):

            student.guardian_name = (
                data.get(
                    "guardian_name"
                )
            )


        if (
            data.get("guardian_phone")
            is not None
        ):

            student.guardian_phone = (
                data.get(
                    "guardian_phone"
                )
            )


        # ====================================================
        # EMAIL
        # ====================================================

        email = data.get(
            "email"
        )


        if (
            email is not None
            and student.user
        ):

            existing_user = (
                User.query.filter(
                    User.email == email,
                    User.id != student.user.id
                ).first()
            )


            if existing_user:

                return jsonify({
                    "success": False,
                    "message": "Email already exists"
                }), 409


            student.user.email = (
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
            and student.user
        ):

            existing_user = (
                User.query.filter(
                    User.username == username,
                    User.id != student.user.id
                ).first()
            )


            if existing_user:

                return jsonify({
                    "success": False,
                    "message": "Username already exists"
                }), 409


            student.user.username = (
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
            and student.user
        ):

            student.user.set_password(
                password
            )


        # ====================================================
        # DEPARTMENT
        # ====================================================

        department_id = data.get(
            "department_id"
        )


        if department_id:

            student.department_id = int(
                department_id
            )


        # ====================================================
        # DATE OF BIRTH
        # ====================================================

        dob = data.get(
            "dob"
        )


        if dob:

            student.dob = (
                datetime.strptime(
                    dob,
                    "%Y-%m-%d"
                ).date()
            )


        # ====================================================
        # ADMISSION DATE
        # ====================================================

        admission_date = data.get(
            "admission_date"
        )


        if admission_date:

            student.admission_date = (
                datetime.strptime(
                    admission_date,
                    "%Y-%m-%d"
                ).date()
            )


        # ====================================================
        # STATUS
        # ====================================================

        status = data.get(
            "status"
        )


        if status is not None:

            student.status = (
                status.lower()
            )


            if student.user:

                student.user.is_active = (
                    student.status
                    == "active"
                )


        # ====================================================
        # PHOTO
        # ====================================================

        photo = request.files.get(
            "photo"
        )


        if photo and photo.filename:

            upload_folder = os.path.join(
                os.getcwd(),
                "uploads",
                "students"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )


            filename = secure_filename(
                photo.filename
            )


            filename = (
                f"{student.user_id}_{filename}"
            )


            photo_path = os.path.join(
                upload_folder,
                filename
            )


            photo.save(
                photo_path
            )


            student.photo_url = (
                f"/uploads/students/{filename}"
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

            entity="student",

            entity_id=student.id,

            details=(
                f"Student updated: "
                f"{student.full_name} "
                f"({student.student_code})"
            )
        )


        return jsonify({

            "success": True,

            "message":
                "Student updated successfully",

            "data":
                student.to_dict()

        })


    except ValueError as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
                f"Invalid data: {str(e)}"

        }), 400


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ============================================================
# DELETE STUDENT
# ============================================================

@bp.delete("/<int:student_id>")
def delete_student(student_id):

    student = Student.query.get(
        student_id
    )


    if not student:

        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404


    try:

        # ====================================================
        # SAVE DETAILS BEFORE DELETE
        # ====================================================

        deleted_student_id = (
            student.id
        )

        deleted_student_name = (
            student.full_name
        )

        deleted_student_code = (
            student.student_code
        )


        user = student.user


        # ====================================================
        # DELETE STUDENT
        # ====================================================

        db.session.delete(
            student
        )


        # ====================================================
        # DELETE ASSOCIATED USER
        # ====================================================

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

            entity="student",

            entity_id=
                deleted_student_id,

            details=(
                f"Student deleted: "
                f"{deleted_student_name} "
                f"({deleted_student_code})"
            )
        )


        return jsonify({

            "success": True,

            "message":
                "Student deleted successfully"

        })


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500