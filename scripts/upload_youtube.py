# scripts/upload_youtube.py
import os
import json
import io
import httplib2
import sys
import re # Importation ajoutée pour les expressions régulières
from datetime import datetime # Importation ajoutée pour la date dans le titre

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes requis pour l'upload de vidéo
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

COMPILED_VIDEO_PATH = os.path.join("data", "compiled_video.mp4")
THUMBNAIL_PATH = os.path.join("data", "thumbnail.jpg")
METADATA_JSON_PATH = os.path.join("data", "video_metadata.json") # CORRIGÉ

def upload_video():
    print("📤 Démarrage de l'upload YouTube...")

    # 1. Charger les métadonnées
    if not os.path.exists(METADATA_JSON_PATH):
        print(f"❌ Fichier de métadonnées '{METADATA_JSON_PATH}' introuvable.")
        sys.exit(1)
    with open(METADATA_JSON_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # --- DÉBUT DES MODIFICATIONS POUR LE TITRE ---
    original_title = metadata["title"]
    description = metadata["description"]
    tags = metadata["tags"]
    
    # Nettoyage et troncation du titre
    today_date_fr = datetime.now().strftime("%d %B") # Ex: "02 juillet"
    
    # Nettoyage du titre : supprimer les éléments potentiellement problématiques
    cleaned_title = original_title
    # Supprimer les émojis et caractères spéciaux non essentiels
    # Conserver alphanumériques, espaces et quelques ponctuations utiles
    cleaned_title = ''.join(c for c in cleaned_title if c.isalnum() or c.isspace() or c in ['!', '?', '.', ',', ':', ';', '-', '(', ')', '[', ']', '|', '\''])
    # Supprimer les mentions de !commands ou autres spam potentiels
    cleaned_title = re.sub(r'!\w+', '', cleaned_title) # Supprime !command
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip() # Remplace multiples espaces par un seul

    # Le titre final pour YouTube
    base_suffix = f" | Le Clip Twitch du Jour FR - {today_date_fr}"
    max_title_length = 100 # Limite de caractères pour les titres YouTube

    # Calculer la longueur maximale disponible pour le titre du clip nettoyé
    max_clip_title_length_allowed = max_title_length - len(base_suffix)

    # Si le titre nettoyé est trop long, le tronquer intelligemment
    if len(cleaned_title) > max_clip_title_length_allowed:
        truncated_clip_title = cleaned_title[:max_clip_title_length_allowed - 3].strip() # -3 pour "..."
        # S'assurer qu'on ne coupe pas un mot en plein milieu
        last_space = truncated_clip_title.rfind(' ')
        if last_space != -1:
            truncated_clip_title = truncated_clip_title[:last_space]
        cleaned_title = truncated_clip_title + "..."
    
    # Si le titre nettoyé est vide après le traitement, utiliser un titre par défaut
    if not cleaned_title:
        cleaned_title = "Le meilleur des clips Twitch"

    title = f"{cleaned_title}{base_suffix}"
    # --- FIN DES MODIFICATIONS POUR LE TITRE ---


    # Récupérer la catégorie et le statut de confidentialité depuis les métadonnées
    category_id = metadata.get("category_id", "20") # Par défaut "Gaming"
    privacy_status = metadata.get("privacyStatus", "public")

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
    
    thumbnail_present = False
    if os.path.exists(THUMBNAIL_PATH):
        thumbnail_present = True
    else:
        print(f"⚠️ Fichier miniature '{THUMBNAIL_PATH}' introuvable. La vidéo sera uploadée sans miniature personnalisée.")


    body = {
        "snippet": {
            "title": title, # Utilise le titre nettoyé et tronqué
            "description": description,
            "tags": tags,
            "categoryId": category_id # Utilise la catégorie des métadonnées
        },
        "status": {
            "privacyStatus": privacy_status, # Utilise le statut de confidentialité des métadonnées
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
        print(f"✅ Vidéo uploadée ! URL: https://www.youtube.com/watch?v={response['id']}") # Corrigé l'URL de YouTube
        
        # Uploader la miniature
        if thumbnail_present:
            print(f"Uploading thumbnail: '{THUMBNAIL_PATH}'...")
            try:
                youtube.thumbnails().set(
                    videoId=response['id'],
                    media_body=MediaFileUpload(THUMBNAIL_PATH)
                ).execute()
                print("✅ Miniature uploadée avec succès !")
            except Exception as thumbnail_e:
                print(f"❌ ERREUR lors de l'upload de la miniature : {thumbnail_e}")
                print("Cela peut être dû à des permissions manquantes sur votre chaîne YouTube pour les miniatures personnalisées.")
        else:
            print("⚠️ Pas de miniature trouvée, upload ignoré.")
        
        return True
    except Exception as e:
        print(f"❌ ERREUR lors de l'upload sur YouTube : {e}")
        sys.exit(1)

if __name__ == "__main__":
    upload_video()