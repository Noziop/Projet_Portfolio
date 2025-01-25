from app.core.celery import celery_app
from astroquery.mast import Observations
from astroquery.simbad import Simbad
import logging
from app.services.minio_service import get_minio_client
import os
from tempfile import NamedTemporaryFile

# Dictionnaire des cibles disponibles
targets = {
    "HST": [
        {
            "name": "Eagle Nebula",
            "id": "M16",
            "description": "Famous for the Pillars of Creation",
            "coordinates": {"ra": "18 18 48", "dec": "-13 49 00"}
        },
        {
            "name": "Sombrero Galaxy",
            "id": "M104",
            "description": "Iconic galaxy with a bright nucleus",
            "coordinates": {"ra": "12 39 59", "dec": "-11 37 23"}
        },
        {
            "name": "Butterfly Nebula",
            "id": "NGC6302",
            "description": "Spectacular planetary nebula",
            "coordinates": {"ra": "17 13 44", "dec": "-37 06 16"}
        },
        {
            "name": "Cigar Galaxy",
            "id": "M82",
            "description": "Galaxy with active star formation",
            "coordinates": {"ra": "09 55 52", "dec": "+69 40 47"}
        },
        {
            "name": "Gabriela Mistral Nebula",
            "id": "NGC3324",
            "description": "Colorful nebula",
            "coordinates": {"ra": "10 37 19", "dec": "-58 38 00"}
        }
    ],
    "JWST": [
        {
            "name": "Eagle Nebula",
            "id": "M16",
            "description": "Famous for the Pillars of Creation",
            "coordinates": {"ra": "18 18 48", "dec": "-13 49 00"}
        },
        {
            "name": "Cartwheel Galaxy",
            "id": "ESO 350-40",
            "description": "Ring galaxy formed by collision",
            "coordinates": {"ra": "00 37 41", "dec": "-33 42 59"}
        },
        {
            "name": "Phantom Galaxy",
            "id": "M74",
            "description": "Perfect spiral galaxy",
            "coordinates": {"ra": "01 36 42", "dec": "+15 47 01"}
        },
        {
            "name": "Stephan's Quintet",
            "id": "HCG 92",
            "description": "Compact group of five galaxies",
            "coordinates": {"ra": "22 35 58", "dec": "+33 57 36"}
        },
        {
            "name": "Southern Ring Nebula",
            "id": "NGC3132",
            "description": "Spectacular planetary nebula",
            "coordinates": {"ra": "10 07 02", "dec": "-40 26 11"}
        }
    ]
}

def get_target_preview(object_name: str, telescope: str):
    """Récupère l'URL de preview pour un objet et un télescope donnés"""
    try:
        obs_table = Observations.query_object(object_name, radius=0.2)
        if len(obs_table) == 0:
            logging.warning(f"No observations found for {object_name}")
            return None
            
        obs_filtered = obs_table[obs_table['obs_collection'] == telescope]
        if len(obs_filtered) == 0:
            logging.warning(f"No {telescope} observations found for {object_name}")
            return None
            
        products = Observations.get_product_list(obs_filtered[0:1])  # Limite à la première observation
        preview_products = Observations.filter_products(
            products,
            productType=["PREVIEW"],
            extension="jpg"
        )
        
        if len(preview_products) > 0:
            preview_url = preview_products[0].get('dataURL')
            if not preview_url:
                logging.warning(f"No preview URL for {object_name}")
                return None
            return preview_url
            
        return None
    except Exception as e:
        logging.error(f"Erreur preview pour {object_name}: {str(e)}")
        return None

def get_available_targets(telescope: str):
    """Retourne la liste des cibles pour un télescope"""
    return targets.get(telescope, [])


@celery_app.task(name='app.services.telescope_service.fetch_object_data')
def fetch_object_data(object_name: str):
    """Récupère les données Simbad pour un objet"""
    try:
        result = Simbad.query_object(object_name)
        return {
            "status": "success",
            "data": {name: str(result[0][name]) for name in result.colnames}
        }
    except Exception as e:
        logging.error(f"Erreur Simbad: {str(e)}")
        return {"status": "error", "message": str(e)}

@celery_app.task(name='app.services.telescope_service.download_fits_async')
def download_fits_async(object_name: str, telescope: str):
    """Télécharge les fichiers FITS et les stocke dans MinIO"""
    try:
        # Initialiser le client MinIO
        minio_client = get_minio_client()
        bucket_name = "fits-files"

        # S'assurer que le bucket existe
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # 1. Recherche des observations
        obs_table = Observations.query_object(object_name, radius=".02 deg")
        
        # 2. Filtrage par télescope
        obs_filtered = obs_table[obs_table['obs_collection'] == telescope]
        if len(obs_filtered) == 0:
            return {
                "status": "error",
                "message": f"No {telescope} observations found for {object_name}"
            }

        # 3. Obtention des produits
        products = Observations.get_product_list(obs_filtered[0])

        # 4. Filtrage des produits FITS
        filtered_products = Observations.filter_products(
            products,
            productType=["SCIENCE"],
            extension="fits"
        )

        if not filtered_products:
            return {
                "status": "error",
                "message": f"No FITS files found for {object_name} with {telescope}"
            }

        uploaded_files = []
        
        # 5. Téléchargement et upload vers MinIO
        for product in filtered_products:
            # Télécharger le fichier
            result = Observations.download_file(product['dataURI'])
            if result[0] == 'COMPLETE':
                # Le nom du fichier est basé sur l'URI
                filename = product['dataURI'].split('/')[-1]
                if os.path.exists(filename):
                    # Upload vers MinIO
                    minio_path = f"{telescope}/{object_name}/{filename}"
                    minio_client.fput_object(bucket_name, minio_path, filename)
                    uploaded_files.append(minio_path)
                    # Nettoyer le fichier local
                    os.remove(filename)

        return {
            "status": "success",
            "count": len(uploaded_files),
            "files": uploaded_files
        }

    except Exception as e:
        logging.error(f"Erreur MAST/MinIO: {str(e)}")
        return {"status": "error", "message": str(e)}
