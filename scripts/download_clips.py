import subprocess
import os
import json

INPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")
OUTPUT_CLIPS_DIR = os.path.join("data", "raw_clips")

def download_clips():
    print("📥 Téléchargement des clips Twitch individuels...")
    os.makedirs(OUTPUT_CLIPS_DIR, exist_ok=True)

    if not os.path.exists(INPUT_CLIPS_JSON):
        print(f"❌ Fichier des clips '{INPUT_CLIPS_JSON}' introuvable.")
        sys.exit(1)

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips = json.load(f)

    downloaded_files = []
    for i, clip in enumerate(clips):
        clip_url = clip["url"] # Utilisez l'URL de la page du clip
        output_filename = os.path.join(OUTPUT_CLIPS_DIR, f"clip_{i+1}_{clip['id']}.mp4")
        
        print(f"Téléchargement du clip {i+1}/{len(clips)}: {clip['title']} par {clip['broadcaster_name']}...")
        try:
            # yt-dlp sait gérer les URLs de clips Twitch
            command = [
                "yt-dlp",
                "--output", output_filename,
                "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                clip_url
            ]
            subprocess.run(command, check=True)
            print(f"  ✅ Clip téléchargé: {output_filename}")
            downloaded_files.append(output_filename)
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erreur lors du téléchargement du clip {clip_url}: {e}")
            if e.stderr: print(f"    STDERR: {e.stderr.decode()}")
            # Ne pas exit(1) ici pour que les autres clips puissent être téléchargés
            # mais enregistrer l'échec pour le montage
        except Exception as e:
            print(f"  ❌ Erreur inattendue lors du téléchargement du clip {clip_url}: {e}")

    # Sauvegarde la liste des fichiers téléchargés pour le script de compilation
    with open(os.path.join("data", "downloaded_clip_paths.json"), "w") as f:
        json.dump(downloaded_files, f)
    
    print("✅ Téléchargement des clips terminé.")

if __name__ == "__main__":
    download_clips()import subprocess
import os
import json

INPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")
OUTPUT_CLIPS_DIR = os.path.join("data", "raw_clips")

def download_clips():
    print("📥 Téléchargement des clips Twitch individuels...")
    os.makedirs(OUTPUT_CLIPS_DIR, exist_ok=True)

    if not os.path.exists(INPUT_CLIPS_JSON):
        print(f"❌ Fichier des clips '{INPUT_CLIPS_JSON}' introuvable.")
        sys.exit(1)

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips = json.load(f)

    downloaded_files = []
    for i, clip in enumerate(clips):
        clip_url = clip["url"] # Utilisez l'URL de la page du clip
        output_filename = os.path.join(OUTPUT_CLIPS_DIR, f"clip_{i+1}_{clip['id']}.mp4")
        
        print(f"Téléchargement du clip {i+1}/{len(clips)}: {clip['title']} par {clip['broadcaster_name']}...")
        try:
            # yt-dlp sait gérer les URLs de clips Twitch
            command = [
                "yt-dlp",
                "--output", output_filename,
                "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                clip_url
            ]
            subprocess.run(command, check=True)
            print(f"  ✅ Clip téléchargé: {output_filename}")
            downloaded_files.append(output_filename)
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erreur lors du téléchargement du clip {clip_url}: {e}")
            if e.stderr: print(f"    STDERR: {e.stderr.decode()}")
            # Ne pas exit(1) ici pour que les autres clips puissent être téléchargés
            # mais enregistrer l'échec pour le montage
        except Exception as e:
            print(f"  ❌ Erreur inattendue lors du téléchargement du clip {clip_url}: {e}")

    # Sauvegarde la liste des fichiers téléchargés pour le script de compilation
    with open(os.path.join("data", "downloaded_clip_paths.json"), "w") as f:
        json.dump(downloaded_files, f)
    
    print("✅ Téléchargement des clips terminé.")

if __name__ == "__main__":
    download_clips()