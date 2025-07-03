import os
import json
from datetime import timedelta

# --- Chemins des fichiers ---
DOWNLOADED_CLIPS_INFO_JSON = os.path.join("data", "downloaded_clip_paths.json") # Nouvelle source
OUTPUT_METADATA_JSON = os.path.join("data", "video_metadata.json")

# --- Paramètres de la vidéo YouTube ---
VIDEO_TITLE_PREFIX = "Les Meilleurs Clips Twitch FR du Jour"
VIDEO_TAGS = ["Twitch", "Clips", "Highlights", "Gaming", "France", "Français", "Best Of", "Drôle"]

# --- Fonctions utilitaires ---
def format_duration(seconds):
    """Formate une durée en secondes en HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def generate_metadata():
    print("📝 Génération des métadonnées vidéo (titre, description, tags)...")

    if not os.path.exists(DOWNLOADED_CLIPS_INFO_JSON):
        print(f"❌ Fichier des informations de clips téléchargés '{DOWNLOADED_CLIPS_INFO_JSON}' introuvable.")
        print("Impossible de générer les métadonnées sans les clips.")
        # Créer un fichier de métadonnées vide pour éviter l'échec des étapes suivantes
        with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump({"title": VIDEO_TITLE_PREFIX, "description": "Aucun clip disponible pour cette compilation.", "tags": VIDEO_TAGS}, f, ensure_ascii=False, indent=2)
        sys.exit(1)

    # Charger les informations des clips téléchargés (qui incluent la durée réelle)
    with open(DOWNLOADED_CLIPS_INFO_JSON, "r", encoding="utf-8") as f:
        downloaded_clips_info = json.load(f)

    if not downloaded_clips_info:
        print("⚠️ Aucune information de clip téléchargée disponible pour générer les métadonnées.")
        # Créer un fichier de métadonnées vide
        with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump({"title": VIDEO_TITLE_PREFIX, "description": "Aucun clip disponible pour cette compilation.", "tags": VIDEO_TAGS}, f, ensure_ascii=False, indent=2)
        return

    # --- Construction du titre de la vidéo ---
    # Le titre peut être dynamique, par exemple avec la date du jour
    current_date = datetime.now().strftime("%d/%m/%Y")
    video_title = f"{VIDEO_TITLE_PREFIX} du {current_date}"

    # --- Construction de la description de la vidéo avec chapitres ---
    description_lines = [
        "Bienvenue sur notre chaîne ! Découvrez les moments les plus drôles, épiques et mémorables de Twitch.",
        "Abonnez-vous pour ne rien manquer des prochains Top Clips !",
        "",
        "Chapitres et clips inclus :"
    ]

    current_offset = 0.0
    for clip_info in downloaded_clips_info:
        # Utilise la durée réelle du clip stockée dans downloaded_clips_info
        clip_duration = clip_info.get("duration", 0.0)
        
        # Assurez-vous que le titre et le nom du streamer sont disponibles
        clip_title = clip_info.get("title", "Clip inconnu")
        broadcaster_name = clip_info.get("broadcaster_name", "Streamer inconnu")

        # Formatage du timecode et ajout à la description
        timecode = format_duration(current_offset)
        description_lines.append(f"{timecode} - {clip_title} par {broadcaster_name}")
        current_offset += clip_duration

    # Ajouter une section de remerciements ou d'appel à l'action
    description_lines.extend([
        "",
        "Merci d'avoir regardé !",
        "Laissez un like et un commentaire si la vidéo vous a plu.",
        "N'oubliez pas de vous abonner pour plus de contenu !"
    ])

    video_description = "\n".join(description_lines)

    # --- Sauvegarde des métadonnées dans un fichier JSON ---
    video_metadata = {
        "title": video_title,
        "description": video_description,
        "tags": VIDEO_TAGS
    }

    output_dir = os.path.dirname(OUTPUT_METADATA_JSON)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(video_metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ Métadonnées générées et sauvegardées dans {OUTPUT_METADATA_JSON}.")
    print(f"Titre: {video_title}")
    print(f"Description (extrait):\n{video_description[:500]}...") # Affiche un extrait

if __name__ == "__main__":
    from datetime import datetime # Importation locale pour main
    generate_metadata()