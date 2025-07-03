import subprocess
import os
import json
import sys
from datetime import datetime, timedelta

# --- Chemins des fichiers ---
INPUT_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_VIDEO_PATH = os.path.join("output", "compiled_video.mp4")
CLIPS_METADATA_JSON = os.path.join("data", "top_clips.json") # Pour lire les métadonnées et durées
CLIPS_LIST_TXT = os.path.join("data", "clips_list.txt") # Utilisé pour concaténation initiale

# --- PARAMÈTRES FFmpeg ---
# Chemin de la police à utiliser pour les timecodes.
# Assurez-vous que ce fichier de police existe dans l'environnement d'exécution (ex: GitHub Actions)
# Pour une police par défaut, tu peux essayer 'Arial' ou 'DejaVuSans' si elles sont disponibles.
# Sinon, tu devras ajouter une étape à ton workflow pour télécharger et installer une police.
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

    if not os.path.exists(CLIPS_METADATA_JSON):
        print(f"❌ Fichier de métadonnées des clips '{CLIPS_METADATA_JSON}' introuvable. Nécessaire pour la sélection finale et les timecodes.")
        sys.exit(1)

    with open(INPUT_PATHS_JSON, "r") as f:
        downloaded_clip_paths_raw = json.load(f)

    with open(CLIPS_METADATA_JSON, "r", encoding="utf-8") as f:
        top_clips_metadata = json.load(f)

    if not downloaded_clip_paths_raw or not top_clips_metadata:
        print("⚠️ Aucune vidéo téléchargée ou aucune métadonnée à compiler. Fin de l'étape de compilation.")
        sys.exit(0)

    # Filtrer downloaded_clip_paths_raw et s'assurer que l'ordre correspond à top_clips_metadata
    final_clips_to_process = []
    downloaded_clip_map = {os.path.basename(p).split('_')[0]: p for p in downloaded_clip_paths_raw}
    
    for clip_meta in top_clips_metadata[:MAX_TOTAL_CLIPS]: # Limite ici aussi pour la sélection des métadonnées
        clip_id = clip_meta['id']
        if clip_id in downloaded_clip_map:
            final_clips_to_process.append({
                "path": os.path.join(REPO_ROOT, downloaded_clip_map[clip_id]),
                "duration": clip_meta.get('duration', 0.0),
                "title": clip_meta.get('title', 'Clip inconnu'),
                "broadcaster_name": clip_meta.get('broadcaster_name', 'Streamer inconnu')
            })
        if len(final_clips_to_process) >= MAX_TOTAL_CLIPS:
            break

    if not final_clips_to_process:
        print("⚠️ Après application des filtres et limites, aucune vidéo à compiler. Fin de l'étape.")
        sys.exit(0)

    print(f"Compilation de {len(final_clips_to_process)} clips (max {MAX_TOTAL_CLIPS} clips).")

    # --- Étape 1: Concaténation initiale (rapide) sans réencodage ---
    # Cette étape est toujours utile pour combiner les vidéos sans traitement coûteux.
    # Les timecodes et l'audio seront traités après.
    temp_concat_video_path = os.path.join(output_dir, "temp_concat_video_no_audio.mp4")
    temp_concat_audio_path = os.path.join(output_dir, "temp_concat_audio.aac")

    # Crée le fichier de liste pour la concaténation
    with open(CLIPS_LIST_TXT, "w") as f:
        for clip_info in final_clips_to_process:
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
    # Concaténation de tous les flux audio, puis normalisation avec loudnorm
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
    # Nous devons réencoder ici pour appliquer le filtre drawtext.
    
    drawtext_filters = []
    current_offset = 0.0
    for clip_info in final_clips_to_process:
        start_time_str = format_duration(current_offset)
        end_time_str = format_duration(current_offset + clip_info['duration'])
        
        # Le texte à afficher : Timecode + Titre du clip + Nom du streamer
        text_content = f"{start_time_str} - {clip_info['title']} par {clip_info['broadcaster_name']}"
        # Échapper les caractères spéciaux pour FFmpeg (ex: apostrophes)
        escaped_text = text_content.replace("'", "'\\''") 
        
        # Filtre drawtext pour chaque segment de clip
        # Il y a plusieurs façons d'écrire ces filtres. Voici une approche simple pour des timecodes qui apparaissent au début de chaque clip.
        # Le texte s'affiche pendant les 5 premières secondes du clip.
        drawtext_filters.append(
            f"drawtext="
            f"fontfile='{FONT_PATH}':"
            f"text='{escaped_text}':"
            f"x=(w-text_w)/2:" # Centré horizontalement
            f"y=h-th-20:"     # 20 pixels du bas
            f"fontsize=36:"   # Taille de la police
            f"fontcolor=white:"
            f"box=1:"         # Fond opaque
            f"boxcolor=black@0.6:" # Couleur du fond avec opacité
            f"enable='between(t,{current_offset},{current_offset + min(clip_info['duration'], 5)})'" # Affiche le texte pendant les 5 premières secondes ou la durée du clip
        )
        current_offset += clip_info['duration']

    # La chaîne de filtre complexe pour tous les drawtext
    video_filter_complex = ",".join(drawtext_filters)

    # Commande FFmpeg pour ajouter les timecodes et fusionner avec l'audio
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