"""initial_migration

Revision ID: 86dc0947d88d
Revises: 
Create Date: 2025-01-26 16:32:52.504508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '86dc0947d88d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('space_telescopes',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('aperture', sa.String(length=50), nullable=False),
    sa.Column('focal_length', sa.String(length=50), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=False),
    sa.Column('instruments', sa.JSON(), nullable=True),
    sa.Column('api_endpoint', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', mysql.CHAR(length=36), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('firstname', sa.String(length=100), nullable=True),
    sa.Column('lastname', sa.String(length=100), nullable=True),
    sa.Column('level', sa.Enum('BEGINNER', 'INTERMEDIATE', 'ADVANCED', name='userlevel'), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('workflows',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('steps', sa.JSON(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('target_type', sa.String(length=100), nullable=False),
    sa.Column('required_filters', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('observations',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('telescope_id', sa.String(length=36), nullable=True),
    sa.Column('target_id', sa.String(length=255), nullable=True),
    sa.Column('coordinates_ra', sa.String(length=50), nullable=False),
    sa.Column('coordinates_dec', sa.String(length=50), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('exposure_time', sa.Integer(), nullable=False),
    sa.Column('instrument', sa.String(length=100), nullable=False),
    sa.Column('filters', sa.JSON(), nullable=True),
    sa.Column('fits_files', sa.JSON(), nullable=True),
    sa.Column('preview_url', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['telescope_id'], ['space_telescopes.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('processing_jobs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('telescope_id', sa.String(length=36), nullable=False),
    sa.Column('workflow_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='jobstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('result_url', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['telescope_id'], ['space_telescopes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('targets',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('telescope_id', sa.String(length=36), nullable=True),
    sa.Column('coordinates_ra', sa.String(length=50), nullable=False),
    sa.Column('coordinates_dec', sa.String(length=50), nullable=False),
    sa.Column('object_type', sa.String(length=100), nullable=False),
    sa.Column('extra_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['telescope_id'], ['space_telescopes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tasks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('parameters', sa.JSON(), nullable=False),
    sa.Column('result', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tasks')
    op.drop_table('targets')
    op.drop_table('processing_jobs')
    op.drop_table('observations')
    op.drop_table('workflows')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('space_telescopes')
    # ### end Alembic commands ###
