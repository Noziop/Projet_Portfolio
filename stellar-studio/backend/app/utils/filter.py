import json

# Charger le fichier JSON brut
with open('cleaned_data.json', 'r') as f:
    data = json.load(f)

# Définir les filtres nécessaires pour chaque preset
necessary_filters = {
    'HOO': ['f656n', 'f502n', 'F335M', 'F405N'],
    'SHO': ['f673n', 'f656n', 'f502n', 'F470N', 'F335M', 'F405N'],
    'HaRGB': ['f656n', 'f814w', 'f547m', 'f439w', 'F335M', 'F444W', 'F356W', 'F277W'],
    'RGB': ['f814w', 'f547m', 'f439w', 'F444W', 'F356W', 'F277W']
}

# Fonction de filtrage des fichiers d'une cible
def filter_files(files):
    result = {}
    for preset, filters in necessary_filters.items():
        # Conserver uniquement les fichiers correspondant aux filtres nécessaires
        result[preset] = [file for file in files if any(filt in file.lower() for filt in filters)]
    return result

# Nouveau dictionnaire pour stocker les cibles filtrées
filtered_data = {}

# Parcourir chaque cible dans le fichier JSON
for target, target_data in data.items():
    if "required_drz_files" in target_data:
        files = target_data["required_drz_files"]
        filtered = filter_files(files)
        # Ajouter les résultats filtrés dans un nouvel objet
        filtered_data[target] = {
            "catalog_name": target_data.get("catalog_name", ""),
            "name": target_data.get("name", ""),
            "telescope": target_data.get("telescope", ""),
            "filtered_files": filtered,
            "total_filtered_files": sum(len(v) for v in filtered.values())  # Compter le total des fichiers filtrés
        }
    else:
        # Si la cible ne contient pas de fichiers, copier telle quelle
        filtered_data[target] = target_data

# Sauvegarder le fichier JSON filtré
with open('filtered_cleaned_data.json', 'w') as f:
    json.dump(filtered_data, f, indent=4)

print("Fichier JSON filtré sauvegardé sous 'filtered_cleaned_data.json'")
