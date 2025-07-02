import subprocess
import os
import json

INPUT_CLIPS_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_COMPILED_VIDEO = os.path.join("data", "compiled_video.mp4")

def compile_video():
    print("🎬 Compilation des clips vidéo...")
    
    if not os.path.exists(INPUT_CLIPS_PATHS_JSON):
        print(f"❌ Fichier des chemins de clips '{INPUT_CLIPS_PATHS_JSON}' introuvable.")
        sys.exit(1)

    with open(INPUT_CLIPS_PATHS_JSON, "r") as f:
        clip_files = json.load(f)
    
    if not clip_files:
        print("⚠️ Aucun clip à compiler. Arrêt.")
        sys.exit(0) # Exit with success if no clips to process

    # Création du fichier list.txt pour ffmpeg concat
    list_file_path = os.path.join("data", "clips_list.txt")
    with open(list_file_path, "w") as f:
        for clip_path in clip_files:
            # S'assurer que les chemins sont relatifs au dossier courant si ffmpeg est lancé depuis là
            # Ou chemins absolus, mais relatif est souvent plus simple pour concat.
            f.write(f"file '{clip_path}'\n")

    # Commande FFmpeg pour concaténer les vidéos
    # Utilisez '-c copy' pour concaténation rapide sans ré-encodage, si les formats sont identiques.
    # Si les formats/résolutions varient, il faudra ré-encoder (plus long, plus gourmand)
    # ffmpeg -f concat -safe 0 -i clips_list.txt -c copy output.mp4
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0", # Nécessaire si les chemins contiennent des caractères spéciaux ou sont générés
        "-i", list_file_path,
        "-c", "copy",
        OUTPUT_COMPILED_VIDEO
    ]

    print(f"Exécution de la commande FFmpeg: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        print(f"✅ Vidéo compilée dans {OUTPUT_COMPILED_VIDEO}")
        return OUTPUT_COMPILED_VIDEO
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la compilation vidéo : {e}")
        if e.stdout: print(f"    STDOUT: {e.stdout.decode()}")
        if e.stderr: print(f"    STDERR: {e.stderr.decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la compilation : {e}")
        sys.exit(1)

if __name__ == "__main__":
    compile_video()