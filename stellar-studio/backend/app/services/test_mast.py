from astroquery.mast import Observations
import os

# Test avec Eagle Nebula
object_name = "M16"
telescope = "HST"

print("1. Recherche des observations")
obs_table = Observations.query_object(object_name, radius=".02 deg")
print(f"Nombre d'observations trouvées : {len(obs_table)}")

print("\n2. Filtrage par télescope")
obs_filtered = obs_table[obs_table['obs_collection'] == telescope]
print(f"Nombre d'observations HST : {len(obs_filtered)}")

if len(obs_filtered) > 0:
    print("\n3. Obtention des produits")
    products = Observations.get_product_list(obs_filtered[0])
    print(f"Nombre de produits : {len(products)}")

    print("\n4. Filtrage des produits FITS")
    filtered_products = Observations.filter_products(
        products,
        productType=["SCIENCE"],
        extension="fits"
    )
    print(f"Nombre de fichiers FITS : {len(filtered_products)}")

    if len(filtered_products) > 0:
        print("\n5. Test de téléchargement")
        product = filtered_products[0]
        print(f"URI du fichier : {product['dataURI']}")
        result = Observations.download_file(product['dataURI'])
        print(f"Résultat : {result}")
        
        # Afficher les fichiers téléchargés
        print("\n6. Fichiers dans le répertoire courant :")
        files = [f for f in os.listdir('.') if f.endswith('.fits')]
        for f in files:
            size = os.path.getsize(f)
            print(f"- {f} ({size/1024/1024:.2f} MB)")
