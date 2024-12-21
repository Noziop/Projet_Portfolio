import logging
from astroquery.simbad import Simbad
from astroquery.mast import Observations, Mast
import logging
from typing import Dict, Optional
import numpy as np

class TelescopeService:
    ICONIC_TARGETS = {
        "jwst": {
            "pillars": {
                "name": "Pillars of Creation",
                "object_name": "M16",
                "type": "Nebula",
                "description": "Colonnes de gaz et de poussière où naissent de nouvelles étoiles",
                "filters": ["F090W", "F187N", "F200W", "F335M", "F444W", "F470N"]
            },
            "crab": {
                "name": "Crab Nebula",
                "object_name": "M1",
                "type": "Supernova Remnant",
                "description": "Rémanent de la supernova observée par les astronomes chinois en 1054",
                "filters": ["F070W", "F100W", "F115W", "F150W", "F200W", "F277W"]
            },
            "eagle": {
                "name": "Eagle Nebula",
                "object_name": "M16",
                "type": "Emission Nebula",
                "description": "Région de formation d'étoiles située à 7000 années-lumière",
                "filters": ["F070W", "F090W", "F115W", "F150W", "F200W", "F277W"]
            },
            "sombrero": {
                "name": "Sombrero Galaxy",
                "object_name": "M104",
                "type": "Spiral Galaxy",
                "description": "Galaxie spirale vue par la tranche avec un bulbe central proéminent",
                "filters": ["F062N", "F087N", "F105W", "F140W", "F187N", "F200W"]
            }
        }
    }


    @staticmethod
    async def get_target_image(telescope: str, target: str) -> Optional[Dict]:
        try:
            logging.info(f"Recherche de {target} pour le télescope {telescope}")
            target_info = TelescopeService.ICONIC_TARGETS[telescope.lower()][target.lower()]
            
            # Configuration du logging pour astroquery
            from astroquery import log
            log.setLevel("DEBUG")
            
            # Requête Simbad avec les champs spécifiques
            customSimbad = Simbad()
            customSimbad.add_votable_fields('otype', 'dim', 'coordinates')
            result = customSimbad.query_object(target_info['object_name'])
            
            if result and len(result) > 0:
                # Conversion des valeurs numpy en types Python natifs
                simbad_data = {}
                for name in result.colnames:
                    value = result[0][name]
                    if isinstance(value, (np.integer, np.floating)):
                        simbad_data[name] = value.item()
                    else:
                        simbad_data[name] = str(value)
                
                return {
                    "telescope": telescope,
                    "target": target_info["name"],
                    "object_name": target_info["object_name"],
                    "filters": target_info["filters"],
                    "simbad_data": simbad_data
                }
            
            logging.warning("Aucune donnée Simbad trouvée")
            return None
            
        except Exception as e:
            logging.error(f"Erreur lors de la requête Simbad: {str(e)}")
            return None

    @staticmethod
    async def download_target_fits(telescope: str, target: str) -> Optional[Dict]:
        """Télécharge les fichiers FITS pour une cible donnée"""
        try:
            target_info = TelescopeService.ICONIC_TARGETS[telescope.lower()][target.lower()]
            
            # Configuration de MAST
            Mast.MAST_DOWNLOAD_URL = 'https://mast.stsci.edu'
            
            # Requête directe par nom d'objet
            obs_table = Observations.query_object(
                target_info['object_name'],
                radius='.02 deg'  # Rayon de recherche restreint
            )
            
            logging.info(f"Observations trouvées: {len(obs_table) if obs_table else 0}")
            
            if obs_table and len(obs_table) > 0:
                products = Observations.get_product_list(obs_table[0])
                if len(products) > 0:
                    manifest = Observations.download_products(products[0])
                    return {
                        "target": target_info['name'],
                        "object_name": target_info['object_name'],
                        "files": manifest['Local Path'].tolist() if manifest else []
                    }
            
            return None

        except Exception as e:
            logging.error(f"Erreur lors du téléchargement des FITS: {str(e)}")
            return None