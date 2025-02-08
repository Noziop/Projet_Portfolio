from astroquery.mast import Observations
from astropy.io import fits
from minio import Minio
import tempfile
import os

# Connexion MinIO
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

def analyze_fits(file_path):
    print(f"\nAnalyse du fichier : {os.path.basename(file_path)}")
    print("-" * 50)
    with fits.open(file_path) as hdul:
        print(f"Nombre d'extensions : {len(hdul)}")
        for i, hdu in enumerate(hdul):
            print(f"\nExtension {i} - {hdu.name}")
            print("Type de données :", hdu.__class__.__name__)
            header = hdu.header
            important_keys = [
                'TELESCOP', 'INSTRUME', 'DETECTOR', 'FILTER', 
                'EXPTIME', 'IMAGETYP', 'TARGNAME', 'DATE-OBS'
            ]
            for key in important_keys:
                if key in header:
                    print(f"{key}: {header[key]}")

def examine_fits_from_minio(bucket_name, object_name):
    print(f"\nAnalyse du fichier MinIO : {object_name}")
    print("-" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.fits') as tmp:
        minio_client.fget_object(bucket_name, object_name, tmp.name)
        analyze_fits(tmp.name)

print("\n=== Analyse des fichiers existants dans MinIO ===")
files_to_examine = [
    "HST/Eagle Nebula/fa2f1401m_a1f.fits",
    "HST/Eagle Nebula/fa2f1401m_a2f.fits",
    "HST/Eagle Nebula/fa2f1401m_a3f.fits"
]

for file_path in files_to_examine:
    examine_fits_from_minio("fits-files", file_path)

print("\n=== Analyse des fichiers DRZ disponibles ===")
# Recherche des observations HST de M16
obs_table = Observations.query_object("M16", radius=".02 deg")
obs_filtered = obs_table[obs_table['obs_collection'] == 'HST']

# Obtention des produits
products = Observations.get_product_list(obs_filtered)

# Filtrage pour obtenir uniquement les DRZ
drz_products = Observations.filter_products(
    products,
    productType=["SCIENCE"],
    productSubGroupDescription="DRZ",
    extension="fits"
)

print(f"\nNombre de fichiers DRZ disponibles : {len(drz_products)}")

# Téléchargement et analyse des 3 premiers fichiers DRZ
print("\nTéléchargement et analyse des premiers fichiers DRZ...")
with tempfile.TemporaryDirectory() as tmp_dir:
    for product in drz_products[:3]:
        local_path = os.path.join(tmp_dir, os.path.basename(product['dataURI']))
        result = Observations.download_file(
            product['dataURI'],
            local_path=local_path
        )
        if result[0] == 'COMPLETE':
            print(f"\nTéléchargé : {os.path.basename(product['dataURI'])}")
            print(f"URI : {product['dataURI']}")
            analyze_fits(local_path)
