import json
from astroquery.mast import Observations

# Dictionnaire des cibles avec leurs références de catalogue
hst_targets = {
    "NGC6611": {"name": "Eagle Nebula", "telescope": "HST"},  # M16
    "M104": {"name": "Sombrero Galaxy", "telescope": "HST"},
    "NGC6302": {"name": "Butterfly Nebula", "telescope": "HST"},
    "NGC3034": {"name": "Cigar Galaxy", "telescope": "HST"},
    "NGC3372": {"name": "Gabriela Mistral Nebula", "telescope": "HST"}
}

jwst_targets = {
    "NGC628": {"name": "Phantom Galaxy", "telescope": "JWST"},  # M74
    "NGC7317": {"name": "Stephan's Quintet", "telescope": "JWST"},  # Part du groupe
    "NGC3132": {"name": "Southern Ring Nebula", "telescope": "JWST"},
    "ESO350-40": {"name": "Cartwheel Galaxy", "telescope": "JWST"},
    "NGC6611": {"name": "Eagle Nebula", "telescope": "JWST"},
}

def get_hst_files(catalog_name):
    try:
        print(f"\nRecherche des observations HST pour {catalog_name}...")
        obs = Observations.query_object(catalog_name, radius=".02 deg")
        obs_filtered = obs[obs['obs_collection'] == "HST"]
        
        if len(obs_filtered) == 0:
            print(f"Aucune observation HST trouvée pour {catalog_name}")
            return []
            
        print(f"Récupération des produits pour {catalog_name}...")
        products = Observations.get_product_list(obs_filtered)
        drz_products = Observations.filter_products(
            products,
            productType=["SCIENCE"],
            productSubGroupDescription="DRZ",
            extension="fits"
        )
        
        uris = [p['dataURI'] for p in drz_products]
        print(f"Trouvé {len(uris)} fichiers DRZ pour {catalog_name}")
        return uris
        
    except Exception as e:
        print(f"Erreur pour {catalog_name}: {e}")
        return []

def get_jwst_files(catalog_name):
    try:
        print(f"\nRecherche des observations JWST pour {catalog_name}...")
        obs = Observations.query_object(catalog_name, radius=".02 deg")
        obs_filtered = obs[obs['obs_collection'] == "JWST"]
        
        if len(obs_filtered) == 0:
            print(f"Aucune observation JWST trouvée pour {catalog_name}")
            return []
            
        print(f"Récupération des produits pour {catalog_name}...")
        products = Observations.get_product_list(obs_filtered)
        
        # Pour JWST, on cherche les fichiers calibrés (CAL) et mosaïques (I2D)
        cal_products = Observations.filter_products(
            products,
            productType=["SCIENCE"],
            productSubGroupDescription=["CAL", "I2D"],
            extension="fits"
        )
        
        uris = [p['dataURI'] for p in cal_products]
        print(f"Trouvé {len(uris)} fichiers calibrés pour {catalog_name}")
        return uris
        
    except Exception as e:
        print(f"Erreur pour {catalog_name}: {e}")
        return []

def main():
    print("Démarrage de la collecte des URIs...")
    uri_data = {}
    
    # Collecter les URIs HST
    print("\nTraitement des cibles HST...")
    for catalog_name, target_info in hst_targets.items():
        uris = get_hst_files(catalog_name)
        uri_data[f"{target_info['name']}-HST"] = {
            "catalog_name": catalog_name,
            "name": target_info['name'],
            "telescope": "HST",
            "required_drz_files": uris
        }

    # Collecter les URIs JWST
    print("\nTraitement des cibles JWST...")
    for catalog_name, target_info in jwst_targets.items():
        uris = get_jwst_files(catalog_name)
        uri_data[f"{target_info['name']}-JWST"] = {
            "catalog_name": catalog_name,
            "name": target_info['name'],
            "telescope": "JWST",
            "required_drz_files": uris
        }

    # Sauvegarder dans un fichier JSON
    output_file = 'target_uris.json'
    with open(output_file, 'w') as f:
        json.dump(uri_data, f, indent=4)

    print(f"\nCollecte terminée. Fichier sauvegardé dans {output_file}")
    print("\nRésumé des URIs collectées :")
    for key, data in uri_data.items():
        print(f"{key}: {len(data['required_drz_files'])} fichiers")

if __name__ == "__main__":
    main()
