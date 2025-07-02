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

# --- IMPORTANT MODIFICATIONS START HERE ---

# Liste des IDs de jeux pour lesquels vous voulez récupérer des clips.
# Vous pouvez trouver les IDs de jeux en utilisant l'API Twitch "helix/games?name=NomDuJeu".
# Exemples d'IDs de jeux populaires :
#   "509670": "Just Chatting" (Très général, souvent en français)
#   "32982": "Grand Theft Auto V"
#   "512965": "Valorant"
#   "21779": "League of Legends"
# Ajoutez d'autres IDs de jeux si vous le souhaitez.
GAME_IDS = ["509670", "32982", "512965", "21779"] # Exemples, à ajuster

# Liste des IDs de streamers francophones populaires.
# C'est le MEILLEUR moyen de cibler le contenu francophone.
# Pour trouver l'ID d'un streamer, utilisez l'API Twitch "helix/users?login=NomDuStreamer"
# (Exemple de requête : https://api.twitch.tv/helix/users?login=squeezie )
# REMPLACEZ CES EXEMPLES PAR DE VRAIS IDs de streamers francophones populaires
BROADCASTER_IDS = [
    "52130765",  # Squeezie 
    "41719107",  # ZeratoR 
    "24147592",  # Gotaga 
    "134966333",  # Kameto
    "737048563" # Anyme023
    "496105401" # byilhann
    "887001013" # Nico_la
    "60256640" # Flamby
    "253195796" #  helydia
    "80716629" # Inoxtag
    "175560856" #Hctuan
    # Ajoutez d'autres IDs de streamers francophones ici
]

# --- IMPORTANT MODIFICATIONS END HERE ---

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

def get_top_clips(access_token, num_clips_per_source=5, days_ago=1):
    """Fetches the top N clips from Twitch for the last X days for specified games and broadcasters."""
    print(f"📊 Récupération des {num_clips_per_source} clips Twitch par source (jeu/streamer) pour les dernières {days_ago} jours...")
    
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_ago)
    
    all_top_clips = []

    # --- NOUVELLE LOGIQUE DE RECHERCHE PAR GAME_ID ET BROADCASTER_ID ---

    # Recherche de clips par Game ID
    for game_id in GAME_IDS:
        print(f"  - Recherche de clips pour le game_id: {game_id}")
        params = {
            "first": num_clips_per_source,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "game_id": game_id
        }
        
        # print(f"Requête API Twitch avec started_at={params['started_at']} et ended_at={params['ended_at']} pour game_id={game_id}") # Debugging détaillé

        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json()
            
            if not clips_data.get("data"):
                print(f"  ⚠️ Aucune donnée de clip trouvée pour game_id {game_id} dans la période spécifiée.")
                # print(f"  Réponse complète de l'API Twitch (pas de clips): {json.dumps(clips_data, indent=2)}") # Debugging détaillé
                continue

            for clip in clips_data.get("data", []):
                # Using .get() with a default value to prevent KeyError and ensure 'views: 0' is not due to missing key
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
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON pour game_id {game_id}: {e}")
            if response.content:
                print(f"    Contenu brut de la réponse: {response.content.decode()}")

    # Recherche de clips par Broadcaster ID
    for broadcaster_id in BROADCASTER_IDS:
        print(f"  - Recherche de clips pour le broadcaster_id: {broadcaster_id}")
        params = {
            "first": num_clips_per_source,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "broadcaster_id": broadcaster_id # <-- C'EST ICI QU'ON UTILISE L'ID DU STREAMER
        }

        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json()

            if not clips_data.get("data"):
                print(f"  ⚠️ Aucune donnée de clip trouvée pour broadcaster_id {broadcaster_id} dans la période spécifiée.")
                continue

            for clip in clips_data.get("data", []):
                all_top_clips.append({
                    "id": clip.get("id"),
                    "url": clip.get("url"),
                    "embed_url": clip.get("embed_url"),
                    "thumbnail_url": clip.get("thumbnail_url"),
                    "title": clip.get("title"),
                    "viewer_count": clip.get("viewer_count", 0),
                    "broadcaster_name": clip.get("broadcaster_name"),
                    "game_name": clip.get("game_name"),
                    "created_at": clip.get("created_at")
                })
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des clips Twitch pour broadcaster_id {broadcaster_id} : {e}")
            if response.content:
                print(f"    Contenu de la réponse API Twitch: {response.content.decode()}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON pour broadcaster_id {broadcaster_id}: {e}")
            if response.content:
                print(f"    Contenu brut de la réponse: {response.content.decode()}")

    # --- FIN DE LA NOUVELLE LOGIQUE ---

    # Après avoir collecté tous les clips de toutes les sources, triez globalement et prenez le TOP 10.
    # On trie par 'viewer_count' en s'assurant qu'il y a une valeur par défaut de 0 au cas où.
    final_clips = sorted(all_top_clips, key=lambda x: x.get('viewer_count', 0), reverse=True)[:10]

    if not final_clips:
        print("⚠️ Aucun clip trouvé pour les critères spécifiés sur TOUS les jeux/streamers. Assurez-vous que les IDs sont corrects ou ajustez la période de recherche.")
        sys.exit(0)
        
    with open(OUTPUT_CLIPS_JSON, "w", encoding="utf-8") as f:
        json.dump(final_clips, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(final_clips)} clips récupérés et sauvegardés dans {OUTPUT_CLIPS_JSON}")
    return final_clips

if __name__ == "__main__":
    token = get_twitch_access_token()
    if token:
        # num_clips_per_source: combien de clips on demande par jeu ET par streamer.
        # Par exemple, si vous avez 3 jeux et 2 streamers, et num_clips_per_source=5,
        # vous demanderez 5*3=15 clips de jeux + 5*2=10 clips de streamers = 25 clips au total,
        # parmi lesquels les 10 meilleurs seront sélectionnés.
        get_top_clips(token, num_clips_per_source=10) # Demande jusqu'à 10 clips par source