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

# --- PARAMÈTRES DE FILTRAGE ET DE SÉLECTION ---

# Liste des IDs de jeux pour lesquels vous voulez récupérer des clips.
# Vous pouvez trouver les IDs de jeux en utilisant l'API Twitch "helix/games?name=NomDuJeu".
GAME_IDS = [
    "509670",       # Just Chatting
    "21779",        # League of Legends
    "32982",        # Grand Theft Auto V
    "512965",       # VALORANT
    "518018",       # Minecraft
    "513143",       # Fortnite
    "32399",        # Counter-Strike
    "511224",       # Apex Legends
    "506520",       # Dota 2
    "490422",       # Dead by Daylight
    "514873",       # Call of Duty: Warzone
    "65768",        # Rocket League
    "518883",       # EA Sports FC 24
    "180025139",    # Mario Kart 8 Deluxe
    "280721",       # Teamfight Tactics
    "488427",       # World of Warcraft
    "1467408070",   # Rust
    "32213",        # Hearthstone
    "138585",       # Chess
    "493306",       # Overwatch 2
    "509660",       # Special Events
    "1063683693",   # Pokémon Scarlet and Violet
    "1678120671",   # Baldur's Gate 3
    "27471",        # osu!
    "507316",       # Phasmophobia
    "19326",        # The Elder Scrolls V: Skyrim
    "512710",       # Fall Guys
    "1285324545",   # Lethal Company
    # Ajoutez d'autres IDs si nécessaire
]

# Liste des IDs de streamers francophones populaires.
# Les clips seront prioritaires selon l'ordre de cette liste.
# Pour trouver l'ID d'un streamer, utilisez le script get_broadcaster_id.py.
BROADCASTER_IDS = [
    "737048563", # Anyme023"
    "52130765",     # Squeezie (chaîne principale)
    "22245231",     # SqueezieLive (sa chaîne secondaire pour le live)
    "41719107",     # ZeratoR
    "24147592",     # Gotaga
    "134966333",    # Kameto
    "737048563",    # AmineMaTue (était Anyme023, même ID)
    "496105401",    # byilhann
    "887001013",    # Nico_la
    "60256640",     # Flamby
    "253195796",    # helydia
    "80716629",     # Inoxtag
    "175560856",    # Hctuan
    "57404419",     # Ponce
    "38038890",     # Antoine Daniel
    "48480373",     # MisterMV
    "19075728",     # Sardoche
    "54546583",     # Locklear
    "50290500",     # Domingo
    "57402636",     # RebeuDeter
    "47565457",     # Joyca
    "153066440",    # Michou
    "31429949",     # LeBouseuh
    "46296316",     # Maghla
    "49896798",     # Chowh1
    "49749557",     # Jiraya
    "53696803",     # Wankil Studio (Laink et Terracid - chaîne principale)
    "72366922",   # Laink (ID individuel, généralement couvert par Wankil Studio)
    "129845722",  # Terracid (ID individuel, généralement couvert par Wankil Studio)
    "51950294",     # Mynthos
    "53140510",     # Etoiles
    "134812328",    # LittleBigWhale
    "180237751",    # Mister V (l'artiste/youtubeur, différent de MisterMV)
    "55787682",     # Shaunz
    "142436402",    # Ultia
    "20875990",     # LCK_France (pour les clips de la ligue de LoL française)
    # Note sur "31289086": La chaîne "WankilStudio" (sans espace) avec cet ID existe,
    # mais "53696803" (Wankil Studio, avec espace) est généralement la plus active pour les clips.
    # Vérifiez laquelle est la plus pertinente pour vous. J'ai gardé la plus courante.
    # ... ajoutez d'autres IDs vérifiés ici ...
]

# PARAMÈTRE POUR LA DURÉE CUMULÉE MINIMALE DE LA VIDÉO FINALE
MIN_VIDEO_DURATION_SECONDS = 630 # 10 minutes et 30 secondes (10*60 + 30)

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

# Augmentez num_clips_per_source pour avoir plus de clips à trier pour la durée minimale
def get_top_clips(access_token, num_clips_per_source=50, days_ago=1): 
    """Fetches the top N clips from Twitch for the last X days for specified games and broadcasters."""
    print(f"📊 Récupération d'un maximum de {num_clips_per_source} clips Twitch par source (jeu/streamer) pour les dernières {days_ago} jours...")
    
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_ago)
    
    all_top_clips = []

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
        
        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json()
            
            if not clips_data.get("data"):
                print(f"  ⚠️ Aucune donnée de clip trouvée pour game_id {game_id} dans la période spécifiée.")
                continue

            for clip in clips_data.get("data", []):
                all_top_clips.append({
                    "id": clip.get("id"),
                    "url": clip.get("url"),
                    "embed_url": clip.get("embed_url"),
                    "thumbnail_url": clip.get("thumbnail_url"),
                    "title": clip.get("title"),
                    "viewer_count": clip.get("viewer_count", 0), # Default to 0 if not present
                    "broadcaster_name": clip.get("broadcaster_name"),
                    "game_name": clip.get("game_name"),
                    "created_at": clip.get("created_at"),
                    "duration": float(clip.get("duration", 0.0)) # <-- AJOUTÉ: Assurez-vous que 'duration' est récupéré et converti en float
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
            "broadcaster_id": broadcaster_id
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
                    "created_at": clip.get("created_at"),
                    "duration": float(clip.get("duration", 0.0)) # <-- AJOUTÉ: Assurez-vous que 'duration' est récupéré et converti en float
                })
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des clips Twitch pour broadcaster_id {broadcaster_id} : {e}")
            if response.content:
                print(f"    Contenu de la réponse API Twitch: {response.content.decode()}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON pour broadcaster_id {broadcaster_id}: {e}")
            if response.content:
                print(f"    Contenu brut de la réponse: {response.content.decode()}")

    # --- NOUVELLE LOGIQUE DE SÉLECTION BASÉE SUR LA DURÉE ET LES VUES ---

    # Tri global de tous les clips collectés par viewer_count (descendant)
    sorted_clips_by_views = sorted(all_top_clips, key=lambda x: x.get('viewer_count', 0), reverse=True)

    final_clips_for_compilation = []
    current_duration_sum = 0.0 # Utilisez un float pour la somme des durées

    print(f"\nSélection des clips pour atteindre au minimum {MIN_VIDEO_DURATION_SECONDS} secondes ({MIN_VIDEO_DURATION_SECONDS / 60:.2f} minutes)...")

    # Parcourt les clips du plus vu au moins vu
    for clip in sorted_clips_by_views:
        clip_duration = float(clip.get('duration', 0.0)) # Assurez-vous que c'est un float
        
        # N'ajoutez que des clips qui ont une durée positive
        if clip_duration > 0: 
            final_clips_for_compilation.append(clip)
            current_duration_sum += clip_duration
            print(f"  Ajouté : '{clip.get('title', 'N/A')}' ({clip_duration:.1f}s, Vues: {clip.get('viewer_count', 0)}). Durée cumulée: {current_duration_sum:.1f}s")
            
            # Vérifie si la durée minimale est atteinte ET qu'il y a un nombre suffisant de clips (ex: au moins 3)
            # pour éviter une compilation d'un seul long clip si le premier suffit.
            if current_duration_sum >= MIN_VIDEO_DURATION_SECONDS and len(final_clips_for_compilation) >= 3: 
                print(f"  ✅ Durée minimale ({MIN_VIDEO_DURATION_SECONDS}s) atteinte avec {len(final_clips_for_compilation)} clips.")
                break # Arrêtez d'ajouter des clips une fois la durée minimale atteinte

    # Si la durée minimale n'est pas atteinte avec tous les clips disponibles, 
    # mais qu'il y a quand même des clips à compiler.
    if current_duration_sum < MIN_VIDEO_DURATION_SECONDS and final_clips_for_compilation:
        print(f"⚠️ ATTENTION: Impossible d'atteindre la durée minimale de {MIN_VIDEO_DURATION_SECONDS} secondes ({MIN_VIDEO_DURATION_SECONDS / 60:.2f} minutes) avec les clips disponibles. Durée finale: {current_duration_sum:.1f}s")
    
    # Cas où aucun clip n'a été sélectionné (par exemple, tous ont une durée de 0, ou aucun n'a été trouvé)
    if not final_clips_for_compilation:
        print("⚠️ Aucun clip viable n'a été sélectionné pour la compilation (peut-être tous avec durée 0, ou aucun trouvé). Le fichier top_clips.json sera vide.")
        sys.exit(0) # Sortie normale si aucun clip n'est sélectionnable

    # La liste finale de clips à sauvegarder est celle qui respecte la durée minimale (ou tous les clips valides trouvés)
    final_clips = final_clips_for_compilation

    # --- DÉBUGGAGE : Affiche les clips finaux avant de les écrire dans le JSON ---
    print("\n--- CLIPS FINAUX SÉLECTIONNÉS POUR SAUVEGARDE ---")
    if final_clips:
        for i, clip in enumerate(final_clips):
            print(f"{i+1}. Title: {clip.get('title', 'N/A')}, Broadcaster: {clip.get('broadcaster_name', 'N/A')}, Views: {clip.get('viewer_count', 0)}, Duration: {clip.get('duration', 'N/A')}s, URL: {clip.get('url', 'N/A')}")
    else:
        print("Aucun clip à sauvegarder.")
    print("--------------------------------------------------\n")
        
    with open(OUTPUT_CLIPS_JSON, "w", encoding="utf-8") as f:
        json.dump(final_clips, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(final_clips)} clips récupérés et sauvegardés dans {OUTPUT_CLIPS_JSON} pour une durée totale de {current_duration_sum:.1f} secondes.")
    return final_clips

if __name__ == "__main__":
    token = get_twitch_access_token()
    if token:
        # num_clips_per_source: Le nombre de clips à demander par requête pour chaque jeu/streamer.
        # Augmentez ce nombre si vous n'atteignez pas la durée minimale avec votre sélection actuelle de IDs.
        get_top_clips(token, num_clips_per_source=50)