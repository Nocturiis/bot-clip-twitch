import os
import json
from datetime import datetime, timedelta

# Mappage des noms de mois en français pour une robustesse maximale
MOIS_FRANCAIS = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril",
    5: "mai", 6: "juin", 7: "juillet", 8: "août",
    9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
}

INPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")
OUTPUT_METADATA_JSON = os.path.join("data", "video_metadata.json")

def format_duration(seconds):
    """Formate une durée en secondes en HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def generate_metadata():
    print("📝 Génération des métadonnées de la vidéo...")
    
    if not os.path.exists(INPUT_CLIPS_JSON):
        print(f"❌ Erreur: Le fichier '{INPUT_CLIPS_JSON}' est introuvable. Assurez-vous que la récupération des clips a réussi.")
        exit(1)

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips_data = json.load(f)

    # Récupérer la date actuelle
    today_date = datetime.now() 
    day = today_date.day
    month_fr = MOIS_FRANCAIS[today_date.month]
    year = today_date.year

    if not clips_data:
        print("⚠️ Aucune donnée de clip à traiter. Le fichier top_clips.json est vide.")
        
        # Le titre par défaut utilise la date en français
        default_title = f"TOP TWITCH CLIPS FR - {day} {month_fr.capitalize()}" # Capitaliser le mois pour le titre par défaut
        
        video_metadata = {
            "title": default_title,
            "description": f"Désolé, aucune compilation de clips disponible pour aujourd'hui ({day} {month_fr} {year}). Revenez demain !",
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
    
    # --- Construction du NOUVEAU TITRE de la vidéo (corrigé) ---
    # Suppression des crochets du titre principal si présents
    clean_popular_title = most_popular_clip_title.replace('[', '').replace(']', '').strip()
    # Utilisation du mois en français
    title = f'{clean_popular_title} | Le Clip Twitch du Jour FR - {day} {month_fr}'

    # Construire la description de la vidéo avec timecodes
    description = f"Découvrez les {len(clips_data)} clips Twitch les plus populaires du {day} {month_fr} {year} !\n\n"
    description += "Chapitres et clips inclus :\n"

    current_timestamp_seconds = 0.0
    for i, clip in enumerate(clips_data):
        title_clip = clip.get('title', 'Titre inconnu') 
        broadcaster = clip.get('broadcaster_name', 'Streamer inconnu')
        clip_duration = float(clip.get('duration', 0.0))

        # Formatage du timecode
        timecode = format_duration(current_timestamp_seconds)
        
        # Ajout du clip avec son timecode
        description += f"{timecode} - {title_clip} par {broadcaster}\n"
        
        # Mise à jour du timecode pour le prochain clip
        current_timestamp_seconds += clip_duration

    description += "\nN'oubliez pas de vous abonner pour ne manquer aucune compilation quotidienne !\n\n"
    # Ajout des tags pour le référencement
    description += "#Twitch #Clips #BestOf #Gaming #Highlights #DailyClips #Top10 #Compilation #MomentsForts #FR #Francophone"
    
    video_metadata = {
        "title": title,
        "description": description,
        "tags": ["Twitch", "Clips", "BestOf", "Gaming", "Highlights", "DailyClips", "Top10", "Compilation", "MomentsForts", "FR", "Francophone"],
        "categoryId": "20", 
        "privacyStatus": "public" 
    }

    with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(video_metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ Métadonnées générées et sauvegardées dans {OUTPUT_METADATA_JSON}")

if __name__ == "__main__":
    generate_metadata()