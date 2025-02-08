"""refonte_architecture_stellar

Revision ID: 0b9fc42f03a3
Revises: c31176e3f9ec
Create Date: 2025-02-05 10:48:39.431684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b9fc42f03a3'
down_revision: Union[str, None] = 'c31176e3f9ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 0. Supprimer la table observations
    op.drop_table('observations')

    # 1. Créer la table filters
    op.create_table(
        'filters',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('telescope_id', sa.String(36), sa.ForeignKey('space_telescopes.id'), nullable=False),
        sa.Column('wavelength', sa.Float),
        sa.Column('description', sa.Text),
    )

    # 2. Créer la table presets
    op.create_table(
        'presets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('processing_params', sa.JSON),
        sa.Column('telescope_id', sa.String(36), sa.ForeignKey('space_telescopes.id'), nullable=False),
    )

    # 3. Créer la table preset_filters
    op.create_table(
        'preset_filters',
        sa.Column('preset_id', sa.String(36), sa.ForeignKey('presets.id'), nullable=False),
        sa.Column('filter_id', sa.String(36), sa.ForeignKey('filters.id'), nullable=False),
        sa.PrimaryKeyConstraint('preset_id', 'filter_id')
    )

    # 4. Créer la table target_files
    op.create_table(
        'target_files',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('target_id', sa.String(36), sa.ForeignKey('targets.id'), nullable=False),
        sa.Column('filter_id', sa.String(36), sa.ForeignKey('filters.id'), nullable=False),
        sa.Column('file_path', sa.String(255), nullable=False),
        sa.Column('file_size', sa.BigInteger),
        sa.Column('in_minio', sa.Boolean, default=False),
        sa.Column('fits_metadata', sa.JSON),
    )

    # 5. Modifier la table targets
    op.add_column('targets', sa.Column('available_presets', sa.JSON))
    op.add_column('targets', sa.Column('processing_config', sa.JSON))
    op.add_column('targets', sa.Column('status', sa.Enum('READY', 'NEEDS_DOWNLOAD', 'PROCESSING'), server_default='NEEDS_DOWNLOAD'))

    # 6. Supprimer les colonnes obsolètes
    op.drop_column('targets', 'extra_data')
    op.drop_column('targets', 'mosaic_config')

    # 7. Modifier processing_jobs
    op.add_column('processing_jobs', sa.Column('target_id', sa.String(36), sa.ForeignKey('targets.id')))
    op.add_column('processing_jobs', sa.Column('preset_id', sa.String(36), sa.ForeignKey('presets.id')))


def downgrade():
    # Rollback des modifications
    op.drop_table('target_files')
    op.drop_table('preset_filters')
    op.drop_table('presets')
    op.drop_table('filters')
    op.drop_column('targets', 'status')
    op.drop_column('targets', 'processing_config')
    op.drop_column('targets', 'available_presets')
    op.drop_column('processing_jobs', 'preset_id')
    op.drop_column('processing_jobs', 'target_id')
    
    # Recréer les colonnes supprimées
    op.add_column('targets', sa.Column('extra_data', sa.JSON))
    op.add_column('targets', sa.Column('mosaic_config', sa.JSON))

    # Recréer la table observations
    op.create_table(
        'observations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('telescope_id', sa.String(36), sa.ForeignKey('space_telescopes.id')),
        sa.Column('target_id', sa.String(255), sa.ForeignKey('targets.id')),
        sa.Column('coordinates_ra', sa.String(50), nullable=False),
        sa.Column('coordinates_dec', sa.String(50), nullable=False),
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('exposure_time', sa.Integer, nullable=False),
        sa.Column('instrument', sa.String(100), nullable=False),
        sa.Column('filters', sa.JSON),
        sa.Column('fits_files', sa.JSON),
        sa.Column('preview_url', sa.String(255))
    )
