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
        sys.exit(1)

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips = json.load(f)

    if not clips:
        print("⚠️ Aucun clip à télécharger. La liste des clips est vide.")
        with open(os.path.join("data", "downloaded_clip_paths.json"), "w") as f:
            json.dump([], f)
        return

    downloaded_and_processed_files = [] # Will store paths to the PROCESSED clips
    for i, clip in enumerate(clips):
        clip_url = clip["url"]
        
        clip_id = clip.get("id", f"unknown_id_{i}")
        # Escape single quotes and colons for FFmpeg drawtext filter
        clip_title = clip.get("title", "Titre inconnu").replace("'", "\\'").replace(":", "\\:")
        broadcaster_name = clip.get("broadcaster_name", "Streamer inconnu").replace("'", "\\'").replace(":", "\\:")

        raw_output_filename = os.path.join(RAW_CLIPS_DIR, f"clip_raw_{clip_id}.mp4") # Store raw download
        processed_output_filename = os.path.join(PROCESSED_CLIPS_DIR, f"clip_processed_{clip_id}.mp4") # Store processed version
        
        print(f"Téléchargement du clip {i+1}/{len(clips)}: {clip_title} par {broadcaster_name}...")
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
            
            # Text for title and streamer
            title_text = f"Titre: {clip_title}"
            broadcaster_text = f"Streamer: {broadcaster_name}"

            # FFmpeg filtergraph for scaling, padding, FPS, and drawing text
            # We'll use a standard font like 'LiberationSans'
            # Positioning:
            # Title: Top-center, slightly down from the very top
            # Streamer: Below the title, with a small margin
            
            # Font settings
            font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf" # Common path for a standard font
            font_size = 36 # Slightly smaller for two lines, adjust as needed
            text_color = "white"
            border_color = "black"
            border_width = 2

            # Drawtext filter for the title
            title_filter = (
                f"drawtext=fontfile='{font_path}':"
                f"text='{title_text}':"
                f"x=(w-text_w)/2:y=H*0.04:" # 4% from top
                f"fontcolor={text_color}:fontsize={font_size}:"
                f"bordercolor={border_color}:borderw={border_width}"
            )
            
            # Drawtext filter for the broadcaster name, positioned below the title
            broadcaster_filter = (
                f"drawtext=fontfile='{font_path}':"
                f"text='{broadcaster_text}':"
                f"x=(w-text_w)/2:y=H*0.04+text_h+5:" # Below title + 5 pixels margin
                f"fontcolor={text_color}:fontsize={font_size}:"
                f"bordercolor={border_color}:borderw={border_width}"
            )
            
            # Combine all video filters: scaling/padding/fps AND both drawtext filters
            # We chain the drawtext filters using commas
            video_filters = (
                "scale=1920:1080:force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                "setsar=1,fps=30,"
                f"{title_filter}," # Add the title drawtext filter
                f"{broadcaster_filter}" # Add the broadcaster drawtext filter
            )

            ffmpeg_preprocess_command = [
                "ffmpeg",
                "-i", raw_output_filename, # Input is the raw downloaded clip
                "-vf", video_filters, # Use the combined video filters
                "-c:v", "libx264",         # H.264 video codec
                "-preset", "fast",         # Encoding speed (can be medium/slow for better quality)
                "-crf", "23",              # Video quality (lower = higher quality, larger file)
                "-pix_fmt", "yuv420p",     # Pixel format compatible with most players
                "-c:a", "aac",             # AAC audio codec
                "-b:a", "192k",             # Audio bitrate
                "-ac", "2",                # Stereo audio
                "-ar", "44100",            # Audio sample rate
                "-loglevel", "error",      # Suppress verbose FFmpeg output, show only errors
                "-y",                      # Overwrite output file without asking
                processed_output_filename  # Output is the processed clip
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