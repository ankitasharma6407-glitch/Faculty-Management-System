"""add leave requests

Revision ID: 966b2de4e518
Revises:
Create Date: 2026-08-15 13:59:46.243509

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "966b2de4e518"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "leave_requests",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "teacher_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "leave_type",
            sa.String(length=60),
            nullable=False
        ),

        sa.Column(
            "start_date",
            sa.Date(),
            nullable=False
        ),

        sa.Column(
            "end_date",
            sa.Date(),
            nullable=False
        ),

        sa.Column(
            "reason",
            sa.Text(),
            nullable=False
        ),

        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            "hod_remarks",
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            "reviewed_by",
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            "reviewed_at",
            sa.DateTime(),
            nullable=True
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
            ["reviewed_by"],
            ["users.id"]
        ),

        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["teachers.id"],
            ondelete="CASCADE"
        ),

        sa.PrimaryKeyConstraint(
            "id"
        )
    )

    op.create_index(
        "ix_leave_requests_status",
        "leave_requests",
        ["status"],
        unique=False
    )

    op.create_index(
        "ix_leave_requests_teacher_id",
        "leave_requests",
        ["teacher_id"],
        unique=False
    )


def downgrade():

    op.drop_index(
        "ix_leave_requests_teacher_id",
        table_name="leave_requests"
    )

    op.drop_index(
        "ix_leave_requests_status",
        table_name="leave_requests"
    )

    op.drop_table(
        "leave_requests"
    )