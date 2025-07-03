import subprocess
import os
import json
import sys
from datetime import datetime # Pour le nommage temporaire ou la gestion des logs

# --- Chemins des fichiers ---
INPUT_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_VIDEO_PATH = os.path.join("output", "compiled_video.mp4") # Changement vers le dossier output
CLIPS_METADATA_JSON = os.path.join("data", "top_clips.json") # Ajout pour lire les métadonnées
CLIPS_LIST_TXT = os.path.join("data", "clips_list.txt")

# --- NOUVEAU PARAMÈTRE : Limite le nombre total de clips dans la compilation finale ---
MAX_TOTAL_CLIPS = 20

# Obtenir le répertoire racine du dépôt (où se trouve .github/)
# C'est généralement /home/runner/work/bot-clip-twitch/bot-clip-twitch/
REPO_ROOT = os.getcwd() # CWD est correct dans un contexte GitHub Actions

def compile_video():
    print("🎬 Démarrage de la compilation des clips vidéo...")

    # --- NOUVELLE AJOUTATION ICI : Création du dossier 'output' ---
    output_dir = os.path.dirname(OUTPUT_VIDEO_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Dossier de sortie créé : {output_dir}")
    # --- FIN DE L'AJOUTATION ---
    
    if not os.path.exists(INPUT_PATHS_JSON):
        print(f"❌ Fichier des chemins de clips téléchargés '{INPUT_PATHS_JSON}' introuvable.")
        sys.exit(1)

    if not os.path.exists(CLIPS_METADATA_JSON):
        print(f"❌ Fichier de métadonnées des clips '{CLIPS_METADATA_JSON}' introuvable. Nécessaire pour la sélection finale.")
        sys.exit(1)

    with open(INPUT_PATHS_JSON, "r") as f:
        downloaded_clip_paths = json.load(f)

    with open(CLIPS_METADATA_JSON, "r", encoding="utf-8") as f:
        top_clips_metadata = json.load(f)

    if not downloaded_clip_paths or not top_clips_metadata:
        print("⚠️ Aucune vidéo téléchargée ou aucune métadonnée à compiler. Fin de l'étape de compilation.")
        sys.exit(0)

    # --- NOUVEAU : Limiter le nombre de clips à compiler (si la liste est plus longue) ---
    # Nous utilisons top_clips_metadata car elle est déjà ordonnée et filtrée
    # Assurez-vous que l'ordre des clips dans downloaded_clip_paths corresponde à top_clips_metadata
    # L'approche la plus sûre est de filtrer downloaded_clip_paths en se basant sur les IDs de top_clips_metadata
    
    # Créer un ensemble des IDs de clips dans top_clips_metadata (limitée à MAX_TOTAL_CLIPS)
    selected_clip_ids = {clip['id'] for clip in top_clips_metadata[:MAX_TOTAL_CLIPS]}
    
    # Filtrer downloaded_clip_paths pour inclure uniquement les clips sélectionnés
    # Et maintenir l'ordre des clips sélectionnés
    final_clips_to_compile = []
    # Nous allons recréer la liste des chemins pour assurer l'ordre et la limite
    for clip_meta in top_clips_metadata:
        if clip_meta['id'] in selected_clip_ids:
            # Trouvez le chemin correspondant dans downloaded_clip_paths
            # Par convention, le chemin contient l'ID du clip
            found_path = None
            for path in downloaded_clip_paths:
                if clip_meta['id'] in path: # Check for clip ID in the path
                    found_path = path
                    break
            if found_path:
                final_clips_to_compile.append(found_path)
            # Retirer l'ID du set pour une recherche plus rapide
            selected_clip_ids.discard(clip_meta['id']) 
        if len(final_clips_to_compile) >= MAX_TOTAL_CLIPS:
            break # Atteint la limite

    if not final_clips_to_compile:
        print("⚠️ Après application des filtres et limites, aucune vidéo à compiler. Fin de l'étape.")
        sys.exit(0)

    print(f"Compiling {len(final_clips_to_compile)} clips (max {MAX_TOTAL_CLIPS} clips).")

    # Créer le fichier texte pour FFmpeg
    # Les chemins dans le fichier DOIVENT être des chemins absolus pour éviter toute ambiguïté.
    with open(CLIPS_LIST_TXT, "w") as f:
        for path in final_clips_to_compile: # Utilise la liste filtrée et limitée
            full_absolute_path = os.path.join(REPO_ROOT, path)
            f.write(f"file '{full_absolute_path}'\n")

    # --- COMMANDE FFmpeg MODIFIÉE POUR CONCATÉNER RAPIDEMENT ---
    # Les clips sont déjà prétraités par download_clips.py
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", CLIPS_LIST_TXT,
        "-c", "copy", # Simply copy the streams, no re-encoding needed here
        "-an", # Remove audio stream. We will re-add a normalized audio stream in a separate pass if needed.
        OUTPUT_VIDEO_PATH # Output with no audio first
    ]
    
    print(f"Exécution de la commande FFmpeg (concaténation vidéo rapide): {' '.join(command)}")

    try:
        process = subprocess.run(command, check=True, cwd=REPO_ROOT, capture_output=True, text=True) 
        print(f"✅ Vidéo compilée (partie vidéo) avec succès : {OUTPUT_VIDEO_PATH}")
        print("FFmpeg STDOUT (video only):\n", process.stdout)
        if process.stderr:
            print("FFmpeg STDERR (video only):\n", process.stderr)

        # --- NOUVELLE ÉTAPE : Normalisation audio et ajout à la vidéo compilée ---
        # Créez un fichier temporaire pour la vidéo avec l'audio traité
        temp_output_with_audio_path = os.path.join(output_dir, "compiled_video_temp_audio.mp4")

        # Get all audio streams from processed clips and combine them
        audio_inputs = []
        for path in final_clips_to_compile:
            audio_inputs.extend(["-i", os.path.join(REPO_ROOT, path)])
        
        # Command to combine and normalize audio
        audio_command = [
            "ffmpeg",
            *audio_inputs, # All processed clips as inputs
            "-filter_complex", 
            f"[0:a][1:a]concat=n={len(final_clips_to_compile)}:v=0:a=1[aout];[aout]loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ac", "2",
            "-ar", "44100",
            "-vn", # No video output
            "-y",
            os.path.join(output_dir, "compiled_audio.aac") # Output combined and normalized audio
        ]

        print(f"\nExécution de la commande FFmpeg (extraction et normalisation audio): {' '.join(audio_command)}")
        audio_process = subprocess.run(audio_command, check=True, cwd=REPO_ROOT, capture_output=True, text=True)
        print("✅ Audio combiné et normalisé avec succès.")
        if audio_process.stdout: print("FFmpeg STDOUT (audio):\n", audio_process.stdout)
        if audio_process.stderr: print("FFmpeg STDERR (audio):\n", audio_process.stderr)

        # Merge video and audio
        merge_command = [
            "ffmpeg",
            "-i", OUTPUT_VIDEO_PATH, # Video only
            "-i", os.path.join(output_dir, "compiled_audio.aac"), # Normalized audio
            "-c:v", "copy",
            "-c:a", "copy",
            "-map", "0:v:0", # Map video stream from first input
            "-map", "1:a:0", # Map audio stream from second input
            "-y", # Overwrite output if exists
            temp_output_with_audio_path
        ]
        
        print(f"\nExécution de la commande FFmpeg (fusion vidéo et audio): {' '.join(merge_command)}")
        merge_process = subprocess.run(merge_command, check=True, cwd=REPO_ROOT, capture_output=True, text=True)
        print("✅ Vidéo finale avec audio normalisé créée.")
        if merge_process.stdout: print("FFmpeg STDOUT (merge):\n", merge_process.stdout)
        if merge_process.stderr: print("FFmpeg STDERR (merge):\n", merge_process.stderr)

        # Replace the video-only file with the merged one
        os.replace(temp_output_with_audio_path, OUTPUT_VIDEO_PATH)
        # Clean up temporary audio file
        os.remove(os.path.join(output_dir, "compiled_audio.aac"))
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la compilation vidéo : {e}")
        if e.stdout:
            print(f"FFmpeg STDOUT: {e.stdout}")
        if e.stderr:
            print(f"FFmpeg STDERR: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la compilation vidéo : {e}")
        sys.exit(1)

if __name__ == "__main__":
    compile_video()