import subprocess
import os
import json
import sys

INPUT_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_VIDEO_PATH = os.path.join("data", "compiled_video.mp4")
CLIPS_LIST_TXT = os.path.join("data", "clips_list.txt")

# Obtenir le répertoire racine du dépôt (où se trouve .github/)
# C'est généralement /home/runner/work/bot-clip-twitch/bot-clip-twitch/
REPO_ROOT = os.getcwd() 

def compile_video():
    print("🎬 Compilation des clips vidéo...")
    
    if not os.path.exists(INPUT_PATHS_JSON):
        print(f"❌ Fichier des chemins de clips téléchargés '{INPUT_PATHS_JSON}' introuvable.")
        sys.exit(1)

    with open(INPUT_PATHS_JSON, "r") as f:
        downloaded_clip_paths = json.load(f)

    if not downloaded_clip_paths:
        print("⚠️ Aucune vidéo téléchargée à compiler. La liste des chemins est vide. Fin de l'étape de compilation.")
        sys.exit(0)

    # Créer le fichier texte pour FFmpeg
    # Les chemins dans le fichier DOIVENT être des chemins absolus pour éviter toute ambiguïté.
    with open(CLIPS_LIST_TXT, "w") as f:
        for path in downloaded_clip_paths:
            # Assurer que le chemin est un chemin absolu complet pour FFmpeg
            # path est par exemple "data/raw_clips/clip_1_ID.mp4"
            # Nous le transformons en "/home/runner/work/.../data/raw_clips/clip_1_ID.mp4"
            full_absolute_path = os.path.join(REPO_ROOT, path)
            
            # Pour la commande ffmpeg, les chemins doivent être formatés correctement
            f.write(f"file '{full_absolute_path}'\n")

    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", CLIPS_LIST_TXT,
        "-c", "copy",
        OUTPUT_VIDEO_PATH # Ce chemin est déjà relatif à la racine du dépôt, ce qui est OK pour la sortie
    ]
    
    print(f"Exécution de la commande FFmpeg: {' '.join(command)}")

    try:
        # Exécuter la commande depuis le répertoire racine du dépôt
        subprocess.run(command, check=True, cwd=REPO_ROOT) # <-- Spécifie explicitement le répertoire de travail
        print(f"✅ Vidéo compilée avec succès : {OUTPUT_VIDEO_PATH}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la compilation vidéo : {e}")
        if e.stderr:
            print(f"FFmpeg STDERR: {e.stderr.decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la compilation vidéo : {e}")
        sys.exit(1)

if __name__ == "__main__":
    compile_video()