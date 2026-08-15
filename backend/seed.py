from datetime import date

from app import create_app
from app.extensions import db
from app.models import (
    Department,
    Hod,
    Recruiter,
    Student,
    Teacher,
    User,
)

app = create_app()


def make_user(username, email, role, password):
    user = User(
        username=username,
        email=email,
        role=role
    )
    user.set_password(password)

    db.session.add(user)
    db.session.flush()

    return user


def run():
    with app.app_context():

        # Create tables if they don't already exist
        db.create_all()

        # Prevent duplicate seed data
        if User.query.filter_by(username="admin").first():
            print("Database already seeded.")
            return

        # ==========================
        # ADMIN
        # ==========================

        admin = make_user(
            "admin",
            "admin@fmps.edu",
            "admin",
            "Admin@123"
        )

        # ==========================
        # DEPARTMENTS
        # ==========================

        cse = Department(
            name="Computer Science",
            code="CSE",
            description="Computer Science and Engineering"
        )

        ece = Department(
            name="Electronics",
            code="ECE",
            description="Electronics and Communication Engineering"
        )

        db.session.add_all([cse, ece])
        db.session.flush()

        # ==========================
        # HOD
        # ==========================

        hod_user = make_user(
            "hod.cse",
            "hod.cse@fmps.edu",
            "hod",
            "Password@123"
        )

        hod = Hod(
            user_id=hod_user.id,
            hod_code="HOD001",
            full_name="Dr. Anita Sharma",
            department_id=cse.id,
            qualification="Ph.D Computer Science",
            experience_years=15,
            joining_date=date(2012, 7, 1),
            phone="9876543210"
        )

        # ==========================
        # TEACHER
        # ==========================

        teacher_user = make_user(
            "rkumar",
            "rkumar@fmps.edu",
            "teacher",
            "Password@123"
        )

        teacher = Teacher(
            user_id=teacher_user.id,
            teacher_code="TCH001",
            full_name="Rahul Kumar",
            department_id=cse.id,
            designation="Assistant Professor",
            qualification="M.Tech",
            experience_years=6,
            salary=65000,
            joining_date=date(2019, 8, 12),
            phone="9812345670"
        )

        # ==========================
        # STUDENT
        # ==========================

        student_user = make_user(
            "s21cse01",
            "priya@fmps.edu",
            "student",
            "Password@123"
        )

        student = Student(
            user_id=student_user.id,
            student_code="STU001",
            roll_number="21CSE001",
            full_name="Priya Verma",
            department_id=cse.id,
            course="B.Tech CSE",
            semester="5",
            section="A",
            guardian_name="Suresh Verma",
            guardian_phone="9800011122",
            admission_date=date(2021, 8, 1)
        )

        # ==========================
        # RECRUITER
        # ==========================

        recruiter_user = make_user(
            "techcorp",
            "hr@techcorp.com",
            "recruiter",
            "Password@123"
        )

        recruiter = Recruiter(
            user_id=recruiter_user.id,
            recruiter_code="REC001",
            full_name="Neha Gupta",
            company_name="TechCorp Solutions",
            designation="HR Manager",
            phone="9700011122"
        )

        db.session.add_all([
            hod,
            teacher,
            student,
            recruiter
        ])

        db.session.commit()

        print("===================================")
        print("Database seeded successfully!")
        print("===================================")
        print()
        print("ADMIN")
        print("Username: admin")
        print("Password: Admin@123")
        print()
        print("HOD")
        print("Username: hod.cse")
        print("Password: Password@123")
        print()
        print("TEACHER")
        print("Username: rkumar")
        print("Password: Password@123")
        print()
        print("STUDENT")
        print("Username: s21cse01")
        print("Password: Password@123")
        print()
        print("RECRUITER")
        print("Username: techcorp")
        print("Password: Password@123")
        print("===================================")


if __name__ == "__main__":
    run()