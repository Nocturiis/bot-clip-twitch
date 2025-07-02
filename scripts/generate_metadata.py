import os
import json
from datetime import datetime
import locale # Importe le module locale

# Définir la locale pour avoir les mois en français
# Cela dépend de l'environnement, sur Ubuntu (GitHub Actions), 'fr_FR.UTF-8' fonctionne souvent.
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    print("⚠️ La locale 'fr_FR.UTF-8' n'est pas disponible. Les dates resteront en anglais.")
    # Fallback pour d'autres systèmes, ou si la locale n'est pas installée
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR')
    except locale.Error:
        print("⚠️ La locale 'fr_FR' n'est pas disponible non plus. Les dates resteront en anglais.")


INPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")
OUTPUT_METADATA_JSON = os.path.join("data", "video_metadata.json")

def generate_metadata():
    print("📝 Génération des métadonnées de la vidéo...")
    
    if not os.path.exists(INPUT_CLIPS_JSON):
        print(f"❌ Erreur: Le fichier '{INPUT_CLIPS_JSON}' est introuvable. Assurez-vous que la récupération des clips a réussi.")
        exit(1)

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips_data = json.load(f)

    if not clips_data:
        print("⚠️ Aucune donnée de clip à traiter. Le fichier top_clips.json est vide.")
        # Générer des métadonnées vides ou avec un titre par défaut si aucun clip n'est trouvé
        default_title = f"TOP TWITCH CLIPS FR - {datetime.now().strftime('%d %B')}"
        video_metadata = {
            "title": default_title,
            "description": f"Désolé, aucune compilation de clips disponible pour aujourd'hui. Revenez demain !",
            "tags": ["Twitch", "Clips", "BestOf", "Gaming", "Highlights", "Compilation", "FR", "Francophone"],
            "categoryId": "20",
            "privacyStatus": "unlisted" # Mettre en "unlisted" si la vidéo est vide
        }
        with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump(video_metadata, f, ensure_ascii=False, indent=2)
        print(f"✅ Métadonnées par défaut générées et sauvegardées dans {OUTPUT_METADATA_JSON} (aucun clip trouvé).")
        exit(0) 

    # Le clip le plus populaire est le premier de la liste car get_top_clips les trie par vues
    most_popular_clip_title = clips_data[0].get('title', 'Clip populaire') 
    
    today_date = datetime.now() # Récupère la date actuelle

    # --- Construction du NOUVEAU TITRE de la vidéo ---
    # Exemple: "Titre du clip le plus populaire" | Le Clip Twitch du Jour FR - 26 Février
    # Suppression des crochets du titre principal
    title = f'{most_popular_clip_title} | Le Clip Twitch du Jour FR - {today_date.strftime("%d %B")}'

    # Construire la description de la vidéo
    # Formatage de la date en français pour la description complète
    description = f"Découvrez les {len(clips_data)} clips Twitch les plus populaires du {today_date.strftime('%d %B %Y')} !\n\nClips inclus :\n"

    for i, clip in enumerate(clips_data):
        title_clip = clip.get('title', 'Titre inconnu') 
        broadcaster = clip.get('broadcaster_name', 'Streamer inconnu')
        views = clip.get('viewer_count', 0) 
        # Suppression des apostrophes autour du titre du clip dans la description
        description += f"- {i+1}. {title_clip} par {broadcaster} (vues: {views})\n"

    description += "\nN'oubliez pas de vous abonner pour ne manquer aucune compilation quotidienne !\n\n"
    # Ajout des tags pour le référencement
    description += "#Twitch #Clips #BestOf #Gaming #Highlights #DailyClips #Top10 #Compilation #MomentsForts #FR #Francophone"
    
    video_metadata = {
        "title": title,
        "description": description,
        "tags": ["Twitch", "Clips", "BestOf", "Gaming", "Highlights", "DailyClips", "Top10", "Compilation", "MomentsForts", "FR", "Francophone"],
        "categoryId": "20",
        "privacyStatus": "public" # "public", "private", "unlisted"
    }

    with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(video_metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ Métadonnées générées et sauvegardées dans {OUTPUT_METADATA_JSON}")

if __name__ == "__main__":
    generate_metadata()