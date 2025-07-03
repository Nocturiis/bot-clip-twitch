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
                if clip_meta['id'] in path:
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

    # --- COMMANDE FFmpeg MODIFIÉE POUR RÉENCODAGE ET NORMALISATION ---
    # Ceci va prendre plus de temps mais résoudra les problèmes de format/codec.
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", CLIPS_LIST_TXT,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30", # Assure 1080p, pad si nécessaire, 30fps
        "-c:v", "libx264",         # Codec vidéo H.264
        "-preset", "fast",         # Vitesse d'encodage (medium, slow, etc. pour meilleure qualité)
        "-crf", "23",              # Qualité vidéo (plus petit = meilleure qualité, plus gros fichier)
        "-pix_fmt", "yuv420p",     # Format de pixel compatible avec la plupart des lecteurs
        "-c:a", "aac",             # Codec audio AAC
        "-b:a", "192k",             # Bitrate audio
        "-ac", "2",                # Stéréo
        "-ar", "44100",            # Fréquence d'échantillonnage audio
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", # Normalisation audio (Recommandé pour YouTube)
        OUTPUT_VIDEO_PATH
    ]
    
    print(f"Exécution de la commande FFmpeg (réencodage): {' '.join(command)}")

    try:
        # Exécuter la commande depuis le répertoire racine du dépôt
        process = subprocess.run(command, check=True, cwd=REPO_ROOT, capture_output=True, text=True) 
        print(f"✅ Vidéo compilée avec succès : {OUTPUT_VIDEO_PATH}")
        print("FFmpeg STDOUT:\n", process.stdout)
        if process.stderr:
            print("FFmpeg STDERR:\n", process.stderr) # Imprime le stderr même en cas de succès pour le debug

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