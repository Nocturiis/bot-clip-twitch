import subprocess
import os
import json
import sys
from datetime import datetime, timedelta

# --- Chemins des fichiers ---
INPUT_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_VIDEO_PATH = os.path.join("output", "compiled_video.mp4")
# CLIPS_METADATA_JSON n'est plus la source principale des durées ici
CLIPS_LIST_TXT = os.path.join("data", "clips_list.txt") # Utilisé pour concaténation initiale

# --- PARAMÈTRES FFmpeg ---
FONT_PATH = "DejaVuSans" # Exemple : Chemin vers une police TTF ou nom de police système

# --- NOUVEAU PARAMÈTRE : Limite le nombre total de clips dans la compilation finale ---
MAX_TOTAL_CLIPS = 20

# Obtenir le répertoire racine du dépôt (où se trouve .github/)
REPO_ROOT = os.getcwd() 

def format_duration(seconds):
    """Formate une durée en secondes en HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def compile_video():
    print("🎬 Démarrage de la compilation des clips vidéo avec timecodes...")

    output_dir = os.path.dirname(OUTPUT_VIDEO_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Dossier de sortie créé : {output_dir}")
        
    if not os.path.exists(INPUT_PATHS_JSON):
        print(f"❌ Fichier des chemins de clips téléchargés '{INPUT_PATHS_JSON}' introuvable.")
        sys.exit(1)

    # Lire les informations des clips téléchargés et prétraités (incluant la durée réelle)
    with open(INPUT_PATHS_JSON, "r") as f:
        downloaded_clip_info = json.load(f)

    if not downloaded_clip_info:
        print("⚠️ Aucune information de vidéo téléchargée à compiler. Fin de l'étape de compilation.")
        sys.exit(0)

    # Filtrer et limiter les clips à traiter
    final_clips_to_process = []
    for clip_data in downloaded_clip_info:
        # Assurez-vous que le clip a un chemin et une durée valide
        if clip_data.get("path") and clip_data.get("duration", 0.0) > 0:
            final_clips_to_process.append(clip_data)
        if len(final_clips_to_process) >= MAX_TOTAL_CLIPS:
            break

    if not final_clips_to_process:
        print("⚠️ Après application des filtres et limites, aucune vidéo à compiler. Fin de l'étape.")
        sys.exit(0)

    print(f"Compilation de {len(final_clips_to_process)} clips (max {MAX_TOTAL_CLIPS} clips).")

    # --- Étape 1: Concaténation initiale (rapide) sans réencodage ---
    temp_concat_video_path = os.path.join(output_dir, "temp_concat_video_no_audio.mp4")
    temp_concat_audio_path = os.path.join(output_dir, "temp_concat_audio.aac")

    # Crée le fichier de liste pour la concaténation
    with open(CLIPS_LIST_TXT, "w") as f:
        for clip_info in final_clips_to_process:
            # Assurez-vous que le chemin est absolu ou relatif au répertoire de travail de FFmpeg
            f.write(f"file '{clip_info['path']}'\n")

    concat_video_command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", CLIPS_LIST_TXT,
        "-c:v", "copy",
        "-an", # Supprime l'audio pour cette étape
        "-y",
        temp_concat_video_path
    ]
    print(f"Exécution de la commande FFmpeg (concaténation vidéo initiale sans audio): {' '.join(concat_video_command)}")
    try:
        subprocess.run(concat_video_command, check=True, capture_output=True, text=True)
        print("✅ Concaténation vidéo initiale terminée.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la concaténation vidéo initiale : {e.stderr}")
        sys.exit(1)

    # --- Étape 2: Concaténation et Normalisation Audio ---
    audio_inputs_cmd = []
    for clip_info in final_clips_to_process:
        audio_inputs_cmd.extend(["-i", clip_info['path']])
        
    # Création de la chaîne de filtre complex pour l'audio
    audio_filter_complex = ""
    if len(final_clips_to_process) > 1:
        audio_filter_complex = "".join([f"[{i}:a]" for i in range(len(final_clips_to_process))])
        audio_filter_complex += f"concat=n={len(final_clips_to_process)}:v=0:a=1[aout];[aout]loudnorm=I=-16:TP=-1.5:LRA=11"
    else: # S'il n'y a qu'un seul clip, applique directement loudnorm
        audio_filter_complex = "[0:a]loudnorm=I=-16:TP=-1.5:LRA=11"

    audio_command = [
        "ffmpeg",
        *audio_inputs_cmd, # Tous les clips comme entrées audio
        "-filter_complex", audio_filter_complex,
        "-c:a", "aac",
        "-b:a", "192k",
        "-ac", "2",
        "-ar", "44100",
        "-vn", # Pas de sortie vidéo
        "-y",
        temp_concat_audio_path
    ]

    print(f"\nExécution de la commande FFmpeg (extraction, concaténation et normalisation audio): {' '.join(audio_command)}")
    try:
        subprocess.run(audio_command, check=True, capture_output=True, text=True)
        print("✅ Audio combiné et normalisé avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du traitement audio : {e.stderr}")
        sys.exit(1)

    # --- Étape 3: Application des timecodes sur la vidéo concaténée et fusion avec l'audio ---
    drawtext_filters = []
    current_offset = 0.0
    for clip_info in final_clips_to_process:
        start_time_str = format_duration(current_offset)
        # Utilise la durée réelle du clip obtenue de downloaded_clip_paths.json
        clip_duration = clip_info.get('duration', 0.0) 
        
        # Le texte à afficher : Timecode + Titre du clip + Nom du streamer
        # Assurez-vous que title et broadcaster_name sont bien échappés si nécessaire,
        # mais ils le sont déjà dans download_clips.py avant d'être écrits dans le JSON.
        text_content = f"{start_time_str} - {clip_info['title']} par {clip_info['broadcaster_name']}"
        escaped_text = text_content.replace("'", "'\\''") 
        
        drawtext_filters.append(
            f"drawtext="
            f"fontfile='{FONT_PATH}':"
            f"text='{escaped_text}':"
            f"x=(w-text_w)/2:"
            f"y=h-th-20:"
            f"fontsize=36:"
            f"fontcolor=white:"
            f"box=1:"
            f"boxcolor=black@0.6:"
            f"enable='between(t,{current_offset},{current_offset + min(clip_duration, 5)})'"
        )
        current_offset += clip_duration # Utilise la durée réelle pour l'offset

    video_filter_complex = ",".join(drawtext_filters)

    final_command = [
        "ffmpeg",
        "-i", temp_concat_video_path, # Vidéo concaténée (sans audio)
        "-i", temp_concat_audio_path, # Audio concaténé et normalisé
        "-filter_complex", video_filter_complex, # Applique les filtres de texte
        "-c:v", "libx264", # Réencodage vidéo avec H.264
        "-preset", "medium", # Préréglage de qualité/vitesse
        "-crf", "23", # Qualité (plus bas = meilleure qualité, plus gros fichier)
        "-map", "0:v:0", # Mappe le flux vidéo de la première entrée
        "-map", "1:a:0", # Mappe le flux audio de la deuxième entrée
        "-y", # Écrase le fichier de sortie s'il existe
        OUTPUT_VIDEO_PATH
    ]
    
    print(f"\nExécution de la commande FFmpeg (ajout timecodes et fusion finale): {' '.join(final_command)}")
    try:
        process = subprocess.run(final_command, check=True, capture_output=True, text=True)
        print(f"✅ Compilation vidéo finale terminée avec timecodes: {OUTPUT_VIDEO_PATH}")
        if process.stdout: print("FFmpeg STDOUT (final):\n", process.stdout)
        if process.stderr: print("FFmpeg STDERR (final):\n", process.stderr)

        # Nettoyage des fichiers temporaires
        os.remove(temp_concat_video_path)
        os.remove(temp_concat_audio_path)
        os.remove(CLIPS_LIST_TXT) # Le fichier clips_list.txt est aussi temporaire
        print("✅ Fichiers temporaires nettoyés.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la compilation vidéo finale : {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la compilation vidéo : {e}")
        sys.exit(1)

if __name__ == "__main__":
    compile_video()