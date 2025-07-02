import requests
import os
import json
import sys
from datetime import datetime, timedelta, timezone

# Twitch API credentials from GitHub Secrets
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ ERREUR: TWITCH_CLIENT_ID ou TWITCH_CLIENT_SECRET non définis.")
    sys.exit(1)

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_URL = "https://api.twitch.tv/helix/clips"

OUTPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")

# --- IMPORTANT ADDITION / MODIFICATION ---
# List of game IDs for which you want to retrieve clips.
# You MUST provide at least one game_id or broadcaster_id.
# Examples:
#   "509670" for "Just Chatting"
#   "32982" for "Grand Theft Auto V"
#   "21779" for "League of Legends"
#   "512965" for "Valorant"
# You can add multiple: GAME_IDS = ["509670", "32982"]
GAME_IDS = ["509670"] # CHANGE THIS TO YOUR DESIRED GAME IDs
# --- END IMPORTANT ADDITION / MODIFICATION ---

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

def get_top_clips(access_token, num_clips_per_game=10, days_ago=1):
    """Fetches the top N clips from Twitch for the last X days for specified games."""
    print(f"📊 Récupération des {num_clips_per_game} clips Twitch par jeu pour les dernières {days_ago} jours...")
    
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_ago)
    
    all_top_clips = []

    # Iterate over each game_id to retrieve clips
    for game_id in GAME_IDS:
        print(f"  - Recherche de clips pour le game_id: {game_id}")
        params = {
            "first": num_clips_per_game,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "game_id": game_id
        }
        
        print(f"Requête API Twitch avec started_at={params['started_at']} et ended_at={params['ended_at']} pour game_id={game_id}")

        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json()
            
            if not clips_data.get("data"):
                print(f"  ⚠️ Aucune donnée de clip trouvée pour game_id {game_id} dans la période spécifiée.")
                print(f"  Réponse complète de l'API Twitch (pas de clips): {json.dumps(clips_data, indent=2)}")
                continue # Skip to the next game_id if no data

            for clip in clips_data.get("data", []):
                # Using .get() with a default value to prevent KeyError
                all_top_clips.append({
                    "id": clip.get("id"),
                    "url": clip.get("url"),
                    "embed_url": clip.get("embed_url"),
                    "thumbnail_url": clip.get("thumbnail_url"),
                    "title": clip.get("title"),
                    "viewer_count": clip.get("viewer_count", 0), # Default to 0 if not present
                    "broadcaster_name": clip.get("broadcaster_name"),
                    "game_name": clip.get("game_name"),
                    "created_at": clip.get("created_at")
                })
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des clips Twitch pour game_id {game_id} : {e}")
            if response.content:
                print(f"    Contenu de la réponse API Twitch: {response.content.decode()}")
            # Do not exit here to allow other game_ids to be attempted.
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON pour game_id {game_id}: {e}")
            if response.content:
                print(f"    Contenu brut de la réponse: {response.content.decode()}")


    # Limit the total number of clips to 10 after collecting all clips per game
    # Sort by viewer_count (descending) and take the top 10
    final_clips = sorted(all_top_clips, key=lambda x: x['viewer_count'], reverse=True)[:10]

    if not final_clips:
        print("⚠️ Aucun clip trouvé pour les critères spécifiés sur TOUS les jeux. Assurez-vous que les IDs de jeux sont corrects ou ajustez la période de recherche.")
        sys.exit(0) # Exit successfully but indicate no clips were found.
        
    with open(OUTPUT_CLIPS_JSON, "w", encoding="utf-8") as f:
        json.dump(final_clips, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(final_clips)} clips récupérés et sauvegardés dans {OUTPUT_CLIPS_JSON}")
    return final_clips

if __name__ == "__main__":
    token = get_twitch_access_token()
    if token:
        get_top_clips(token, num_clips_per_game=10) # Request up to 10 clips per game