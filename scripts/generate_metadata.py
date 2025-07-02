import subprocess
import os
import json
import datetime

COMPILED_VIDEO_PATH = os.path.join("data", "compiled_video.mp4")
THUMBNAIL_PATH = os.path.join("data", "thumbnail.jpg")
METADATA_JSON_PATH = os.path.join("data", "metadata.json")
THUMB_OFFSET = "00:00:05" # Prend une image à 5 secondes de la vidéo compilée

def generate_metadata():
    print("📝 Génération du titre, de la description et de la miniature...")
    
    today = datetime.date.today()
    # Titre : ex. "TOP 10 TWITCH CLIPS - Daily Best Moments - 01 Juillet 2025"
    title = f"TOP 10 TWITCH CLIPS - Daily Best Moments - {today.strftime('%d %B %Y')}"
    
    # Description (va lister les clips)
    description = f"Découvrez les 10 clips Twitch les plus populaires du {today.strftime('%d %B %Y')} !\n\n"
    
    # Lire les clips originaux pour la description détaillée
    original_clips_json = os.path.join("data", "top_clips.json")
    if os.path.exists(original_clips_json):
        with open(original_clips_json, "r", encoding="utf-8") as f:
            clips_data = json.load(f)
        
        description += "Clips inclus :\n"
        for i, clip in enumerate(clips_data):
            description += f"- {i+1}. '{clip['title']}' par {clip['broadcaster_name']} (vues: {clip['viewer_count']:,})\n"
            # Optionnel: inclure le lien du clip original si désiré, mais risque de spam/référencement externe
            # description += f"  Lien original: {clip['url']}\n"
        description += "\nN'oubliez pas de vous abonner pour ne manquer aucune compilation quotidienne !\n"
    else:
        description += "Pas de détails de clips disponibles.\n"

    description += "\n#Twitch #Clips #BestOf #Gaming #Highlights #DailyClips #Top10" # Tags YouTube

    # Miniature
    if not os.path.exists(COMPILED_VIDEO_PATH):
        print(f"❌ Fichier vidéo compilée '{COMPILED_VIDEO_PATH}' introuvable pour la miniature.")
        sys.exit(1)
    
    try:
        command = [
            "ffmpeg",
            "-ss", THUMB_OFFSET,
            "-i", COMPILED_VIDEO_PATH,
            "-vframes", "1",
            THUMBNAIL_PATH
        ]
        subprocess.run(command, check=True)
        print(f"✅ Miniature générée dans {THUMBNAIL_PATH}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la génération de la miniature : {e}")
        if e.stderr: print(f"    STDERR: {e.stderr.decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la génération de la miniature : {e}")
        sys.exit(1)

    # Sauvegarde les métadonnées dans un fichier JSON pour le script d'upload
    metadata = {
        "title": title,
        "description": description,
        "tags": ["Twitch", "Clips", "Best Of", "Gaming", "Highlights", "DailyClips", "Top 10"]
    }
    with open(METADATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print("✅ Métadonnées sauvegardées dans metadata.json")

if __name__ == "__main__":
    generate_metadata()