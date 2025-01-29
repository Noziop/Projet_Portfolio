from typing import Optional, Dict, Any, List
from astroquery.mast import Observations
from astroquery.simbad import Simbad
import logging
from app.db.session import SessionLocal
from app.infrastructure.repositories.models.target import Target

class ObservationService:
    def get_target_preview(self, object_name: str, telescope: str) -> Optional[str]:
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
                
            products = Observations.get_product_list(obs_filtered[0:1])
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
            logging.error(f"Preview error for {object_name}: {str(e)}")
            return None

    def get_available_targets(self, telescope: str) -> List[Dict]:
        """Retourne la liste des cibles pour un télescope depuis la DB"""
        with SessionLocal() as db:
            targets = db.query(Target).filter(Target.telescope_id == telescope).all()
            return [target.to_dict() for target in targets]

    async def fetch_object_data(self, object_name: str) -> Dict[str, Any]:
        """Récupère les données Simbad pour un objet"""
        try:
            result = Simbad.query_object(object_name)
            return {
                "status": "success",
                "data": {name: str(result[0][name]) for name in result.colnames}
            }
        except Exception as e:
            logging.error(f"Simbad error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_telescope_observations(self, telescope_id: str, target_name: str) -> Dict[str, Any]:
        """Récupère les observations d'un télescope pour une cible donnée"""
        try:
            obs_table = Observations.query_object(target_name, radius=".02 deg")
            obs_filtered = obs_table[obs_table['obs_collection'] == telescope_id]
            
            if len(obs_filtered) == 0:
                return {
                    "status": "error",
                    "message": f"No {telescope_id} observations found for {target_name}"
                }

            return {
                "status": "success",
                "count": len(obs_filtered),
                "observations": obs_filtered.to_table().to_pandas().to_dict('records')
            }
        except Exception as e:
            logging.error(f"Error fetching observations: {str(e)}")
            return {"status": "error", "message": str(e)}
