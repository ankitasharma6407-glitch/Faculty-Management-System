from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


# ============================================================
# CONSTANTS
# ============================================================

ROLES = (
    "admin",
    "hod",
    "teacher",
    "student",
    "recruiter",
)


# ============================================================
# MIXIN
# ============================================================

class TimestampMixin:
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


# ============================================================
# USER
# ============================================================

class User(TimestampMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(160),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.Enum(*ROLES, name="user_role"),
        nullable=False,
        index=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    last_login = db.Column(
        db.DateTime
    )

    # Relationships
    teacher = db.relationship(
        "Teacher",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    hod = db.relationship(
        "Hod",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    student = db.relationship(
        "Student",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    recruiter = db.relationship(
        "Recruiter",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    face = db.relationship(
        "FaceEncoding",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(
            self.password_hash,
            raw_password
        )

    @property
    def profile(self):

        return (
            self.teacher
            or self.hod
            or self.student
            or self.recruiter
        )

    def to_dict(self, with_profile=False):

        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "last_login": (
                self.last_login.isoformat()
                if self.last_login
                else None
            ),
            "created_at": self.created_at.isoformat(),
        }

        if with_profile and self.profile:
            data["profile"] = self.profile.to_dict()

        return data


# ============================================================
# DEPARTMENT
# ============================================================

class Department(TimestampMixin, db.Model):

    __tablename__ = "departments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    teachers = db.relationship(
        "Teacher",
        back_populates="department"
    )

    students = db.relationship(
        "Student",
        back_populates="department"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "teacher_count": len(self.teachers),
            "student_count": len(self.students),
        }


# ============================================================
# TEACHER
# ============================================================

class Teacher(TimestampMixin, db.Model):

    __tablename__ = "teachers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False
    )

    teacher_code = db.Column(
        db.String(40),
        unique=True,
        nullable=False,
        index=True
    )

    full_name = db.Column(
        db.String(140),
        nullable=False
    )

    phone = db.Column(
        db.String(20)
    )

    gender = db.Column(
        db.String(20)
    )

    dob = db.Column(
        db.Date
    )

    blood_group = db.Column(
        db.String(10)
    )

    address = db.Column(
        db.Text
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    designation = db.Column(
        db.String(80)
    )

    qualification = db.Column(
        db.String(140)
    )

    experience_years = db.Column(
        db.Integer,
        default=0
    )

    salary = db.Column(
        db.Numeric(12, 2)
    )

    joining_date = db.Column(
        db.Date
    )

    status = db.Column(
        db.String(20),
        default="active"
    )

    photo_url = db.Column(
        db.String(255)
    )

    user = db.relationship(
        "User",
        back_populates="teacher"
    )

    department = db.relationship(
        "Department",
        back_populates="teachers"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "teacher_code": self.teacher_code,
            "full_name": self.full_name,
            "email": self.user.email if self.user else None,
            "username": self.user.username if self.user else None,
            "phone": self.phone,
            "gender": self.gender,
            "dob": self.dob.isoformat() if self.dob else None,
            "blood_group": self.blood_group,
            "address": self.address,
            "department_id": self.department_id,
            "department": (
                self.department.name
                if self.department
                else None
            ),
            "designation": self.designation,
            "qualification": self.qualification,
            "experience_years": self.experience_years,
            "salary": (
                float(self.salary)
                if self.salary is not None
                else None
            ),
            "joining_date": (
                self.joining_date.isoformat()
                if self.joining_date
                else None
            ),
            "status": self.status,
            "photo_url": self.photo_url,
        }


# ============================================================
# HOD
# ============================================================

class Hod(TimestampMixin, db.Model):

    __tablename__ = "hods"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False
    )

    hod_code = db.Column(
        db.String(40),
        unique=True,
        nullable=False,
        index=True
    )

    full_name = db.Column(
        db.String(140),
        nullable=False
    )

    phone = db.Column(
        db.String(20)
    )

    gender = db.Column(
        db.String(20)
    )

    dob = db.Column(
        db.Date
    )

    address = db.Column(
        db.Text
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    qualification = db.Column(
        db.String(140)
    )
    
    experience_years = db.Column(
        db.Integer,
        default=0
    )

    salary = db.Column(
        db.Numeric(12, 2)
    )

    office_room_no = db.Column(
        db.String(50)
    )

    joining_date = db.Column(
        db.Date
    )

    status = db.Column(
        db.String(20),
        default="active"
    )

    photo_url = db.Column(
        db.String(255)
    )

    user = db.relationship(
        "User",
        back_populates="hod"
    )

    department = db.relationship(
        "Department"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "hod_code": self.hod_code,
            "full_name": self.full_name,
            "email": self.user.email if self.user else None,
            "phone": self.phone,
            "gender": self.gender,
            "dob": self.dob.isoformat() if self.dob else None,
            "address": self.address,
            "department_id": self.department_id,
            "department": (
                self.department.name
                if self.department
                else None
            ),
            "qualification": self.qualification,
            "experience_years": self.experience_years,
                        "salary": (
                float(self.salary)
                if self.salary is not None
                else None
            ),

            "office_room_no": self.office_room_no,
            "joining_date": (
                self.joining_date.isoformat()
                if self.joining_date
                else None
            ),
            "status": self.status,
            "photo_url": self.photo_url,
        }


# ============================================================
# STUDENT
# ============================================================

class Student(TimestampMixin, db.Model):

    __tablename__ = "students"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False
    )

    student_code = db.Column(
        db.String(40),
        unique=True,
        nullable=False,
        index=True
    )

    roll_number = db.Column(
        db.String(40),
        unique=True,
        nullable=False,
        index=True
    )

    full_name = db.Column(
        db.String(140),
        nullable=False
    )

    phone = db.Column(
        db.String(20)
    )

    gender = db.Column(
        db.String(20)
    )

    dob = db.Column(
        db.Date
    )

    blood_group = db.Column(
        db.String(10)
    )

    address = db.Column(
        db.Text
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    course = db.Column(
        db.String(120)
    )

    semester = db.Column(
        db.String(20)
    )

    section = db.Column(
        db.String(20)
    )

    guardian_name = db.Column(
        db.String(140)
    )

    guardian_phone = db.Column(
        db.String(20)
    )

    admission_date = db.Column(
        db.Date
    )

    status = db.Column(
        db.String(20),
        default="active"
    )

    photo_url = db.Column(
        db.String(255)
    )

    user = db.relationship(
        "User",
        back_populates="student"
    )

    department = db.relationship(
        "Department",
        back_populates="students"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "student_code": self.student_code,
            "roll_number": self.roll_number,
            "full_name": self.full_name,
            "email": self.user.email if self.user else None,
            "username": self.user.username if self.user else None,
            "phone": self.phone,
            "gender": self.gender,
            "dob": self.dob.isoformat() if self.dob else None,
            "blood_group": self.blood_group,
            "address": self.address,
            "department_id": self.department_id,
            "department": (
                self.department.name
                if self.department
                else None
            ),
            "course": self.course,
            "semester": self.semester,
            "section": self.section,
            "guardian_name": self.guardian_name,
            "guardian_phone": self.guardian_phone,
            "admission_date": (
                self.admission_date.isoformat()
                if self.admission_date
                else None
            ),
            "status": self.status,
            "photo_url": self.photo_url,
        }


# ============================================================
# RECRUITER
# ============================================================

class Recruiter(TimestampMixin, db.Model):

    __tablename__ = "recruiters"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False
    )

    recruiter_code = db.Column(
        db.String(40),
        unique=True,
        nullable=False
    )

    full_name = db.Column(
        db.String(140),
        nullable=False
    )

    phone = db.Column(
        db.String(20)
    )

    company_name = db.Column(
        db.String(160)
    )

    designation = db.Column(
        db.String(100)
    )

    website = db.Column(
        db.String(255)
    )

    industry_type = db.Column(
        db.String(120)
    )

    company_size = db.Column(
        db.String(80)
    )

    hiring_role = db.Column(
        db.String(120)
    )

    package_offered = db.Column(
        db.String(80)
    )

    hiring_date = db.Column(
        db.Date
    )

    address = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(20),
        default="active"
    )

    photo_url = db.Column(
        db.String(255)
    )

    user = db.relationship(
        "User",
        back_populates="recruiter"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "recruiter_code": self.recruiter_code,
            "full_name": self.full_name,
            "email": (
                self.user.email
                if self.user
                else None
            ),
            "username": (
                self.user.username
                if self.user
                else None
            ),
            "phone": self.phone,
            "company_name": self.company_name,
            "designation": self.designation,
            "website": self.website,
            "industry_type": self.industry_type,
            "company_size": self.company_size,
            "hiring_role": self.hiring_role,
            "package_offered": self.package_offered,
            "hiring_date": (
                self.hiring_date.isoformat()
                if self.hiring_date
                else None
            ),
            "address": self.address,
            "status": self.status,
            "photo_url": self.photo_url,
        }


# ============================================================
# SUBJECT
# ============================================================

class Subject(TimestampMixin, db.Model):

    __tablename__ = "subjects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(160),
        nullable=False
    )

    code = db.Column(
        db.String(40),
        unique=True,
        nullable=False
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    semester = db.Column(
        db.String(20)
    )

    credits = db.Column(
        db.Integer,
        default=0
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teachers.id")
    )

    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "department_id": self.department_id,
            "semester": self.semester,
            "credits": self.credits,
            "teacher_id": self.teacher_id,
        }


# ============================================================
# TIMETABLE
# ============================================================

class Timetable(TimestampMixin, db.Model):

    __tablename__ = "timetable"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Department whose timetable this class belongs to
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False,
        index=True
    )

    # Subject being taught
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False,
        index=True
    )

    # Assigned faculty
    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teachers.id"),
        nullable=False,
        index=True
    )

    # Semester
    semester = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )

    # Section A / B / C
    section = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )

    # lecture / lab / tutorial / seminar
    class_type = db.Column(
        db.String(30),
        nullable=False,
        default="lecture"
    )

    # Monday / Tuesday / etc.
    day_of_week = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    room = db.Column(
        db.String(120),
        nullable=False
    )

    # HOD/Admin user who created timetable entry
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    department = db.relationship(
        "Department"
    )

    subject = db.relationship(
        "Subject"
    )

    teacher = db.relationship(
        "Teacher"
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by]
    )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    def to_dict(self):

        return {
            "id": self.id,

            "department_id": self.department_id,

            "department": (
                self.department.name
                if self.department
                else None
            ),

            "subject_id": self.subject_id,

            "subject": (
                self.subject.name
                if self.subject
                else None
            ),

            "subject_code": (
                self.subject.code
                if self.subject
                else None
            ),

            "teacher_id": self.teacher_id,

            "faculty": (
                self.teacher.full_name
                if self.teacher
                else None
            ),

            "teacher_code": (
                self.teacher.teacher_code
                if self.teacher
                else None
            ),

            "semester": self.semester,

            "section": self.section,

            "class_type": self.class_type,

            "day_of_week": self.day_of_week,

            "start_time": (
                self.start_time.strftime("%H:%M")
                if self.start_time
                else None
            ),

            "end_time": (
                self.end_time.strftime("%H:%M")
                if self.end_time
                else None
            ),

            "room": self.room,

            "created_by": self.created_by,

            "created_by_name": (
                self.creator.username
                if self.creator
                else None
            ),

            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),

            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            )
        }


# ============================================================
# ATTENDANCE
# ============================================================

class Attendance(TimestampMixin, db.Model):

    __tablename__ = "attendance"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "students.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id")
    )

    date = db.Column(
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="present"
    )

    marked_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    student = db.relationship("Student")
    subject = db.relationship("Subject")

    def to_dict(self):

        return {
            "id": self.id,
            "student_id": self.student_id,
            "student": (
                self.student.full_name
                if self.student
                else None
            ),
            "subject_id": self.subject_id,
            "subject": (
                self.subject.name
                if self.subject
                else None
            ),
            "date": self.date.isoformat(),
            "status": self.status,
            "marked_by": self.marked_by,
        }

# ============================================================
# FACULTY ATTENDANCE
# ============================================================

class FacultyAttendance(TimestampMixin, db.Model):

    __tablename__ = "faculty_attendance"

    __table_args__ = (
        db.UniqueConstraint(
            "faculty_user_id",
            "date",
            name="uq_faculty_attendance_user_date"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Teacher or HOD user id
    faculty_user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # Department of faculty member
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False,
        index=True
    )

    # Attendance date
    date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )

    # present / absent / leave
    status = db.Column(
        db.String(20),
        nullable=False,
        default="present"
    )

    # Optional remarks
    remarks = db.Column(
        db.Text
    )

    # User who marked the attendance
    marked_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    faculty = db.relationship(
        "User",
        foreign_keys=[faculty_user_id]
    )

    department = db.relationship(
        "Department"
    )

    marker = db.relationship(
        "User",
        foreign_keys=[marked_by]
    )

    # --------------------------------------------------------
    # CONVERT TO JSON
    # --------------------------------------------------------

    def to_dict(self):

        faculty_name = None
        faculty_code = None
        faculty_role = None

        if self.faculty:

            faculty_role = self.faculty.role

            if self.faculty.teacher:

                faculty_name = (
                    self.faculty.teacher.full_name
                )

                faculty_code = (
                    self.faculty.teacher.teacher_code
                )

            elif self.faculty.hod:

                faculty_name = (
                    self.faculty.hod.full_name
                )

                faculty_code = (
                    self.faculty.hod.hod_code
                )

        return {

            "id": self.id,

            "faculty_user_id": self.faculty_user_id,

            "faculty_code": faculty_code,

            "faculty_name": faculty_name,

            "role": faculty_role,

            "department_id": self.department_id,

            "department": (
                self.department.name
                if self.department
                else None
            ),

            "date": (
                self.date.isoformat()
                if self.date
                else None
            ),

            "status": self.status,

            "remarks": self.remarks,

            "marked_by": self.marked_by,

            "marked_by_name": (
                self.marker.username
                if self.marker
                else None
            ),

            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),

            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            )
        }

# ============================================================
# ASSIGNMENT
# ============================================================

class Assignment(TimestampMixin, db.Model):

    __tablename__ = "assignments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id")
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teachers.id")
    )

    due_date = db.Column(
        db.Date
    )

    max_marks = db.Column(
        db.Integer,
        default=100
    )

    attachment_url = db.Column(
        db.String(255)
    )

    subject = db.relationship("Subject")
    teacher = db.relationship("Teacher")

    submissions = db.relationship(
        "AssignmentSubmission",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "subject_id": self.subject_id,
            "subject": (
                self.subject.name
                if self.subject
                else None
            ),
            "teacher_id": self.teacher_id,
            "due_date": (
                self.due_date.isoformat()
                if self.due_date
                else None
            ),
            "max_marks": self.max_marks,
            "attachment_url": self.attachment_url,
            "submission_count": len(self.submissions),
        }


# ============================================================
# ASSIGNMENT SUBMISSION
# ============================================================

class AssignmentSubmission(TimestampMixin, db.Model):

    __tablename__ = "assignment_submissions"

    __table_args__ = (
        db.UniqueConstraint(
            "assignment_id",
            "student_id",
            name="uq_submission"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "assignments.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "students.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    file_url = db.Column(
        db.String(255)
    )

    note = db.Column(
        db.Text
    )

    marks = db.Column(
        db.Integer
    )

    feedback = db.Column(
        db.Text
    )

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    assignment = db.relationship(
        "Assignment",
        back_populates="submissions"
    )

    student = db.relationship("Student")

    def to_dict(self):

        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "student_id": self.student_id,
            "student": (
                self.student.full_name
                if self.student
                else None
            ),
            "file_url": self.file_url,
            "note": self.note,
            "marks": self.marks,
            "feedback": self.feedback,
            "submitted_at": (
                self.submitted_at.isoformat()
                if self.submitted_at
                else None
            ),
        }


# ============================================================
# STUDY MATERIAL
# ============================================================

class StudyMaterial(TimestampMixin, db.Model):

    __tablename__ = "study_materials"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id")
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teachers.id")
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    semester = db.Column(
        db.String(20)
    )

    file_url = db.Column(
        db.String(255)
    )

    subject = db.relationship("Subject")

    def to_dict(self):

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "subject_id": self.subject_id,
            "subject": (
                self.subject.name
                if self.subject
                else None
            ),
            "teacher_id": self.teacher_id,
            "department_id": self.department_id,
            "semester": self.semester,
            "file_url": self.file_url,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# ACADEMIC EVENT
# ============================================================

class AcademicEvent(TimestampMixin, db.Model):

    __tablename__ = "academic_events"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    event_type = db.Column(
        db.String(60),
        default="event"
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    def to_dict(self):

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "start_date": self.start_date.isoformat(),
            "end_date": (
                self.end_date.isoformat()
                if self.end_date
                else None
            ),
            "department_id": self.department_id,
            "created_by": self.created_by,
        }


# ============================================================
# PERFORMANCE RECORD
# ============================================================

class PerformanceRecord(TimestampMixin, db.Model):

    __tablename__ = "performance_records"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id")
    )

    term = db.Column(
        db.String(40)
    )

    score = db.Column(
        db.Numeric(6, 2)
    )

    max_score = db.Column(
        db.Numeric(6, 2),
        default=100
    )

    grade = db.Column(
        db.String(5)
    )

    remarks = db.Column(
        db.Text
    )

    subject = db.relationship("Subject")

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "subject_id": self.subject_id,
            "subject": (
                self.subject.name
                if self.subject
                else None
            ),
            "term": self.term,
            "score": (
                float(self.score)
                if self.score is not None
                else None
            ),
            "max_score": (
                float(self.max_score)
                if self.max_score is not None
                else None
            ),
            "grade": self.grade,
            "remarks": self.remarks,
        }


# ============================================================
# LEAVE REQUEST
# ============================================================

class LeaveRequest(TimestampMixin, db.Model):

    __tablename__ = "leave_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "teachers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    leave_type = db.Column(
        db.String(60),
        nullable=False
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False,
        index=True
    )

    hod_remarks = db.Column(
        db.Text
    )

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    reviewed_at = db.Column(
        db.DateTime
    )

    teacher = db.relationship(
        "Teacher",
        backref="leave_requests"
    )

    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    def to_dict(self):

        return {
            "id": self.id,

            "teacher_id": self.teacher_id,

            "teacher_name": (
                self.teacher.full_name
                if self.teacher
                else None
            ),

            "teacher_code": (
                self.teacher.teacher_code
                if self.teacher
                else None
            ),

            "department_id": (
                self.teacher.department_id
                if self.teacher
                else None
            ),

            "department": (
                self.teacher.department.name
                if self.teacher
                and self.teacher.department
                else None
            ),

            "leave_type": self.leave_type,

            "start_date": (
                self.start_date.isoformat()
                if self.start_date
                else None
            ),

            "end_date": (
                self.end_date.isoformat()
                if self.end_date
                else None
            ),

            "reason": self.reason,

            "status": self.status,

            "hod_remarks": self.hod_remarks,

            "reviewed_by": self.reviewed_by,

            "reviewed_at": (
                self.reviewed_at.isoformat()
                if self.reviewed_at
                else None
            ),

            "created_at": self.created_at.isoformat(),

            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================
# FACE ENCODING
# ============================================================

class FaceEncoding(TimestampMixin, db.Model):

    __tablename__ = "face_encodings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False
    )

    descriptor = db.Column(
        db.JSON,
        nullable=False
    )

    image_url = db.Column(
        db.String(255)
    )

    user = db.relationship(
        "User",
        back_populates="face"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_url": self.image_url,
            "registered_at": self.created_at.isoformat(),
        }


# ============================================================
# NOTIFICATION
# ============================================================

class Notification(TimestampMixin, db.Model):

    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    message = db.Column(
        db.Text
    )

    category = db.Column(
        db.String(50),
        default="general"
    )

    link = db.Column(
        db.String(1024)
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="notifications"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "link": self.link,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }

# ============================================================
# NOTICE BOARD
# ============================================================

class Notice(TimestampMixin, db.Model):

    __tablename__ = "notices"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Notice heading
    title = db.Column(
        db.String(255),
        nullable=False
    )

    # Full notice content
    message = db.Column(
        db.Text,
        nullable=False
    )

    # general / academic / examination / event / placement
    category = db.Column(
        db.String(50),
        nullable=False,
        default="general"
    )

    # all / teacher / hod / student
    audience = db.Column(
        db.String(50),
        nullable=False,
        default="all"
    )

    # normal / important / urgent
    priority = db.Column(
        db.String(20),
        nullable=False,
        default="normal"
    )

    # draft / published / archived
    status = db.Column(
        db.String(20),
        nullable=False,
        default="published"
    )

    # Optional expiry date
    expiry_date = db.Column(
        db.Date,
        nullable=True
    )

    # Admin/User who created notice
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by]
    )

    def to_dict(self):

        return {

            "id": self.id,

            "title": self.title,

            "message": self.message,

            "category": self.category,

            "audience": self.audience,

            "priority": self.priority,

            "status": self.status,

            "expiry_date": (
                self.expiry_date.isoformat()
                if self.expiry_date
                else None
            ),

            "created_by": self.created_by,

            "created_by_name": (
                self.creator.username
                if self.creator
                else None
            ),

            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),

            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            )
        }

# ============================================================
# PASSWORD RESET TOKEN
# ============================================================

class PasswordResetToken(TimestampMixin, db.Model):

    __tablename__ = "password_reset_tokens"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    token = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    used = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(TimestampMixin, db.Model):

    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    action = db.Column(
        db.String(120),
        nullable=False
    )

    entity = db.Column(
        db.String(80)
    )

    entity_id = db.Column(
        db.Integer
    )

    details = db.Column(
        db.Text
    )

    ip_address = db.Column(
        db.String(60)
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat(),
        }