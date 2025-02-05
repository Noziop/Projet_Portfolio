from typing import List, Optional, Literal, Dict
from app.infrastructure.repositories.models.target import Target, TargetCoordinates


class CatalogService:
    # Catalogue prédéfini
    _targets: Dict[str, List[Target]] = {
        "HST": [
            # Nébuleuses
            Target(
                id="M42_HST",
                name="Orion Nebula",
                telescope="HST",
                object_type="nebula",
                description="The most famous and brightest nebula in the sky",
                coordinates=TargetCoordinates(ra="05 35 17.3", dec="-05 23 28")
            ),
            Target(
                id="M16_HST",
                name="Eagle Nebula",
                telescope="HST",
                object_type="nebula",
                description="Famous for the Pillars of Creation",
                coordinates=TargetCoordinates(ra="18 18 48", dec="-13 49 00")
            ),
            Target(
                id="NGC6302_HST",
                name="Butterfly Nebula",
                telescope="HST",
                object_type="nebula",
                description="Spectacular planetary nebula",
                coordinates=TargetCoordinates(ra="17 13 44", dec="-37 06 16")
            ),
            # Amas
            Target(
                id="M45_HST",
                name="Pleiades",
                telescope="HST",
                object_type="cluster",
                description="The Seven Sisters, most famous open cluster",
                coordinates=TargetCoordinates(ra="03 47 24", dec="+24 07 00")
            ),
            Target(
                id="M35_HST",
                name="M35",
                telescope="HST",
                object_type="cluster",
                description="Rich open cluster in Gemini",
                coordinates=TargetCoordinates(ra="06 08 54", dec="+24 20 00")
            ),
            Target(
                id="NGC5139_HST",
                name="Omega Centauri",
                telescope="HST",
                object_type="cluster",
                description="Largest and brightest globular cluster in the sky",
                coordinates=TargetCoordinates(ra="13 26 48", dec="-47 28 00")
            ),
            # Galaxies
            Target(
                id="M31_HST",
                name="Andromeda Galaxy",
                telescope="HST",
                object_type="galaxy",
                description="The nearest major galaxy to the Milky Way",
                coordinates=TargetCoordinates(ra="00 42 44", dec="+41 16 09")
            ),
            Target(
                id="M104_HST",
                name="Sombrero Galaxy",
                telescope="HST",
                object_type="galaxy",
                description="Iconic galaxy with a bright nucleus and dark dust lane",
                coordinates=TargetCoordinates(ra="12 39 59", dec="-11 37 23")
            ),
            Target(
                id="M51_HST",
                name="Whirlpool Galaxy",
                telescope="HST",
                object_type="galaxy",
                description="Classic spiral galaxy interacting with NGC 5195",
                coordinates=TargetCoordinates(ra="13 29 53", dec="+47 11 43")
            )
        ],
        "JWST": [
            # Nébuleuses
            Target(
                id="M16_JWST",
                name="Eagle Nebula",
                telescope="JWST",
                object_type="nebula",
                description="Famous Pillars of Creation in infrared",
                coordinates=TargetCoordinates(ra="18 18 48", dec="-13 49 00")
            ),
            Target(
                id="NGC3132_JWST",
                name="Southern Ring Nebula",
                telescope="JWST",
                object_type="nebula",
                description="Spectacular planetary nebula in infrared",
                coordinates=TargetCoordinates(ra="10 07 02", dec="-40 26 11")
            ),
            Target(
                id="NGC3372_JWST",
                name="Carina Nebula",
                telescope="JWST",
                object_type="nebula",
                description="Massive star-forming region",
                coordinates=TargetCoordinates(ra="10 45 08", dec="-59 52 04")
            ),
            # Amas
            Target(
                id="WESTERLUND2_JWST",
                name="Westerlund 2",
                telescope="JWST",
                object_type="cluster",
                description="Young massive cluster in Carina",
                coordinates=TargetCoordinates(ra="10 24 02", dec="-57 45 28")
            ),
            Target(
                id="R136_JWST",
                name="R136",
                telescope="JWST",
                object_type="cluster",
                description="Super star cluster in the LMC",
                coordinates=TargetCoordinates(ra="05 38 42", dec="-69 06 03")
            ),
            Target(
                id="QUINTUPLET_JWST",
                name="Quintuplet Cluster",
                telescope="JWST",
                object_type="cluster",
                description="Young massive cluster near Galactic center",
                coordinates=TargetCoordinates(ra="17 46 15", dec="-28 49 41")
            ),
            # Galaxies
            Target(
                id="M74_JWST",
                name="Phantom Galaxy",
                telescope="JWST",
                object_type="galaxy",
                description="Perfect face-on spiral galaxy",
                coordinates=TargetCoordinates(ra="01 36 42", dec="+15 47 01")
            ),
            Target(
                id="M104_JWST",
                name="Sombrero Galaxy",
                telescope="JWST",
                object_type="galaxy",
                description="Edge-on galaxy in infrared",
                coordinates=TargetCoordinates(ra="12 39 59", dec="-11 37 23")
            ),
            Target(
                id="HCG92_JWST",
                name="Stephan's Quintet",
                telescope="JWST",
                object_type="galaxy",
                description="Compact group of five interacting galaxies",
                coordinates=TargetCoordinates(ra="22 35 58", dec="+33 57 36")
            )
        ]
    }

    # Processus disponibles par type d'objet
    _available_processes = {
        "nebula": ["abe", "hoo", "sho"],
        "galaxy": ["abe", "contrast", "luminance"],
        "cluster": ["abe", "align", "contrast"]
    }

    @classmethod
    def get_targets(
        cls,
        telescope: Optional[Literal["HST", "JWST"]] = None,
        object_type: Optional[Literal["nebula", "cluster", "galaxy"]] = None
    ) -> List[Target]:
        """Retourne les cibles filtrées"""
        all_targets = []
        for tel_targets in cls._targets.values():
            all_targets.extend(tel_targets)

        filtered = all_targets
        if telescope:
            filtered = [t for t in filtered if t.telescope == telescope]
        if object_type:
            filtered = [t for t in filtered if t.object_type == object_type]
        
        return filtered

    @classmethod
    def get_target_by_id(cls, target_id: str) -> Optional[Target]:
        """Retourne une cible spécifique par son ID"""
        for tel_targets in cls._targets.values():
            for target in tel_targets:
                if target.id == target_id:
                    return target
        return None

    @classmethod
    def get_available_processes(cls, target_id: str) -> Optional[Dict]:
        """Retourne les processus disponibles pour une cible"""
        target = cls.get_target_by_id(target_id)
        if not target:
            return None
            
        return {
            "target": target.name,
            "available_processes": cls._available_processes[target.object_type]
        }
