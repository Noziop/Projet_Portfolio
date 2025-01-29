"""seed_initial_data

Revision ID: xxx
Revises: yyy
Create Date: 2025-01-29 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.mysql import JSON
import json
from datetime import datetime, timezone
import uuid
import os
from dotenv import load_dotenv
from app.core.security import get_password_hash

# Chargement des variables d'environnement
load_dotenv()

# revision identifiers, used by Alembic
revision = 'xxx'
down_revision = 'b21176e3f8ec'
branch_labels = None
depends_on = None

def upgrade():
    # Récupération et hashage sécurisé du mot de passe admin
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise ValueError("ADMIN_PASSWORD must be set in environment variables")
    
    admin_password_hash = get_password_hash(admin_password)

    # Définition des tables
    users = table('users',
        column('id', sa.String),
        column('email', sa.String),
        column('username', sa.String),
        column('hashed_password', sa.String),
        column('firstname', sa.String),
        column('lastname', sa.String),
        column('level', sa.String),
        column('role', sa.String),
        column('created_at', sa.DateTime),
        column('last_login', sa.DateTime),
        column('is_active', sa.Boolean)
    )

    telescopes = table('space_telescopes',
        column('id', sa.String),
        column('name', sa.String),
        column('description', sa.String),
        column('aperture', sa.String),
        column('focal_length', sa.String),
        column('location', sa.String),
        column('instruments', JSON),
        column('api_endpoint', sa.String)
    )

    targets = table('targets',
        column('id', sa.String),
        column('name', sa.String),
        column('description', sa.String),
        column('telescope_id', sa.String),
        column('coordinates_ra', sa.String),
        column('coordinates_dec', sa.String),
        column('object_type', sa.String)
    )

    # Seed admin user avec le mot de passe depuis les variables d'environnement
    op.bulk_insert(users, [{
        'id': str(uuid.uuid4()),
        'email': 'admin@stellarstudio.com',
        'username': 'admin',
        'hashed_password': admin_password_hash,
        'firstname': None,
        'lastname': None,
        'level': 'BEGINNER',
        'role': 'ADMIN',
        'created_at': datetime.now(timezone.utc),
        'last_login': None,
        'is_active': True
    }])

    # Seed telescopes
    op.bulk_insert(telescopes, [
        {
            'id': 'HST',
            'name': 'Hubble Space Telescope',
            'description': "NASA's visible/UV/near-IR telescope",
            'aperture': '2.4m',
            'focal_length': '57.6m',
            'location': 'Low Earth Orbit',
            'instruments': json.dumps({
                'WFC3': 'Wide Field Camera 3',
                'COS': 'Cosmic Origins Spectrograph'
            }),
            'api_endpoint': '/api/v1/telescopes/hst'
        },
        {
            'id': 'JWST',
            'name': 'James Webb Space Telescope',
            'description': "NASA's infrared flagship telescope",
            'aperture': '6.5m',
            'focal_length': '131.4m',
            'location': 'L2 Lagrange Point',
            'instruments': json.dumps({
                'NIRCam': 'Near Infrared Camera',
                'MIRI': 'Mid-Infrared Instrument'
            }),
            'api_endpoint': '/api/v1/telescopes/jwst'
        }
    ])

    # Seed targets
    targets_data = [
        # HST Targets
        {
            'id': str(uuid.uuid4()),
            'name': 'Eagle Nebula',
            'description': 'Famous for the Pillars of Creation',
            'telescope_id': 'HST',
            'coordinates_ra': '18 18 48',
            'coordinates_dec': '-13 49 00',
            'object_type': 'nebula'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Sombrero Galaxy',
            'description': 'Iconic galaxy with a bright nucleus',
            'telescope_id': 'HST',
            'coordinates_ra': '12 39 59',
            'coordinates_dec': '-11 37 23',
            'object_type': 'galaxy'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Butterfly Nebula',
            'description': 'Spectacular planetary nebula',
            'telescope_id': 'HST',
            'coordinates_ra': '17 13 44',
            'coordinates_dec': '-37 06 16',
            'object_type': 'nebula'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Cigar Galaxy',
            'description': 'Galaxy with active star formation',
            'telescope_id': 'HST',
            'coordinates_ra': '09 55 52',
            'coordinates_dec': '+69 40 47',
            'object_type': 'galaxy'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Gabriela Mistral Nebula',
            'description': 'Colorful nebula',
            'telescope_id': 'HST',
            'coordinates_ra': '10 37 19',
            'coordinates_dec': '-58 38 00',
            'object_type': 'nebula'
        },
        # JWST Targets
        {
            'id': str(uuid.uuid4()),
            'name': 'Cartwheel Galaxy',
            'description': 'Ring galaxy formed by collision',
            'telescope_id': 'JWST',
            'coordinates_ra': '00 37 41',
            'coordinates_dec': '-33 42 59',
            'object_type': 'galaxy'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Phantom Galaxy',
            'description': 'Perfect spiral galaxy',
            'telescope_id': 'JWST',
            'coordinates_ra': '01 36 42',
            'coordinates_dec': '+15 47 01',
            'object_type': 'galaxy'
        },
        {
            'id': str(uuid.uuid4()),
            'name': "Stephan's Quintet",
            'description': 'Compact group of five galaxies',
            'telescope_id': 'JWST',
            'coordinates_ra': '22 35 58',
            'coordinates_dec': '+33 57 36',
            'object_type': 'galaxy'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Southern Ring Nebula',
            'description': 'Spectacular planetary nebula',
            'telescope_id': 'JWST',
            'coordinates_ra': '10 07 02',
            'coordinates_dec': '-40 26 11',
            'object_type': 'nebula'
        }
    ]

    op.bulk_insert(targets, targets_data)

def downgrade():
    # Suppression dans l'ordre inverse des insertions
    op.execute('DELETE FROM targets')
    op.execute('DELETE FROM space_telescopes')
    op.execute('DELETE FROM users WHERE username = "admin"')
