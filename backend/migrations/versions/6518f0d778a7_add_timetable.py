"""add timetable

Revision ID: 6518f0d778a7
Revises: 966b2de4e518
Create Date: 2026-08-16 08:12:06.080882

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6518f0d778a7"
down_revision = "966b2de4e518"
branch_labels = None
depends_on = None


def upgrade():

    # ============================================================
    # CREATE TIMETABLE TABLE
    # ============================================================

    op.create_table(
        "timetable",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "department_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "subject_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "teacher_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "semester",
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            "section",
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            "class_type",
            sa.String(length=30),
            nullable=False
        ),

        sa.Column(
            "day_of_week",
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            "start_time",
            sa.Time(),
            nullable=False
        ),

        sa.Column(
            "end_time",
            sa.Time(),
            nullable=False
        ),

        sa.Column(
            "room",
            sa.String(length=120),
            nullable=False
        ),

        sa.Column(
            "created_by",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"]
        ),

        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"]
        ),

        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"]
        ),

        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["teachers.id"]
        ),

        sa.PrimaryKeyConstraint(
            "id"
        )
    )


    # ============================================================
    # TIMETABLE INDEXES
    # ============================================================

    with op.batch_alter_table(
        "timetable",
        schema=None
    ) as batch_op:

        batch_op.create_index(
            batch_op.f(
                "ix_timetable_day_of_week"
            ),
            ["day_of_week"],
            unique=False
        )

        batch_op.create_index(
            batch_op.f(
                "ix_timetable_department_id"
            ),
            ["department_id"],
            unique=False
        )

        batch_op.create_index(
            batch_op.f(
                "ix_timetable_section"
            ),
            ["section"],
            unique=False
        )

        batch_op.create_index(
            batch_op.f(
                "ix_timetable_semester"
            ),
            ["semester"],
            unique=False
        )

        batch_op.create_index(
            batch_op.f(
                "ix_timetable_subject_id"
            ),
            ["subject_id"],
            unique=False
        )

        batch_op.create_index(
            batch_op.f(
                "ix_timetable_teacher_id"
            ),
            ["teacher_id"],
            unique=False
        )


def downgrade():

    # ============================================================
    # REMOVE TIMETABLE INDEXES
    # ============================================================

    with op.batch_alter_table(
        "timetable",
        schema=None
    ) as batch_op:

        batch_op.drop_index(
            batch_op.f(
                "ix_timetable_teacher_id"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_timetable_subject_id"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_timetable_semester"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_timetable_section"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_timetable_department_id"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_timetable_day_of_week"
            )
        )


    # ============================================================
    # DROP TIMETABLE TABLE
    # ============================================================

    op.drop_table(
        "timetable"
    )