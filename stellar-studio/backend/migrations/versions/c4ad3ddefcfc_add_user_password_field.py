"""add_user_password_field

Revision ID: c4ad3ddefcfc
Revises: 0b9fc42f03a3
Create Date: 2024-02-05 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import text

# revision identifiers
revision = 'c4ad3ddefcfc'
down_revision = '0b9fc42f03a3'
branch_labels = None
depends_on = None

def upgrade():
    # Simplement ajouter le champ password
    op.add_column('users', sa.Column('hashed_password', sa.String(255), nullable=False))

def downgrade():
    # Supprimer le champ password
    op.drop_column('users', 'hashed_password')
