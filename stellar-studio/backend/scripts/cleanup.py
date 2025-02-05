import pandas as pd
import json
import sys
import argparse
from pathlib import Path

def clean_hst_files(df):
    """Nettoie les fichiers HST en ne gardant que les mosaïques drz finales"""
    df['clean_name'] = df['filename'].str.extract(r'([^/]+)\.fits$')
    
    # Ne garder que les fichiers du répertoire product (mosaïques officielles)
    df = df[df['filename'].str.contains('mast:HST/product/')]
    
    # Ne garder que les fichiers drz
    df = df[df['clean_name'].str.contains('_drz')]
    
    # Capture les instruments et filtres
    df['instrument'] = df['filename'].str.extract(r'_(wfc3|wfpc2|acs)_')
    df['filter'] = df['filename'].str.extract(r'_(f\d+[nw])_')
    
    # Supprimer les doublons
    df = df.drop_duplicates(subset=['clean_name'])
    
    return df

def clean_jwst_files(df):
    """Nettoie les fichiers JWST en ne gardant que les mosaïques i2d"""
    df['clean_name'] = df['filename'].str.extract(r'([^/]+)\.fits$')
    
    # Ne garder que les fichiers du répertoire product (mosaïques officielles)
    df = df[df['filename'].str.contains('mast:JWST/product/')]
    
    # Ne garder que les fichiers i2d (mosaïques)
    df = df[df['clean_name'].str.contains('i2d')]
    
    # Capture les instruments (NIRCam et MIRI)
    df['instrument'] = df['filename'].str.extract(r'_(nircam|miri)_')
    
    # Capture les filtres avec deux patterns différents
    nircam_filter = df['filename'].str.extract(r'clear-(f\d+[nw])')
    miri_filter = df['filename'].str.extract(r'miri_(f\d+w)')
    
    # Combiner les deux
    df['filter'] = nircam_filter.fillna(miri_filter)
    
    # Supprimer les doublons
    df = df.drop_duplicates(subset=['clean_name'])
    
    return df

def clean_drz_files(json_file):
    print(f"Lecture du fichier {json_file}...")
    
    # Charger le JSON
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    cleaned_data = {}
    
    # Pour chaque cible
    for target, target_info in data.items():
        print(f"\nTraitement de {target}...")
        print(f"Nombre initial de fichiers : {len(target_info['required_drz_files'])}")
        
        # Créer un DataFrame avec les fichiers
        df = pd.DataFrame(target_info['required_drz_files'], columns=['filename'])
        
        # Appliquer le nettoyage approprié selon le télescope
        if target_info['telescope'] == 'HST':
            df = clean_hst_files(df)
            print(f"Après filtrage (mosaïques DRZ uniquement) : {len(df)}")
        else:
            df = clean_jwst_files(df)
            print(f"Après filtrage (mosaïques i2d uniquement) : {len(df)}")
        
        # Regrouper par instrument et filtre
        if not df.empty and not df['instrument'].isna().all() and not df['filter'].isna().all():
            grouped = df.groupby(['instrument', 'filter'])['filename'].agg(list).to_dict()
            stats = {f"{inst}-{filt}": len(files) for (inst, filt), files in grouped.items()}
            print("Statistiques par instrument/filtre :")
            for key, count in stats.items():
                print(f"  {key}: {count} fichiers")
        else:
            stats = {}
        
        # Mettre à jour le dictionnaire nettoyé
        cleaned_data[target] = {
            "catalog_name": target_info["catalog_name"],
            "name": target_info["name"],
            "telescope": target_info["telescope"],
            "required_drz_files": df['filename'].tolist(),
            "file_stats": {
                "total_files": len(df),
                "by_instrument": stats
            }
        }
    
    return cleaned_data

def main():
    parser = argparse.ArgumentParser(description='Nettoie les fichiers en ne gardant que les mosaïques (DRZ pour HST, i2d pour JWST)')
    parser.add_argument('input_file', help='Fichier JSON d\'entrée')
    parser.add_argument('-o', '--output', help='Fichier JSON de sortie (optionnel)')
    
    args = parser.parse_args()
    
    # Vérifier que le fichier d'entrée existe
    if not Path(args.input_file).exists():
        print(f"Erreur : Le fichier {args.input_file} n'existe pas")
        sys.exit(1)
    
    # Nettoyer les données
    cleaned_data = clean_drz_files(args.input_file)
    
    # Définir le fichier de sortie
    output_file = args.output or args.input_file.replace('.json', '_cleaned.json')
    
    # Sauvegarder le résultat
    with open(output_file, 'w') as f:
        json.dump(cleaned_data, f, indent=4)
    
    print(f"\nFichier nettoyé sauvegardé dans : {output_file}")

if __name__ == "__main__":
    main()
