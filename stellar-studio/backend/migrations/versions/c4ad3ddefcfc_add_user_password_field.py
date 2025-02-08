"""add_user_password_field

Revision ID: c4ad3ddefcfc
Revises: 0b9fc42f03a3
Create Date: 2024-02-05 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = 'c4ad3ddefcfc'
down_revision = '0b9fc42f03a3'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Supprimer les contraintes FK existantes
    op.drop_constraint('fk_processing_jobs_preset_id', 'processing_jobs', type_='foreignkey')
    op.drop_constraint('fk_preset_filters_preset_id', 'preset_filters', type_='foreignkey')
    op.drop_constraint('fk_preset_filters_filter_id', 'preset_filters', type_='foreignkey')
    
    # 2. Supprimer les tables dans l'ordre
    op.drop_table('preset_filters')
    op.drop_table('presets')
    
    # 3. Recréer la table presets avec la nouvelle structure
    op.create_table(
        'presets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('processing_params', sa.JSON),
        sa.Column('telescope_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['telescope_id'], ['space_telescopes.id']),
    )
    
    # 4. Recréer la table de liaison preset_filters
    op.create_table(
        'preset_filters',
        sa.Column('preset_id', sa.String(36)),
        sa.Column('filter_id', sa.String(36)),
        sa.ForeignKeyConstraint(['preset_id'], ['presets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['filter_id'], ['filters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('preset_id', 'filter_id')
    )
    
    # 5. Ajouter le champ hashed_password à users
    op.add_column('users', sa.Column('hashed_password', sa.String(255), nullable=False))
    
    # 6. Recréer les contraintes FK pour processing_jobs
    op.create_foreign_key(
        'fk_processing_jobs_preset_id',
        'processing_jobs', 'presets',
        ['preset_id'], ['id'],
        ondelete='SET NULL'
    )

def downgrade():
    # 1. Supprimer les contraintes
    op.drop_constraint('fk_processing_jobs_preset_id', 'processing_jobs', type_='foreignkey')
    
    # 2. Supprimer le champ hashed_password
    op.drop_column('users', 'hashed_password')
    
    # 3. Supprimer les tables dans l'ordre inverse
    op.drop_table('preset_filters')
    op.drop_table('presets')
    
    # 4. Recréer les tables dans leur état initial
    op.create_table(
        'presets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('processing_params', sa.JSON),
        sa.Column('telescope_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['telescope_id'], ['space_telescopes.id']),
    )
    
    # 5. Recréer les contraintes originales
    op.create_foreign_key(
        'fk_processing_jobs_preset_id',
        'processing_jobs', 'presets',
        ['preset_id'], ['id']
    )
