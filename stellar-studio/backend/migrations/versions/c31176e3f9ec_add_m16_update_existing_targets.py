"""add_target_drz_data

Revision ID: c31176e3f9ec
Revises: xxx
Create Date: 2024-01-30 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import JSON
import uuid
import json

# revision identifiers, used by Alembic
revision = 'c31176e3f9ec'
down_revision = 'xxx'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Vérifier et ajouter les colonnes si nécessaire
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('targets')]
    
    if 'filters' not in columns:
        op.add_column('targets', sa.Column('filters', JSON, nullable=True))
    if 'required_drz_files' not in columns:
        op.add_column('targets', sa.Column('required_drz_files', JSON, nullable=True))
    if 'mosaic_config' not in columns:
        op.add_column('targets', sa.Column('mosaic_config', JSON, nullable=True))

    # 2. Données pour chaque cible
    targets_data = {
        "Eagle Nebula-HST": {
            "filters": {
                "F657N": {"instrument": "WFC3/UVIS", "wavelength": 657, "exposure": 1200},
                "F673N": {"instrument": "WFC3/UVIS", "wavelength": 673, "exposure": 1200},
                "F110W": {"instrument": "WFC3/IR", "wavelength": 1100, "exposure": 900},
                "F160W": {"instrument": "WFC3/IR", "wavelength": 1600, "exposure": 900}
            },
            "required_drz_files": [
                # UVIS F657N (6 positions)
                "hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos1_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos2_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos3_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos4_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos5_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos6_drz.fits",
                
                # UVIS F673N (6 positions)
                "hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos1_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos2_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos3_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos4_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos5_drz.fits",
                "hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos6_drz.fits",
                
                # IR F110W (4 positions)
                "hlsp_heritage_hst_wfc3-ir_m16_f110w_v1_pos1_drz.fits",
                "hlsp_heritage_hst_wfc3-ir_m16_f110w_v1_pos2_drz.fits",
                "hlsp_heritage_hst_wfc3-ir_m16_f110w_v1_pos3_drz.fits",
                "hlsp_heritage_hst_wfc3-ir_m16_f110w_v1_pos4_drz.fits",
                
                # IR F160W (4 positions)
                "hlsp_heritage_hst_wfc3-ir_m16_f160w_v1_pos1_drz.fits",
                "hlsp_heritage_hst_wfc3-ir_m16_f160w_v1_pos2_drz.fits",
                "hlsp_heritage_hst_wfc3-ir_m16_f160w_v1_pos3_drz.fits",
                "hlsp_heritage_hst_wfc3-ir_m16_f160w_v1_pos4_drz.fits"
            ],
            "mosaic_config": {
                "uvis_panels": 6,
                "ir_panels": 4,
                "overlap": 15
            }
        },
        "Sombrero Galaxy": {
            "filters": {
                "F435W": {"instrument": "ACS/WFC", "wavelength": 435, "exposure": 2700},
                "F555W": {"instrument": "ACS/WFC", "wavelength": 555, "exposure": 2000},
                "F625W": {"instrument": "ACS/WFC", "wavelength": 625, "exposure": 1400}
            },
            "required_drz_files": [
                # F435W (4 positions)
                "hst_9714_02_acs_wfc_f435w_j8lw02_drz.fits",
                "hst_9714_03_acs_wfc_f435w_j8lw03_drz.fits",
                "hst_9714_04_acs_wfc_f435w_j8lw04_drz.fits",
                "hst_9714_06_acs_wfc_f435w_j8lw06_drz.fits",
                
                # F555W (4 positions)
                "hst_9714_02_acs_wfc_f555w_j8lw02_drz.fits",
                "hst_9714_03_acs_wfc_f555w_j8lw03_drz.fits",
                "hst_9714_04_acs_wfc_f555w_j8lw04_drz.fits",
                "hst_9714_06_acs_wfc_f555w_j8lw06_drz.fits",
                
                # F625W (4 positions)
                "hst_9714_02_acs_wfc_f625w_j8lw02_drz.fits",
                "hst_9714_03_acs_wfc_f625w_j8lw03_drz.fits",
                "hst_9714_04_acs_wfc_f625w_j8lw04_drz.fits",
                "hst_9714_06_acs_wfc_f625w_j8lw06_drz.fits"
            ],
            "mosaic_config": {
                "positions": ["POS2", "POS3", "POS4", "POS6"],
                "overlap": 15
            }
        },
        "Butterfly Nebula": {
            "filters": {
                "F438W": {"instrument": "WFC3/UVIS", "wavelength": 438, "exposure": 270},
                "F555W": {"instrument": "WFC3/UVIS", "wavelength": 555, "exposure": 42},
                "F814W": {"instrument": "WFC3/UVIS", "wavelength": 814, "exposure": 36}
            },
           "required_drz_files": [
                # F438W (3 positions)
                "ib5741010_pos1_drz.fits",
                "ib5741010_pos2_drz.fits",
                "ib5741010_pos3_drz.fits",
                
                # F555W (3 positions)
                "ib5741020_pos1_drz.fits",
                "ib5741020_pos2_drz.fits",
                "ib5741020_pos3_drz.fits",
                
                # F814W (3 positions)
                "ib5741030_pos1_drz.fits",
                "ib5741030_pos2_drz.fits",
                "ib5741030_pos3_drz.fits"
            ],
            "mosaic_config": {
                "panels": 3,
                "overlap": 10
            }
        },
        "Cigar Galaxy": {
            "filters": {
                "F658N": {"instrument": "ACS/WFC", "wavelength": 658, "exposure": 1100},
                "F160W": {"instrument": "WFC3/IR", "wavelength": 1600, "exposure": 1842},
                "F225W": {"instrument": "WFC3/UVIS", "wavelength": 225, "exposure": 1070}
            },
            "required_drz_files": [
                # ACS/WFC F658N (5 positions)
                "j9e1020q_pos1_drz.fits",
                "j9e1020q_pos2_drz.fits",
                "j9e1020q_pos3_drz.fits",
                "j9e1020q_pos4_drz.fits",
                "j9e1020q_pos5_drz.fits",
                
                # WFC3/IR F160W (5 positions)
                "ibhj01e4q_pos1_drz.fits",
                "ibhj01e4q_pos2_drz.fits",
                "ibhj01e4q_pos3_drz.fits",
                "ibhj01e4q_pos4_drz.fits",
                "ibhj01e4q_pos5_drz.fits",
                
                # WFC3/UVIS F225W (5 positions)
                "ibhj01010_pos1_drz.fits",
                "ibhj01010_pos2_drz.fits",
                "ibhj01010_pos3_drz.fits",
                "ibhj01010_pos4_drz.fits",
                "ibhj01010_pos5_drz.fits"
            ],
            "mosaic_config": {
                "panels": 5,
                "overlap": 12
            }
        },
        "Gabriela Mistral Nebula": {
            "filters": {
                "F550M": {"instrument": "ACS/WFC", "wavelength": 550, "exposure": 654},
                "F658N": {"instrument": "ACS/WFC", "wavelength": 658, "exposure": 1300},
                "F660N": {"instrument": "ACS/WFC", "wavelength": 660, "exposure": 1960}
            },
            "required_drz_files": [
                # F550M (2 positions)
                "j8rh03_f550m_pos1_drz.fits",
                "j8rh03_f550m_pos2_drz.fits",
                
                # F658N (2 positions)
                "j8rh04_f658n_pos1_drz.fits",
                "j8rh04_f658n_pos2_drz.fits",
                
                # F660N (2 positions)
                "j8rh05_f660n_pos1_drz.fits",
                "j8rh05_f660n_pos2_drz.fits"
            ],
            "mosaic_config": {
                "panels": 2,
                "overlap": 10
            }
        },
        "Cartwheel Galaxy": {
            "filters": {
                "F090W": {"instrument": "NIRCam", "wavelength": 900, "exposure": 2748.616},
                "F150W": {"instrument": "NIRCam", "wavelength": 1500, "exposure": 2748.616},
                "F200W": {"instrument": "NIRCam", "wavelength": 2000, "exposure": 2748.616},
                "F770W": {"instrument": "MIRI", "wavelength": 7700, "exposure": 4040.464}
            },
            "required_drz_files": [
                # NIRCam
                "jw02736-o001_t001_nircam_clear-f090w_drz.fits",
                "jw02736-o001_t001_nircam_clear-f150w_drz.fits",
                "jw02736-o001_t001_nircam_clear-f200w_drz.fits",
                "jw02736-o001_t001_nircam_clear-f277w_drz.fits",
                "jw02736-o001_t001_nircam_clear-f356w_drz.fits",
                "jw02736-o001_t001_nircam_clear-f444w_drz.fits",
                
                # MIRI
                "jw02736-o001_t001_miri_f770w_drz.fits",
                "jw02736-o001_t001_miri_f1000w_drz.fits",
                "jw02736-o001_t001_miri_f1280w_drz.fits",
                "jw02736-o001_t001_miri_f1800w_drz.fits"
            ],
            "mosaic_config": {
                "mosaic_type": "full",
                "overlap": 10
            }
        },
        "Phantom Galaxy": {
            "filters": {
                "F115W": {"instrument": "NIRCam", "wavelength": 1150, "exposure": 944.832},
                "F200W": {"instrument": "NIRCam", "wavelength": 2000, "exposure": 4208.816},
                "F770W": {"instrument": "MIRI", "wavelength": 7700, "exposure": 4440.06}
            },
            "required_drz_files": [
                # NIRCam
                "jw02727-o001_t001_nircam_clear-f115w_drz.fits",
                "jw02727-o001_t001_nircam_clear-f150w_drz.fits",
                "jw02727-o001_t001_nircam_clear-f187n_drz.fits",
                "jw02727-o001_t001_nircam_clear-f200w_drz.fits",
                "jw02727-o001_t001_nircam_clear-f277w_drz.fits",
                "jw02727-o001_t001_nircam_clear-f335m_drz.fits",
                "jw02727-o001_t001_nircam_clear-f444w_drz.fits",
                
                # MIRI
                "jw02727-o001_t001_miri_f560w_drz.fits",
                "jw02727-o001_t001_miri_f770w_drz.fits",
                "jw02727-o001_t001_miri_f1000w_drz.fits",
                "jw02727-o001_t001_miri_f1130w_drz.fits",
                "jw02727-o001_t001_miri_f2100w_drz.fits"
            ],
            "mosaic_config": {
                "mosaic_type": "full",
                "overlap": 10
            }
        },
        "Stephan's Quintet": {
            "filters": {
                "F090W": {"instrument": "NIRCam", "wavelength": 900, "exposure": 7086.27},
                "F150W": {"instrument": "NIRCam", "wavelength": 1500, "exposure": 7086.27},
                "F770W": {"instrument": "MIRI", "wavelength": 7700, "exposure": 2708.432}
            },
            "required_drz_files": [
                # NIRCam
                "jw02734-o001_t001_nircam_clear-f090w_drz.fits",
                "jw02734-o001_t001_nircam_clear-f150w_drz.fits",
                "jw02734-o001_t001_nircam_clear-f200w_drz.fits",
                "jw02734-o001_t001_nircam_clear-f277w_drz.fits",
                "jw02734-o001_t001_nircam_clear-f356w_drz.fits",
                "jw02734-o001_t001_nircam_clear-f444w_drz.fits",
                
                # MIRI
                "jw02734-o001_t001_miri_f770w_drz.fits",
                "jw02734-o001_t001_miri_f1000w_drz.fits",
                "jw02734-o001_t001_miri_f1500w_drz.fits"
            ],
            "mosaic_config": {
                "mosaic_type": "full",
                "overlap": 10
            }
        },
        "Southern Ring Nebula": {
            "filters": {
                "F090W": {"instrument": "NIRCam", "wavelength": 900, "exposure": 1460.2},
                "F187N": {"instrument": "NIRCam", "wavelength": 1870, "exposure": 2319.144},
                "F770W": {"instrument": "MIRI", "wavelength": 7700, "exposure": 2708.432}
            },
            "required_drz_files": [
                # NIRCam
                "jw02733-o001_t001_nircam_clear-f090w_drz.fits",
                "jw02733-o001_t001_nircam_clear-f187n_drz.fits",
                "jw02733-o001_t001_nircam_clear-f212n_drz.fits",
                "jw02733-o001_t001_nircam_clear-f356w_drz.fits",
                "jw02733-o001_t001_nircam_clear-f444w_drz.fits",
                "jw02733-o001_t001_nircam_clear-f405n_drz.fits",
                "jw02733-o001_t001_nircam_clear-f470n_drz.fits",
                
                # MIRI
                "jw02733-o001_t001_miri_f770w_drz.fits",
                "jw02733-o001_t001_miri_f1130w_drz.fits",
                "jw02733-o001_t001_miri_f1280w_drz.fits",
                "jw02733-o001_t001_miri_f1800w_drz.fits"
            ],
            "mosaic_config": {
                "mosaic_type": "full",
                "overlap": 10
            }
        }
    }

    # 3. Update des cibles existantes
    connection = op.get_bind()
    for target_name, data in targets_data.items():
        sql = text("""
            UPDATE targets 
            SET 
                filters = :filters,
                required_drz_files = :required_drz_files,
                mosaic_config = :mosaic_config
            WHERE name = :name
        """)
        
        connection.execute(
            sql,
            {
                "filters": json.dumps(data['filters']),
                "required_drz_files": json.dumps(data['required_drz_files']),
                "mosaic_config": json.dumps(data['mosaic_config']),
                "name": target_name.split('-')[0]
            }
        )

    # 4. Ajout de M16 JWST
    sql_insert = text("""
        INSERT INTO targets 
        (id, name, description, telescope_id, coordinates_ra, coordinates_dec, 
        object_type, filters, required_drz_files, mosaic_config)
        VALUES 
        (:id, :name, :description, :telescope_id, :coordinates_ra, :coordinates_dec,
        :object_type, :filters, :required_drz_files, :mosaic_config)
    """)

    m16_jwst_data = {
        "id": str(uuid.uuid4()),
        "name": "Eagle Nebula",
        "description": "Famous for the Pillars of Creation",
        "telescope_id": "JWST",
        "coordinates_ra": "18 18 48",
        "coordinates_dec": "-13 49 00",
        "object_type": "nebula",
        "filters": json.dumps({
            "F090W": {"instrument": "NIRCam", "wavelength": 900, "exposure": 3221.04},
            "F187N": {"instrument": "NIRCam", "wavelength": 1870, "exposure": 3221.04},
            "F200W": {"instrument": "NIRCam", "wavelength": 2000, "exposure": 3221.04},
            "F335M": {"instrument": "NIRCam", "wavelength": 3350, "exposure": 3221.04},
            "F444W": {"instrument": "NIRCam", "wavelength": 4440, "exposure": 3221.04},
            "F405N": {"instrument": "NIRCam", "wavelength": 4050, "exposure": 3221.04},
            "F470N": {"instrument": "NIRCam", "wavelength": 4700, "exposure": 3221.04},
            "F770W": {"instrument": "MIRI", "wavelength": 7700, "exposure": 2708.432},
            "F1130W": {"instrument": "MIRI", "wavelength": 11300, "exposure": 2708.432},
            "F1280W": {"instrument": "MIRI", "wavelength": 12800, "exposure": 2708.432},
            "F1800W": {"instrument": "MIRI", "wavelength": 18000, "exposure": 2708.432}
        }),
        "required_drz_files": json.dumps([
            "jw02739-o001_t001_nircam_clear-f090w_drz.fits",
            "jw02739-o001_t001_nircam_clear-f187n_drz.fits",
            "jw02739-o001_t001_nircam_clear-f200w_drz.fits",
            "jw02739-o001_t001_nircam_clear-f335m_drz.fits",
            "jw02739-o001_t001_nircam_clear-f444w_drz.fits",
            "jw02739-o001_t001_nircam_clear-f405n_drz.fits",
            "jw02739-o001_t001_nircam_clear-f470n_drz.fits",
            "jw02739-o002_t001_miri_f770w_drz.fits",
            "jw02739-o002_t001_miri_f1130w_drz.fits",
            "jw02739-o002_t001_miri_f1280w_drz.fits",
            "jw02739-o002_t001_miri_f1800w_drz.fits"
        ]),
        "mosaic_config": json.dumps({
            "mosaic_type": "full",
            "overlap": 10
        })
    }

    connection.execute(sql_insert, m16_jwst_data)

def downgrade():
    # Suppression de M16 JWST
    op.execute("DELETE FROM targets WHERE name = 'Eagle Nebula' AND telescope_id = 'JWST'")
    
    # Suppression des colonnes
    op.drop_column('targets', 'filters')
    op.drop_column('targets', 'required_drz_files')
    op.drop_column('targets', 'mosaic_config')
