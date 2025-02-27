# app/db/init_db.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.db.base_class import Base
from app.db.session import engine, AsyncSessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from app.domain.value_objects.user_types import UserRole, UserLevel
from app.domain.value_objects.telescope_types import TelescopeStatus
from app.domain.value_objects.target_types import ObjectType, TargetStatus
from uuid import uuid4
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Récupération des variables d'environnement
ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD
ADMIN_USERNAME = settings.ADMIN_USERNAME

BEGINNER_EMAIL = settings.BEGINNER_EMAIL
BEGINNER_PASSWORD = settings.BEGINNER_PASSWORD
BEGINNER_USERNAME = settings.BEGINNER_USERNAME

# Vérification que les variables requises sont définies
if not all([ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_USERNAME, 
            BEGINNER_EMAIL, BEGINNER_PASSWORD, BEGINNER_USERNAME]):
    logger.error("Variables d'environnement manquantes pour les utilisateurs")
    raise ValueError("Les variables d'environnement pour les utilisateurs doivent être définies")

async def init_db():
    """Initialise la base de données et seed les données initiales"""
    try:
        # Création des tables
        async with engine.begin() as conn:
            logger.info("Création des tables...")
            await conn.run_sync(lambda x: Base.metadata.create_all(x, checkfirst=True))
        
        # Vérification si la base est déjà seedée
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if user_count == 0:
                logger.info("Seeding de la base de données...")
                await seed_data(session)
                logger.info("Seeding terminé avec succès !")
            else:
                logger.info("La base de données est déjà seedée.")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        raise

async def seed_data(session: AsyncSession):
    """Seed les données initiales dans la base de données"""
    try:
        # 1. Création des utilisateurs
        user_ids = await seed_users(session)
        
        # 2. Création des télescopes
        telescope_ids = await seed_telescopes(session)
        
        # 3. Création des filtres
        filter_ids = await seed_filters(session, telescope_ids)
        
        # 4. Création des cibles
        target_ids = await seed_targets(session, telescope_ids)
        
        # 5. Création des presets
        preset_ids = await seed_presets(session, telescope_ids)
        
        # 6. Création des fichiers cibles
        await seed_target_files(session, target_ids, filter_ids)
        
        # 7. Création des associations target-preset
        await seed_target_presets(session, target_ids, preset_ids)
        
        # Commit final
        await session.commit()
    
    except Exception as e:
        await session.rollback()
        logger.error(f"Erreur lors du seeding: {str(e)}")
        raise

async def seed_users(session: AsyncSession):
    """Seed les utilisateurs"""
    from app.infrastructure.repositories.models.user import User
    
    # Utilisateur admin
    admin_id = uuid4()
    admin = User(
        id=admin_id,
        email=ADMIN_EMAIL,
        username=ADMIN_USERNAME,
        hashed_password=get_password_hash(ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        level=UserLevel.ADVANCED,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    session.add(admin)
    
    # Utilisateur débutant
    beginner_id = uuid4()
    beginner = User(
        id=beginner_id,
        email=BEGINNER_EMAIL,
        username=BEGINNER_USERNAME,
        hashed_password=get_password_hash(BEGINNER_PASSWORD),
        role=UserRole.USER,
        level=UserLevel.BEGINNER,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    session.add(beginner)
    
    logger.info(f"Utilisateurs créés: {ADMIN_USERNAME}, {BEGINNER_USERNAME}")
    return {
        "admin": admin_id,
        "beginner": beginner_id
    }

async def seed_telescopes(session: AsyncSession):
    """Seed les télescopes"""
    from app.infrastructure.repositories.models.telescope import SpaceTelescope
    
    # Hubble Space Telescope
    hst_id = uuid4()
    hst = SpaceTelescope(
        id=hst_id,
        name="HST",
        aperture="2.4m",
        focal_length="57.6m",
        location="Low Earth Orbit",
        status=TelescopeStatus.ONLINE,
        api_endpoint="https://api.stellastudio.fassih.ch/api/v1/telescopes/{telescope_id}",
        instruments=[
        {"name": "WFC3", "type": "Camera (200-1700nm)"},
        {"name": "ACS", "type": "Camera (350-1100nm)"},
        {"name": "STIS", "type": "Spectrograph (115-1000nm)"}
    ],
        description="Le télescope spatial Hubble est l'un des plus grands et des plus polyvalents, et est bien connu comme un instrument de recherche important et un outil de relations publiques pour l'astronomie."
    )
    session.add(hst)
    
    # James Webb Space Telescope
    jwst_id = uuid4()
    jwst = SpaceTelescope(
        id=jwst_id,
        name="JWST",
        aperture="6.5m",
        focal_length="131.4m",
        location="L2 Orbit",
        status=TelescopeStatus.ONLINE,
        api_endpoint="https://api.stellastudio.fassih.ch/api/v1/telescopes/{telescope_id}",
        instruments=[
        {"name": "NIRCam", "type": "Near Infrared Camera"},
        {"name": "MIRI", "type": "Mid-Infrared Instrument"},
        {"name": "NIRSpec", "type": "Near Infrared Spectrograph"}
    ],
        description="Le télescope spatial James Webb est un télescope spatial infrarouge qui a succédé au télescope spatial Hubble comme observatoire phare de la NASA."
    )
    session.add(jwst)
    
    logger.info(f"Télescopes créés: HST, JWST")
    return {
        "hst": hst_id,
        "jwst": jwst_id
    }

async def seed_filters(session: AsyncSession, telescope_ids):
    """Seed les filtres"""
    from app.infrastructure.repositories.models.filter import Filter
    from app.domain.value_objects.filter_types import FilterType
    
    # Vérifier les valeurs disponibles dans l'énumération
    # Remplacer WIDEBAND par la valeur correcte (probablement BROADBAND)
    
    filters = {}
    
    # Filtres HST
    hst_filters = [
        # Filtres pour HOO preset
        {"name": "F656N", "filter_type": FilterType.NARROWBAND, "wavelength": 656, "description": "H-alpha"},
        {"name": "F502N", "filter_type": FilterType.NARROWBAND, "wavelength": 502, "description": "OIII"},
        # Autres filtres utiles
        {"name": "F658N", "filter_type": FilterType.NARROWBAND, "wavelength": 658, "description": "NII"},
        {"name": "F814W", "filter_type": FilterType.BROADBAND, "wavelength": 814, "description": "I-band"}
    ]
    
    for filter_data in hst_filters:
        filter_id = uuid4()
        new_filter = Filter(
            id=filter_id,
            telescope_id=telescope_ids["hst"],
            **filter_data
        )
        session.add(new_filter)
        filters[filter_data["name"]] = filter_id
    
    # Filtres JWST
    jwst_filters = [
        # Filtres NIRCam
        {"name": "F090W", "filter_type": FilterType.BROADBAND, "wavelength": 900, "description": "NIRCam Wide Band"},
        {"name": "F187N", "filter_type": FilterType.NARROWBAND, "wavelength": 1870, "description": "Paschen-alpha"},
        {"name": "F212N", "filter_type": FilterType.NARROWBAND, "wavelength": 2120, "description": "H2"},
        # Filtres MIRI
        {"name": "F770W", "filter_type": FilterType.BROADBAND, "wavelength": 7700, "description": "MIRI Wide Band"},
        {"name": "F1130W", "filter_type": FilterType.BROADBAND, "wavelength": 11300, "description": "PAH"}
    ]
    
    for filter_data in jwst_filters:
        filter_id = uuid4()
        new_filter = Filter(
            id=filter_id,
            telescope_id=telescope_ids["jwst"],
            **filter_data
        )
        session.add(new_filter)
        filters[filter_data["name"]] = filter_id
    
    logger.info(f"Filtres créés: {', '.join(filters.keys())}")
    return filters


async def seed_targets(session: AsyncSession, telescope_ids):
    """Seed les cibles"""
    from app.infrastructure.repositories.models.target import Target
    
    targets = {}
    
    # Eagle Nebula (M16) - HST
    m16_hst_id = uuid4()
    m16_hst = Target(
        id=m16_hst_id,
        name="Eagle Nebula",
        catalog_name="M16",
        common_name="Eagle Nebula",
        coordinates_ra="18:18:48",
        coordinates_dec="-13:49:00",
        object_type=ObjectType.NEBULA,
        status=TargetStatus.READY,
        telescope_id=telescope_ids["hst"],
        description="La nébuleuse de l'Aigle est une région de formation d'étoiles située dans la constellation du Serpent. Elle contient les célèbres 'Piliers de la Création'."
    )
    session.add(m16_hst)
    targets["m16_hst"] = m16_hst_id
    
    # Eagle Nebula (M16) - JWST
    m16_jwst_id = uuid4()
    m16_jwst = Target(
        id=m16_jwst_id,
        name="Eagle Nebula",
        catalog_name="M16",
        common_name="Eagle Nebula",
        coordinates_ra="18:18:48",
        coordinates_dec="-13:49:00",
        object_type=ObjectType.NEBULA,
        status=TargetStatus.READY,
        telescope_id=telescope_ids["jwst"],
        description="La nébuleuse de l'Aigle vue par JWST révèle des détails sans précédent dans l'infrarouge, montrant les processus de formation stellaire cachés."
    )
    session.add(m16_jwst)
    targets["m16_jwst"] = m16_jwst_id
    
    # Sombrero Galaxy (M104) - HST
    m104_id = uuid4()
    m104 = Target(
        id=m104_id,
        name="Sombrero Galaxy",
        catalog_name="M104",
        common_name="Sombrero Galaxy",
        coordinates_ra="12:39:59.4",
        coordinates_dec="-11:37:23",
        object_type=ObjectType.GALAXY,
        status=TargetStatus.READY,
        telescope_id=telescope_ids["hst"],
        description="La galaxie du Sombrero est une galaxie spirale vue par la tranche, avec un bulbe central proéminent et un anneau de poussière caractéristique."
    )
    session.add(m104)
    targets["m104"] = m104_id
    
    # Cartwheel Galaxy - JWST
    cartwheel_id = uuid4()
    cartwheel = Target(
        id=cartwheel_id,
        name="Cartwheel Galaxy",
        catalog_name="ESO350-40",
        common_name="Cartwheel Galaxy",
        coordinates_ra="00:37:41.1",
        coordinates_dec="-33:42:59",
        object_type=ObjectType.GALAXY,
        status=TargetStatus.READY,
        telescope_id=telescope_ids["jwst"],
        description="La galaxie de la Roue de Chariot est une galaxie lenticulaire à anneau qui a été formée par une collision galactique. JWST révèle sa structure complexe en détail."
    )
    session.add(cartwheel)
    targets["cartwheel"] = cartwheel_id
    
    logger.info(f"Cibles créées: Eagle Nebula (HST), Eagle Nebula (JWST), Sombrero Galaxy, Cartwheel Galaxy")
    return targets

async def seed_presets(session: AsyncSession, telescope_ids):
    """Seed les presets de traitement d'image"""
    from app.infrastructure.repositories.models.preset import Preset
    
    presets = {}
    
    # Preset HOO pour HST
    hoo_hst_id = uuid4()
    hoo_hst = Preset(
        id=hoo_hst_id,
        name="HOO",
        description="Hydrogen-alpha (rouge) et Oxygen-III (vert+bleu)",
        telescope_id=telescope_ids["hst"],
        target_type="NEBULA",
        is_default=True,
        processing_params={
            "version": "1.0",
            "channels": {
                "red": {"filter": "F656N", "stretch": 1.5, "weight": 1.0},
                "green": {"filter": "F502N", "stretch": 1.2, "weight": 0.8},
                "blue": {"filter": "F502N", "stretch": 1.2, "weight": 1.0}
            },
            "steps": [
                {"name": "calibration", "type": "CALIBRATION", "params": {}},
                {"name": "registration", "type": "REGISTRATION", "params": {"method": "auto"}},
                {"name": "stretching", "type": "STRETCHING", "params": {"method": "arcsinh", "factor": 0.5}},
                {"name": "color_balance", "type": "COLOR_BALANCE", "params": {"method": "histogram_matching"}}
            ]
        },
        required_filters={"F656N": 1.0, "F502N": 1.0}
    )
    session.add(hoo_hst)
    presets["hoo_hst"] = hoo_hst_id
    
    # Preset HOO pour JWST
    hoo_jwst_id = uuid4()
    hoo_jwst = Preset(
        id=hoo_jwst_id,
        name="HOO",
        description="Hydrogen-alpha (rouge) et Oxygen-III (vert+bleu) pour JWST",
        telescope_id=telescope_ids["jwst"],
        target_type="NEBULA",
        is_default=True,
        processing_params={
            "version": "1.0",
            "channels": {
                "red": {"filter": "F187N", "stretch": 1.5, "weight": 1.0},
                "green": {"filter": "F212N", "stretch": 1.2, "weight": 0.8},
                "blue": {"filter": "F212N", "stretch": 1.2, "weight": 1.0}
            },
            "steps": [
                {"name": "calibration", "type": "CALIBRATION", "params": {}},
                {"name": "registration", "type": "REGISTRATION", "params": {"method": "auto"}},
                {"name": "stretching", "type": "STRETCHING", "params": {"method": "arcsinh", "factor": 0.5}},
                {"name": "color_balance", "type": "COLOR_BALANCE", "params": {"method": "histogram_matching"}}
            ]
        },
        required_filters={"F187N": 1.0, "F212N": 1.0}
    )
    session.add(hoo_jwst)
    presets["hoo_jwst"] = hoo_jwst_id
    
    # Preset RGB pour HST (galaxies)
    rgb_hst_id = uuid4()
    rgb_hst = Preset(
        id=rgb_hst_id,
        name="RGB",
        description="Traitement RGB standard pour galaxies",
        telescope_id=telescope_ids["hst"],
        target_type="GALAXY",
        is_default=True,
        processing_params={
            "version": "1.0",
            "channels": {
                "red": {"filter": "F814W", "stretch": 1.0, "weight": 1.0},
                "green": {"filter": "F658N", "stretch": 1.0, "weight": 1.0},
                "blue": {"filter": "F502N", "stretch": 1.0, "weight": 1.0}
            },
            "steps": [
                {"name": "calibration", "type": "CALIBRATION", "params": {}},
                {"name": "registration", "type": "REGISTRATION", "params": {"method": "auto"}},
                {"name": "stretching", "type": "STRETCHING", "params": {"method": "arcsinh", "factor": 0.5}},
                {"name": "color_balance", "type": "COLOR_BALANCE", "params": {"method": "histogram_matching"}}
            ]
        },
        required_filters={"F814W": 1.0, "F658N": 1.0, "F502N": 1.0}
    )
    session.add(rgb_hst)
    presets["rgb_hst"] = rgb_hst_id
    
    # Preset RGB pour JWST (galaxies)
    rgb_jwst_id = uuid4()
    rgb_jwst = Preset(
        id=rgb_jwst_id,
        name="RGB",
        description="Traitement RGB pour galaxies avec JWST",
        telescope_id=telescope_ids["jwst"],
        target_type="GALAXY",
        is_default=True,
        processing_params={
            "version": "1.0",
            "channels": {
                "red": {"filter": "F770W", "stretch": 1.0, "weight": 1.0},
                "green": {"filter": "F1130W", "stretch": 1.0, "weight": 1.0},
                "blue": {"filter": "F090W", "stretch": 1.0, "weight": 1.0}
            },
            "steps": [
                {"name": "calibration", "type": "CALIBRATION", "params": {}},
                {"name": "registration", "type": "REGISTRATION", "params": {"method": "auto"}},
                {"name": "stretching", "type": "STRETCHING", "params": {"method": "arcsinh", "factor": 0.5}},
                {"name": "color_balance", "type": "COLOR_BALANCE", "params": {"method": "histogram_matching"}}
            ]
        },
        required_filters={"F770W": 1.0, "F1130W": 1.0, "F090W": 1.0}
    )
    session.add(rgb_jwst)
    presets["rgb_jwst"] = rgb_jwst_id
    
    logger.info(f"Presets créés: HOO (HST), HOO (JWST), RGB (HST), RGB (JWST)")
    return presets

async def seed_presets(session: AsyncSession, telescope_ids):
    """Seed les presets de traitement d'image"""
    from app.infrastructure.repositories.models.preset import Preset
    from app.domain.value_objects.target_types import ObjectType
    
    presets = {}
    
    # Preset HOO pour HST
    hoo_hst_id = uuid4()
    hoo_hst = Preset(
        id=hoo_hst_id,
        name="HOO",
        description="Hydrogen-alpha (rouge) et Oxygen-III (vert+bleu)",
        telescope_id=telescope_ids["hst"],
        target_type=ObjectType.NEBULA.value,  # Utiliser .value pour obtenir la chaîne
        processing_params={
            "version": "1.0",
            "channels": {
                "red": {"filter": "F656N", "stretch": 1.5, "weight": 1.0},
                "green": {"filter": "F502N", "stretch": 1.2, "weight": 0.8},
                "blue": {"filter": "F502N", "stretch": 1.2, "weight": 1.0}
            },
            "steps": [
                {"name": "calibration", "type": "CALIBRATION", "params": {}},
                {"name": "registration", "type": "REGISTRATION", "params": {"method": "auto"}},
                {"name": "stretching", "type": "STRETCHING", "params": {"method": "arcsinh", "factor": 0.5}},
                {"name": "color_balance", "type": "COLOR_BALANCE", "params": {"method": "histogram_matching"}}
            ]
        }
    )
    session.add(hoo_hst)
    presets["hoo_hst"] = hoo_hst_id
    
    # Preset HOO pour JWST
    hoo_jwst_id = uuid4()
    hoo_jwst = Preset(
        id=hoo_jwst_id,
        name="HOO",
        description="Hydrogen-alpha (rouge) et Oxygen-III (vert+bleu) pour JWST",
        telescope_id=telescope_ids["jwst"],
        target_type=ObjectType.NEBULA.value,
        processing_params={
            "version": "1.0",
            "channels": {
                "red": {"filter": "F187N", "stretch": 1.5, "weight": 1.0},
                "green": {"filter": "F212N", "stretch": 1.2, "weight": 0.8},
                "blue": {"filter": "F212N", "stretch": 1.2, "weight": 1.0}
            },
            "steps": [
                {"name": "calibration", "type": "CALIBRATION", "params": {}},
                {"name": "registration", "type": "REGISTRATION", "params": {"method": "auto"}},
                {"name": "stretching", "type": "STRETCHING", "params": {"method": "arcsinh", "factor": 0.5}},
                {"name": "color_balance", "type": "COLOR_BALANCE", "params": {"method": "histogram_matching"}}
            ]
        }
    )
    session.add(hoo_jwst)
    presets["hoo_jwst"] = hoo_jwst_id
    
    # Preset RGB pour HST (galaxies)
    rgb_hst_id = uuid4()
    rgb_hst = Preset(
        id=rgb_hst_id,
        name="RGB",
        description="Traitement RGB standard pour galaxies",
        telescope_id=telescope_ids["hst"],
        target_type=ObjectType.GALAXY.value,
        processing_params={
            "version": "1.0",
            "channels": {
                "red": {"filter": "F814W", "stretch": 1.0, "weight": 1.0},
                "green": {"filter": "F658N", "stretch": 1.0, "weight": 1.0},
                "blue": {"filter": "F502N", "stretch": 1.0, "weight": 1.0}
            },
            "steps": [
                {"name": "calibration", "type": "CALIBRATION", "params": {}},
                {"name": "registration", "type": "REGISTRATION", "params": {"method": "auto"}},
                {"name": "stretching", "type": "STRETCHING", "params": {"method": "arcsinh", "factor": 0.5}},
                {"name": "color_balance", "type": "COLOR_BALANCE", "params": {"method": "histogram_matching"}}
            ]
        }
    )
    session.add(rgb_hst)
    presets["rgb_hst"] = rgb_hst_id
    
    # Preset RGB pour JWST (galaxies)
    rgb_jwst_id = uuid4()
    rgb_jwst = Preset(
        id=rgb_jwst_id,
        name="RGB",
        description="Traitement RGB pour galaxies avec JWST",
        telescope_id=telescope_ids["jwst"],
        target_type=ObjectType.GALAXY.value,
        processing_params={
            "version": "1.0",
            "channels": {
                "red": {"filter": "F770W", "stretch": 1.0, "weight": 1.0},
                "green": {"filter": "F1130W", "stretch": 1.0, "weight": 1.0},
                "blue": {"filter": "F090W", "stretch": 1.0, "weight": 1.0}
            },
            "steps": [
                {"name": "calibration", "type": "CALIBRATION", "params": {}},
                {"name": "registration", "type": "REGISTRATION", "params": {"method": "auto"}},
                {"name": "stretching", "type": "STRETCHING", "params": {"method": "arcsinh", "factor": 0.5}},
                {"name": "color_balance", "type": "COLOR_BALANCE", "params": {"method": "histogram_matching"}}
            ]
        }
    )
    session.add(rgb_jwst)
    presets["rgb_jwst"] = rgb_jwst_id
    
    logger.info(f"Presets créés: HOO (HST), HOO (JWST), RGB (HST), RGB (JWST)")
    return presets


async def seed_target_files(session: AsyncSession, target_ids, filter_ids):
    """Seed les fichiers cibles"""
    from app.infrastructure.repositories.models.target_file import TargetFile
    
    # Fichiers pour Eagle Nebula (HST)
    m16_hst_files = [
        {
            "filter_id": filter_ids["F656N"],
            "file_path": "hst/m16/hst_05773_05_wfpc2_f656n_wf.fits",
            "file_size": 16777216,  # Taille fictive en octets
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 16,
                "NAXIS": 2,
                "NAXIS1": 800,
                "NAXIS2": 800,
                "EXPTIME": 2000.0,
                "TELESCOP": "HST",
                "INSTRUME": "WFPC2"
            },
            "is_downloaded": False,
            "in_minio": False
        },
        {
            "filter_id": filter_ids["F502N"],
            "file_path": "hst/m16/hst_05773_05_wfpc2_f502n_wf.fits",
            "file_size": 16777216,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 16,
                "NAXIS": 2,
                "NAXIS1": 800,
                "NAXIS2": 800,
                "EXPTIME": 2600.0,
                "TELESCOP": "HST",
                "INSTRUME": "WFPC2"
            },
            "is_downloaded": False,
            "in_minio": False
        }
    ]
    
    for file_data in m16_hst_files:
        target_file = TargetFile(
            id=uuid4(),
            target_id=target_ids["m16_hst"],
            **file_data
        )
        session.add(target_file)
    
    # Fichiers pour Eagle Nebula (JWST)
    m16_jwst_files = [
        {
            "filter_id": filter_ids["F187N"],
            "file_path": "jwst/m16/jw02739-o001_t001_nircam_clear-f187n.fits",
            "file_size": 33554432,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 32,
                "NAXIS": 2,
                "NAXIS1": 2048,
                "NAXIS2": 2048,
                "EXPTIME": 1000.0,
                "TELESCOP": "JWST",
                "INSTRUME": "NIRCAM"
            },
            "is_downloaded": False,
            "in_minio": False
        },
        {
            "filter_id": filter_ids["F212N"],
            "file_path": "jwst/m16/jw02739-o001_t001_nircam_clear-f212n.fits",
            "file_size": 33554432,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 32,
                "NAXIS": 2,
                "NAXIS1": 2048,
                "NAXIS2": 2048,
                "EXPTIME": 1000.0,
                "TELESCOP": "JWST",
                "INSTRUME": "NIRCAM"
            },
            "is_downloaded": False,
            "in_minio": False
        }
    ]
    
    for file_data in m16_jwst_files:
        target_file = TargetFile(
            id=uuid4(),
            target_id=target_ids["m16_jwst"],
            **file_data
        )
        session.add(target_file)
    
    # Fichiers pour Sombrero Galaxy (HST)
    m104_files = [
        {
            "filter_id": filter_ids["F814W"],
            "file_path": "hst/m104/hst_10146_01_acs_f814w_wfc.fits",
            "file_size": 25165824,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 16,
                "NAXIS": 2,
                "NAXIS1": 4096,
                "NAXIS2": 2048,
                "EXPTIME": 1200.0,
                "TELESCOP": "HST",
                "INSTRUME": "ACS"
            },
            "is_downloaded": False,
            "in_minio": False
        },
        {
            "filter_id": filter_ids["F658N"],
            "file_path": "hst/m104/hst_10146_01_acs_f658n_wfc.fits",
            "file_size": 25165824,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 16,
                "NAXIS": 2,
                "NAXIS1": 4096,
                "NAXIS2": 2048,
                "EXPTIME": 1400.0,
                "TELESCOP": "HST",
                "INSTRUME": "ACS"
            },
            "is_downloaded": False,
            "in_minio": False
        },
        {
            "filter_id": filter_ids["F502N"],
            "file_path": "hst/m104/hst_10146_01_acs_f502n_wfc.fits",
            "file_size": 25165824,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 16,
                "NAXIS": 2,
                "NAXIS1": 4096,
                "NAXIS2": 2048,
                "EXPTIME": 1600.0,
                "TELESCOP": "HST",
                "INSTRUME": "ACS"
            },
            "is_downloaded": False,
            "in_minio": False
        }
    ]
    
    for file_data in m104_files:
        target_file = TargetFile(
            id=uuid4(),
            target_id=target_ids["m104"],
            **file_data
        )
        session.add(target_file)
    
    # Fichiers pour Cartwheel Galaxy (JWST)
    cartwheel_files = [
        {
            "filter_id": filter_ids["F090W"],
            "file_path": "jwst/cartwheel/jw02727-o001_t001_nircam_clear-f090w.fits",
            "file_size": 41943040,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 32,
                "NAXIS": 2,
                "NAXIS1": 2048,
                "NAXIS2": 2048,
                "EXPTIME": 900.0,
                "TELESCOP": "JWST",
                "INSTRUME": "NIRCAM"
            },
            "is_downloaded": False,
            "in_minio": False
        },
        {
            "filter_id": filter_ids["F770W"],
            "file_path": "jwst/cartwheel/jw02727-o001_t001_miri_f770w.fits",
            "file_size": 41943040,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 32,
                "NAXIS": 2,
                "NAXIS1": 1024,
                "NAXIS2": 1024,
                "EXPTIME": 1200.0,
                "TELESCOP": "JWST",
                "INSTRUME": "MIRI"
            },
            "is_downloaded": False,
            "in_minio": False
        },
        {
            "filter_id": filter_ids["F1130W"],
            "file_path": "jwst/cartwheel/jw02727-o001_t001_miri_f1130w.fits",
            "file_size": 41943040,
            "fits_metadata": {
                "SIMPLE": True,
                "BITPIX": 32,
                "NAXIS": 2,
                "NAXIS1": 1024,
                "NAXIS2": 1024,
                "EXPTIME": 1500.0,
                "TELESCOP": "JWST",
                "INSTRUME": "MIRI"
            },
            "is_downloaded": False,
            "in_minio": False
        }
    ]
    
    for file_data in cartwheel_files:
        target_file = TargetFile(
            id=uuid4(),
            target_id=target_ids["cartwheel"],
            **file_data
        )
        session.add(target_file)
    
    logger.info(f"Fichiers cibles créés pour: Eagle Nebula (HST), Eagle Nebula (JWST), Sombrero Galaxy, Cartwheel Galaxy")

async def seed_target_presets(session: AsyncSession, target_ids, preset_ids):
    """Seed les associations target-preset"""
    from app.infrastructure.repositories.models.target_preset import TargetPreset
    
    # Associations pour Eagle Nebula (HST)
    m16_hst_preset = TargetPreset(
        target_id=target_ids["m16_hst"],
        preset_id=preset_ids["hoo_hst"],
        is_available=True
    )
    session.add(m16_hst_preset)
    
    # Associations pour Eagle Nebula (JWST)
    m16_jwst_preset = TargetPreset(
        target_id=target_ids["m16_jwst"],
        preset_id=preset_ids["hoo_jwst"],
        is_available=True
    )
    session.add(m16_jwst_preset)
    
    # Associations pour Sombrero Galaxy (HST)
    m104_preset = TargetPreset(
        target_id=target_ids["m104"],
        preset_id=preset_ids["rgb_hst"],
        is_available=True
    )
    session.add(m104_preset)
    
    # Associations pour Cartwheel Galaxy (JWST)
    cartwheel_preset = TargetPreset(
        target_id=target_ids["cartwheel"],
        preset_id=preset_ids["rgb_jwst"],
        is_available=True
    )
    session.add(cartwheel_preset)
    
    logger.info(f"Associations target-preset créées pour toutes les cibles")
