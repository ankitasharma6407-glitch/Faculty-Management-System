from flask import Blueprint, jsonify, request
from datetime import datetime

from ..models import (
    User,
    Department,
    Teacher,
    Hod,
    Student,
    Recruiter,
    Subject,
    Assignment,
    AssignmentSubmission,
    StudyMaterial,
    AcademicEvent,
    PerformanceRecord,
    Notification,
    AuditLog,
)

bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/admin"
)


@bp.get("/dashboard")
def admin_dashboard():

    data = {
        "users": User.query.count(),
        "departments": Department.query.count(),
        "teachers": Teacher.query.count(),
        "hods": Hod.query.count(),
        "students": Student.query.count(),
        "recruiters": Recruiter.query.count(),
        "subjects": Subject.query.count(),
        "assignments": Assignment.query.count(),
        "submissions": AssignmentSubmission.query.count(),
        "study_materials": StudyMaterial.query.count(),
        "academic_events": AcademicEvent.query.count(),
        "performance_records": PerformanceRecord.query.count(),
        "notifications": Notification.query.count(),
        "audit_logs": AuditLog.query.count(),
    }

    return jsonify({
        "success": True,
        "data": data
    })

# ============================================================
# ADD TEACHER
# ============================================================

@bp.post("/teachers")
def add_teacher():

    data = request.form

    # -----------------------------
    # Required fields
    # -----------------------------

    teacher_code = data.get("teacherId")
    full_name = data.get("teacherName")
    email = data.get("teacherEmail")
    phone = data.get("teacherPhone")
    gender = data.get("teacherGender")
    dob = data.get("teacherDob")
    blood_group = data.get("bloodGroup")
    department_name = data.get("teacherDepartment")
    designation = data.get("teacherDesignation")
    qualification = data.get("teacherQualification")
    experience = data.get("teacherExperience")
    joining_date = data.get("joiningDate")
    salary = data.get("teacherSalary")
    address = data.get("teacherAddress")
    username = data.get("username")
    password = data.get("password")
    status = data.get("teacherStatus", "Active")

    # -----------------------------
    # Basic validation
    # -----------------------------

    if not teacher_code or not full_name or not email:
        return jsonify({
            "success": False,
            "message": "Teacher ID, name and email are required."
        }), 400

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required."
        }), 400

    # -----------------------------
    # Check duplicate username
    # -----------------------------

    if User.query.filter_by(username=username).first():
        return jsonify({
            "success": False,
            "message": "Username already exists."
        }), 409

    # -----------------------------
    # Check duplicate email
    # -----------------------------

    if User.query.filter_by(email=email).first():
        return jsonify({
            "success": False,
            "message": "Email already exists."
        }), 409

    # -----------------------------
    # Check duplicate Teacher ID
    # -----------------------------

    if Teacher.query.filter_by(
        teacher_code=teacher_code
    ).first():

        return jsonify({
            "success": False,
            "message": "Teacher ID already exists."
        }), 409

    # -----------------------------
    # Find department
    # -----------------------------

    department = Department.query.filter_by(
        name=department_name
    ).first()

    if not department:

        return jsonify({
            "success": False,
            "message": "Department not found."
        }), 404

    try:

        # -----------------------------
        # Create User
        # -----------------------------

        user = User(
            username=username,
            email=email,
            role="teacher",
            is_active=True
        )

        user.set_password(password)

        # -----------------------------
        # Convert dates
        # -----------------------------

        dob_date = (
            datetime.strptime(dob, "%Y-%m-%d").date()
            if dob
            else None
        )

        joining_date_value = (
            datetime.strptime(
                joining_date,
                "%Y-%m-%d"
            ).date()
            if joining_date
            else None
        )

        # -----------------------------
        # Create Teacher
        # -----------------------------

        teacher = Teacher(
            user=user,
            teacher_code=teacher_code,
            full_name=full_name,
            phone=phone,
            gender=gender,
            dob=dob_date,
            blood_group=blood_group,
            address=address,
            department=department,
            designation=designation,
            qualification=qualification,
            experience_years=int(experience or 0),
            salary=float(salary) if salary else None,
            joining_date=joining_date_value,
            status=status.lower()
        )

        # -----------------------------
        # Profile Photo
        # -----------------------------

        photo = request.files.get("teacherPhoto")

        if photo and photo.filename:

            filename = photo.filename

            upload_folder = "uploads"

            import os

            os.makedirs(upload_folder, exist_ok=True)

            photo_path = os.path.join(
                upload_folder,
                filename
            )

            photo.save(photo_path)

            teacher.photo_url = photo_path

        # -----------------------------
        # Save to database
        # -----------------------------

        from ..extensions import db

        db.session.add(user)
        db.session.add(teacher)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Teacher added successfully.",
            "teacher": teacher.to_dict()
        }), 201

    except Exception as e:

        from ..extensions import db

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to add teacher.",
            "error": str(e)
        }), 500