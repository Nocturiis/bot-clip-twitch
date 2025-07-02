import subprocess
import os
import json
import sys

INPUT_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_VIDEO_PATH = os.path.join("data", "compiled_video.mp4")
CLIPS_LIST_TXT = os.path.join("data", "clips_list.txt")

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
    # Le chemin dans le fichier doit être relatif au répertoire de travail de FFmpeg,
    # qui est la racine du dépôt ("/home/runner/work/bot-clip-twitch/bot-clip-twitch/")
    with open(CLIPS_LIST_TXT, "w") as f:
        for path in downloaded_clip_paths:
            # Assurez-vous que le chemin est correct.
            # Il devrait déjà être "data/raw_clips/clip_..."
            # Nous allons explicitement nous assurer qu'il n'y a qu'une seule instance de "data/" au début
            
            # Méthode plus robuste pour garantir le bon chemin relatif
            # On prend la partie du chemin après "data/" (s'il y a un "data/" au début)
            # Puis on la reconstitue avec un seul "data/"
            
            # Initialement, les chemins sont par exemple : "data/raw_clips/clip_1_ID.mp4"
            # Si pour une raison inconnue ils devenaient "/home/runner/work/.../data/raw_clips/...",
            # ou "data/data/raw_clips/...", cette logique les normaliserait.
            
            if path.startswith("data/raw_clips/"):
                cleaned_path = path # Le chemin est déjà correct
            elif path.startswith("raw_clips/"): # Si pour une raison l'étape de DL omet "data/"
                cleaned_path = os.path.join("data", path)
            elif "data/data/raw_clips/" in path: # Cas de l'erreur persistante
                cleaned_path = path.replace("data/data/raw_clips/", "data/raw_clips/")
            else:
                cleaned_path = path # Garde le chemin tel quel si non reconnu
            
            # Pour être absolument certain, on peut aussi reconstruire le chemin depuis la racine si nécessaire.
            # Mais les chemins sont déjà relatifs à la racine.
            
            f.write(f"file '{cleaned_path}'\n")

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
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la compilation vidéo : {e}")
        sys.exit(1)

if __name__ == "__main__":
    compile_video()