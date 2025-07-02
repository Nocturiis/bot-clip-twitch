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

# --- AJOUT IMPORTANT ---
# Liste des IDs de jeux pour lesquels vous voulez récupérer les clips.
# Vous DEVEZ fournir au moins un game_id ou broadcaster_id.
# Exemples:
#   "509670" pour "Just Chatting"
#   "32982" pour "Grand Theft Auto V"
#   "21779" pour "League of Legends"
#   "512965" pour "Valorant"
# Vous pouvez en ajouter plusieurs : GAME_IDS = ["509670", "32982"]
GAME_IDS = ["509670"] # REMPLACEZ PAR LES IDS DES JEUX QUE VOUS SOUHAITEZ CIBLER

# Vous pouvez aussi cibler par broadcaster_id si vous préférez
# BROADCASER_IDS = ["YOUR_BROADCASTER_ID"]

# --- FIN AJOUT IMPORTANT ---

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

def get_top_clips(access_token, num_clips_per_game=5, days_ago=1):
    """Fetches the top N clips from Twitch for the last X days for specified games."""
    print(f"📊 Récupération des {num_clips_per_game} clips Twitch par jeu pour les dernières {days_ago} jours...")
    
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_ago)
    
    all_top_clips = []

    # Itérer sur chaque game_id pour récupérer les clips
    for game_id in GAME_IDS:
        print(f"  - Recherche de clips pour le game_id: {game_id}")
        params = {
            "first": num_clips_per_game,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "game_id": game_id # <-- AJOUTE LE PARAMÈTRE game_id ICI
        }
        
        # Si vous utilisez broadcaster_id, vous l'ajouteriez ici à la place de game_id
        # if BROADCASER_IDS:
        #    params["broadcaster_id"] = BROADCASER_IDS[0] # Ou itérer sur eux

        print(f"Requête API Twitch avec started_at={params['started_at']} et ended_at={params['ended_at']} pour game_id={game_id}")

        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json()
            
            for clip in clips_data.get("data", []):
                all_top_clips.append({
                    "id": clip["id"],
                    "url": clip["url"],
                    "embed_url": clip["embed_url"],
                    "thumbnail_url": clip["thumbnail_url"],
                    "title": clip["title"],
                    "viewer_count": clip["viewer_count"],
                    "broadcaster_name": clip["broadcaster_name"],
                    "game_name": clip["game_name"],
                    "created_at": clip["created_at"]
                })
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des clips Twitch pour game_id {game_id} : {e}")
            if response.content:
                print(f"Contenu de la réponse API Twitch: {response.content.decode()}")
            # Ne pas sortir ici pour essayer d'autres game_id, mais logguer l'erreur.
            # sys.exit(1) # Ne pas exit ici si vous voulez essayer d'autres game_ids
    
    # Limiter le nombre total de clips à 10 après avoir collecté tous les clips par jeu
    # Vous pouvez ajuster cette logique si vous voulez EXACTEMENT 10 clips répartis
    # ou 10 clips par jeu. Ici, cela prendra les 10 premiers trouvés si plusieurs jeux.
    final_clips = sorted(all_top_clips, key=lambda x: x['viewer_count'], reverse=True)[:10]

    if not final_clips:
        print("⚠️ Aucun clip trouvé pour les critères spécifiés. Assurez-vous que les IDs de jeux sont corrects ou ajustez la période de recherche.")
        # Il est important de sortir ici si aucun clip n'est trouvé pour éviter que les scripts suivants ne plantent
        sys.exit(0) # Exit avec succès mais indique qu'aucun clip n'a été trouvé.
        
    with open(OUTPUT_CLIPS_JSON, "w", encoding="utf-8") as f:
        json.dump(final_clips, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(final_clips)} clips récupérés et sauvegardés dans {OUTPUT_CLIPS_JSON}")
    return final_clips

if __name__ == "__main__":
    token = get_twitch_access_token()
    if token:
        # On passe num_clips=5 pour avoir 5 clips par jeu, si on a plusieurs GAME_IDS
        # Si vous voulez un total de 10, ajustez la logique 'final_clips' en fin de fonction.
        # Ou laissez num_clips=10 et assurez-vous de n'avoir qu'un GAME_IDS si vous voulez 10 clips d'UN seul jeu.
        get_top_clips(token, num_clips_per_game=10)