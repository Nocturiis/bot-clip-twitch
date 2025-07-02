import subprocess
import os
import json
import sys # <-- AJOUTEZ CETTE LIGNE

INPUT_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_VIDEO_PATH = os.path.join("data", "compiled_video.mp4")
CLIPS_LIST_TXT = os.path.join("data", "clips_list.txt")

def compile_video():
    print("🎬 Compilation des clips vidéo...")
    
    if not os.path.exists(INPUT_PATHS_JSON):
        print(f"❌ Fichier des chemins de clips téléchargés '{INPUT_PATHS_JSON}' introuvable.")
        sys.exit(1) # Quitter car on ne peut pas continuer sans la liste des clips

    with open(INPUT_PATHS_JSON, "r") as f:
        downloaded_clip_paths = json.load(f)

    if not downloaded_clip_paths:
        print("⚠️ Aucune vidéo téléchargée à compiler. La liste des chemins est vide. Fin de l'étape de compilation.")
        # Crée un fichier vidéo vide ou gère le cas dans l'étape suivante si nécessaire
        # Pour l'instant, on sort proprement.
        sys.exit(0) # Sortir avec succès car il n'y a pas d'erreur, juste pas de clips.

    # Créer le fichier texte pour FFmpeg
    # Le chemin dans le fichier doit être relatif au répertoire de travail de FFmpeg,
    # qui est la racine du dépôt ("/home/runner/work/bot-clip-twitch/bot-clip-twitch/")
    # Donc, on s'assure que les chemins commencent par "data/raw_clips/"
    with open(CLIPS_LIST_TXT, "w") as f:
        for path in downloaded_clip_paths:
            # Assurez-vous que le chemin est correct.
            # Il devrait déjà être "data/raw_clips/clip_..."
            # Si jamais il y avait un problème de double "data/", on le nettoierait ici.
            # Exemple : path.replace("data/data/", "data/")
            f.write(f"file '{path}'\n")

    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", CLIPS_LIST_TXT,
        "-c", "copy",
        OUTPUT_VIDEO_PATH
    ]
    
    print(f"Exécution de la commande FFmpeg: {' '.join(command)}")

    try:
        subprocess.run(command, check=True)
        print(f"✅ Vidéo compilée avec succès : {OUTPUT_VIDEO_PATH}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la compilation vidéo : {e}")
        if e.stderr:
            print(f"FFmpeg STDERR: {e.stderr.decode()}")
        sys.exit(1) # Quitter avec erreur si FFmpeg échoue
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la compilation vidéo : {e}")
        sys.exit(1)

if __name__ == "__main__":
    compile_video()