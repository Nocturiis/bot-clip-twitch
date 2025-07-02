# scripts/upload_youtube.py
import os
import json
import io
import httplib2
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes requis pour l'upload de vidéo
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

COMPILED_VIDEO_PATH = os.path.join("data", "compiled_video.mp4")
THUMBNAIL_PATH = os.path.join("data", "thumbnail.jpg")
METADATA_JSON_PATH = os.path.join("data", "metadata.json")

def upload_video():
    print("📤 Démarrage de l'upload YouTube...")

    # 1. Charger les métadonnées
    if not os.path.exists(METADATA_JSON_PATH):
        print(f"❌ Fichier de métadonnées '{METADATA_JSON_PATH}' introuvable.")
        sys.exit(1)
    with open(METADATA_JSON_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    title = metadata["title"]
    description = metadata["description"]
    tags = metadata["tags"]

    # 2. Authentification YouTube (via Refresh Token)
    creds = None
    refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
    client_id = os.getenv('YOUTUBE_CLIENT_ID')
    client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
    
    if not all([refresh_token, client_id, client_secret]):
        print("❌ ERREUR: YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID ou YOUTUBE_CLIENT_SECRET manquants.")
        print("Veuillez vous assurer que tous les secrets GitHub sont configurés.")
        sys.exit(1)
        
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    print("✅ Tentative d'authentification YouTube via Refresh Token...")

    try:
        creds.refresh(Request())
        print("✅ Refresh Token utilisé avec succès pour obtenir un nouveau jeton d'accès.")
    except Exception as e:
        print(f"❌ Échec du rafraîchissement du jeton d'accès : {e}")
        print("Vérifiez YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET et la validité du token.")
        sys.exit(1)
        

    # Construire le service YouTube
    youtube = build("youtube", "v3", credentials=creds)

    # 3. Préparer la vidéo et la miniature
    if not os.path.exists(COMPILED_VIDEO_PATH):
        print(f"❌ Fichier vidéo compilée '{COMPILED_VIDEO_PATH}' introuvable.")
        sys.exit(1)
    if not os.path.exists(THUMBNAIL_PATH):
        print(f"❌ Fichier miniature '{THUMBNAIL_PATH}' introuvable.")
        # Ne pas exit ici, on peut uploader sans miniature, mais c'est mieux de la logger.
        thumbnail_present = False
    else:
        thumbnail_present = True

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "20" # Catégorie "Gaming" (20) ou "People & Blogs" (22) ou "Entertainment" (24)
        },
        "status": {
            "privacyStatus": "public", # ou "unlisted" pour tester
            "selfDeclaredMadeForKids": False # Important: doit être False si pas pour enfants
        }
    }

    # Uploader la vidéo
    media_body = MediaFileUpload(COMPILED_VIDEO_PATH, resumable=True)

    print(f"Uploading video: '{title}'...")
    insert_request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media_body
    )

    try:
        response = insert_request.execute()
        print(f"✅ Vidéo uploadée ! URL: https://www.youtube.com/watch?v={response['id']}")
        
        # Uploader la miniature
        if thumbnail_present:
            print(f"Uploading thumbnail: '{THUMBNAIL_PATH}'...")
            youtube.thumbnails().set(
                videoId=response['id'],
                media_body=MediaFileUpload(THUMBNAIL_PATH)
            ).execute()
            print("✅ Miniature uploadée avec succès !")
        else:
            print("⚠️ Pas de miniature trouvée, upload ignoré.")
        
        return True
    except Exception as e:
        print(f"❌ ERREUR lors de l'upload sur YouTube : {e}")
        sys.exit(1)

if __name__ == "__main__":
    upload_video()