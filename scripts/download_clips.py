import subprocess
import os
import json
import sys

INPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")
RAW_CLIPS_DIR = os.path.join("data", "raw_clips") # Keep original downloads here
PROCESSED_CLIPS_DIR = os.path.join("data", "processed_clips") # New directory for consistent clips

def download_clips():
    print("📥 Démarrage du téléchargement et du prétraitement des clips Twitch individuels...")
    os.makedirs(RAW_CLIPS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_CLIPS_DIR, exist_ok=True) # Create the new processed clips directory

    if not os.path.exists(INPUT_CLIPS_JSON):
        print(f"❌ Fichier des clips '{INPUT_CLIPS_JSON}' introuvable.")
        # Écrire un fichier JSON vide pour downloaded_clip_paths.json
        with open(os.path.join("data", "downloaded_clip_paths.json"), "w") as f:
            json.dump([], f)
        sys.exit(1)

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips = json.load(f)

    if not clips:
        print("⚠️ Aucun clip à télécharger. La liste des clips est vide.")
        with open(os.path.join("data", "downloaded_clip_paths.json"), "w") as f:
            json.dump([], f)
        # N'appelle pas sys.exit(0) ici, car cela arrêterait le workflow avant compile_video
        # qui doit pouvoir gérer un downloaded_clip_paths.json vide et afficher son propre message.
        return

    downloaded_and_processed_files = [] # Will store paths to the PROCESSED clips
    for i, clip in enumerate(clips):
        clip_url = clip["url"]
        
        clip_id = clip.get("id", f"unknown_id_{i}")
        # Escape single quotes and colons for FFmpeg drawtext filter
        clip_title = clip.get("title", "Titre inconnu").replace("'", "'\\''")
        broadcaster_name = clip.get("broadcaster_name", "Streamer inconnu").replace("'", "'\\''")

        # --- CORRECTION ICI : Modifier le nom du fichier pour inclure l'ID au début ---
        raw_output_filename = os.path.join(RAW_CLIPS_DIR, f"{clip_id}_raw.mp4")
        processed_output_filename = os.path.join(PROCESSED_CLIPS_DIR, f"{clip_id}_processed.mp4")
        # --- FIN DE LA CORRECTION ---
        
        print(f"Téléchargement du clip {i+1}/{len(clips)}: {clip_title} par {broadcaster_name} (ID: {clip_id})...")
        try:
            # 1. Téléchargement avec yt-dlp
            yt_dlp_command = [
                "yt-dlp",
                "--output", raw_output_filename,
                "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                clip_url
            ]
            subprocess.run(yt_dlp_command, check=True)
            print(f"  ✅ Clip téléchargé: {raw_output_filename}")

            # 2. Prétraitement avec FFmpeg pour normaliser le format, les codecs et ajouter du texte
            print(f"  Prétraitement du clip {i+1}/{len(clips)}: {clip_title} (ajout du texte)...")
            
            title_display = f"Titre: {clip_title}"
            broadcaster_display = f"Streamer: {broadcaster_name}"

            # Font settings - Ensure this font is available in your GitHub Actions runner or provide its path
            # For robustness, consider providing fallback fonts or installing a common one in your workflow.
            # 'LiberationSans' or 'DejaVuSans' are often available on Linux runners.
            font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf" 
            # Fallback to DejaVuSans if LiberationSans is not found (common on GitHub Actions)
            if not os.path.exists(font_path):
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Regular.ttf"
                if not os.path.exists(font_path):
                    # As a last resort, just use the font name if FFmpeg can resolve it, but it's less reliable
                    font_path = "sans-serif" # Generic font family name for FFmpeg
                    print(f"⚠️ Police spécifique non trouvée. Utilisation d'une police générique '{font_path}'.")


            font_size = 36
            text_color = "white"
            border_color = "black"
            border_width = 2

            title_filter = (
                f"drawtext=fontfile='{font_path}':"
                f"text='{title_display}':"
                f"x=(w-text_w)/2:y=H*0.04:"
                f"fontcolor={text_color}:fontsize={font_size}:"
                f"bordercolor={border_color}:borderw={border_width}"
            )
            
            broadcaster_filter = (
                f"drawtext=fontfile='{font_path}':"
                f"text='{broadcaster_display}':"
                f"x=(w-text_w)/2:y=H*0.04+text_h+5:"
                f"fontcolor={text_color}:fontsize={font_size}:"
                f"bordercolor={border_color}:borderw={border_width}"
            )
            
            video_filters = (
                "scale=1920:1080:force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                "setsar=1,fps=30,"
                f"{title_filter},"
                f"{broadcaster_filter}"
            )

            ffmpeg_preprocess_command = [
                "ffmpeg",
                "-i", raw_output_filename,
                "-vf", video_filters,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ac", "2",
                "-ar", "44100",
                "-loglevel", "error",
                "-y",
                processed_output_filename
            ]
            subprocess.run(ffmpeg_preprocess_command, check=True, capture_output=True, text=True)
            print(f"  ✅ Clip prétraité avec texte: {processed_output_filename}")
            downloaded_and_processed_files.append(processed_output_filename)

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erreur lors du traitement du clip {clip_url} (téléchargement ou prétraitement): {e}")
            if e.stdout: print(f"    STDOUT: {e.stdout}")
            if e.stderr: print(f"    STDERR: {e.stderr}")
        except Exception as e:
            print(f"  ❌ Erreur inattendue lors du traitement du clip {clip_url}: {e}")

    # Sauvegarde la liste des fichiers TÉLÉCHARGÉS ET PRÉTRAITÉS pour le script de compilation
    with open(os.path.join("data", "downloaded_clip_paths.json"), "w") as f:
        json.dump(downloaded_and_processed_files, f)
    
    print("✅ Téléchargement et prétraitement des clips terminé.")

if __name__ == "__main__":
    download_clips()