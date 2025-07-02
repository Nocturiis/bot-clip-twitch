import requests
import os
import json
import sys # <-- AJOUTEZ CETTE LIGNE
from datetime import datetime, timedelta, timezone # <-- MODIFIEZ CETTE LIGNE, ajoutez 'timezone'

# Twitch API credentials from GitHub Secrets
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ ERREUR: TWITCH_CLIENT_ID ou TWITCH_CLIENT_SECRET non définis.")
    sys.exit(1)

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_URL = "https://api.twitch.tv/helix/clips"

OUTPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")

def get_twitch_access_token():
    """Gets an application access token for Twitch API."""
    print("🔑 Récupération du jeton d'accès Twitch...")
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    try:
        response = requests.post(TWITCH_AUTH_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()
        print("✅ Jeton d'accès Twitch récupéré.")
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération du jeton d'accès Twitch : {e}")
        sys.exit(1)

def get_top_clips(access_token, num_clips=10, days_ago=1):
    """Fetches the top N clips from Twitch for the last X days."""
    print(f"📊 Récupération des {num_clips} clips Twitch les plus populaires des dernières {days_ago} jours...")
    
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    # Calcul des dates pour la période de recherche
    # Utilisation de datetime.now(datetime.UTC) et formatage sans microsecondes
    end_date = datetime.now(timezone.utc) # Maintenant, en UTC
    start_date = end_date - timedelta(days=days_ago) # Il y a X jours, en UTC
    
    params = {
        "first": num_clips,
        "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'), # Format ISO 8601 sans microsecondes
        "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),     # Format ISO 8601 sans microsecondes
        "sort": "views" # Tri par nombre de vues
        # Vous pouvez ajouter 'game_id' ou 'broadcaster_id' pour filtrer
        # "game_id": "YOUR_GAME_ID" 
    }

    print(f"Requête API Twitch avec started_at={params['started_at']} et ended_at={params['ended_at']}") # Pour le debug

    try:
        response = requests.get(TWITCH_API_URL, headers=headers, params=params)
        response.raise_for_status()
        clips_data = response.json()
        
        # Filtre et sélectionne les informations pertinentes
        top_clips = []
        for clip in clips_data.get("data", []):
            top_clips.append({
                "id": clip["id"],
                "url": clip["url"], # URL de la page du clip
                "embed_url": clip["embed_url"], # URL pour intégrer le clip
                "thumbnail_url": clip["thumbnail_url"], # URL de la miniature
                "title": clip["title"],
                "viewer_count": clip["viewer_count"],
                "broadcaster_name": clip["broadcaster_name"],
                "game_name": clip["game_name"],
                "created_at": clip["created_at"]
            })
        
        # Sauvegarde les clips dans un fichier JSON
        with open(OUTPUT_CLIPS_JSON, "w", encoding="utf-8") as f:
            json.dump(top_clips, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(top_clips)} clips récupérés et sauvegardés dans {OUTPUT_CLIPS_JSON}")
        return top_clips
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des clips Twitch : {e}")
        # Affiche la réponse de l'API si elle est disponible pour plus de détails
        if response.content:
            print(f"Contenu de la réponse API Twitch: {response.content.decode()}")
        sys.exit(1) # <-- CORRECTION ici, sys est maintenant importé

if __name__ == "__main__":
    token = get_twitch_access_token()
    if token:
        get_top_clips(token)