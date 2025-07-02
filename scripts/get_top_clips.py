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

# --- FIN DES PARAMÈTRES ---

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

def get_top_clips(access_token, num_clips_per_source=100, days_ago=3):
    """Fetches clips from Twitch, prioritizing by broadcaster list order, then by views."""
    print(f"📊 Récupération de clips Twitch pour les {days_ago} derniers jours, priorité par Broadcaster ID et ensuite par Game ID.")
    
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_ago)
    
    # Dictionnaire pour stocker tous les clips uniques par leur ID
    all_unique_clips = {}
    
    # Première phase: Récupération et stockage des clips par Broadcaster ID
    print("\n--- Phase 1: Récupération par Broadcaster ID (Prioritaire) ---")
    for broadcaster_id in BROADCASTER_IDS:
        print(f"  - Recherche de clips pour le broadcaster_id: {broadcaster_id}")
        params = {
            "first": num_clips_per_source,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views", 
            "broadcaster_id": broadcaster_id,
            "language": "fr"
        }
        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json().get("data", [])
            
            if not clips_data:
                print(f"    ⚠️ Aucune donnée de clip trouvée pour broadcaster_id {broadcaster_id}.")
                continue

            # Ajout des clips à notre collection unique, en filtrant immédiatement par langue et qualité
            for clip in clips_data:
                if clip.get('language') == 'fr' and not clip.get('title', '').startswith('NUMBERz') and float(clip.get('duration', 0.0)) > 0:
                    # Ajoute broadcaster_id au clip pour le tri futur
                    clip_info = {
                        "id": clip.get("id"),
                        "url": clip.get("url"),
                        "embed_url": clip.get("embed_url"),
                        "thumbnail_url": clip.get("thumbnail_url"),
                        "title": clip.get("title"),
                        "viewer_count": clip.get("viewer_count", 0),
                        "broadcaster_name": clip.get("broadcaster_name"),
                        "broadcaster_id": clip.get("broadcaster_id"), # Ajoutez ceci
                        "game_name": clip.get("game_name"),
                        "created_at": clip.get("created_at"),
                        "duration": float(clip.get("duration", 0.0)),
                        "language": clip.get("language")
                    }
                    all_unique_clips[clip['id']] = clip_info
            print(f"    Collecté {len(clips_data)} clips (uniques et pertinents: {len(all_unique_clips)}).")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des clips Twitch pour broadcaster_id {broadcaster_id} : {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"    Contenu de la réponse API Twitch: {e.response.content.decode()}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON pour broadcaster_id {broadcaster_id}: {e}")
            if hasattr(response, 'content') and response.content is not None:
                print(f"    Contenu brut de la réponse: {response.content.decode()}")

    # Deuxième phase: Récupération et stockage des clips par Game ID
    print("\n--- Phase 2: Récupération par Game ID (Complémentaire) ---")
    for game_id in GAME_IDS:
        print(f"  - Recherche de clips pour le game_id: {game_id}")
        params = {
            "first": num_clips_per_source,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "game_id": game_id,
            "language": "fr"
        }
        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json().get("data", [])
            
            if not clips_data:
                print(f"    ⚠️ Aucune donnée de clip trouvée pour game_id {game_id}.")
                continue

            # Ajout des clips à notre collection unique, filtrant immédiatement
            for clip in clips_data:
                if clip.get('language') == 'fr' and not clip.get('title', '').startswith('NUMBERz') and float(clip.get('duration', 0.0)) > 0:
                    # Ajoute broadcaster_id au clip pour le tri futur (même s'il vient d'un game_id)
                    clip_info = {
                        "id": clip.get("id"),
                        "url": clip.get("url"),
                        "embed_url": clip.get("embed_url"),
                        "thumbnail_url": clip.get("thumbnail_url"),
                        "title": clip.get("title"),
                        "viewer_count": clip.get("viewer_count", 0),
                        "broadcaster_name": clip.get("broadcaster_name"),
                        "broadcaster_id": clip.get("broadcaster_id"), # Ajoutez ceci
                        "game_name": clip.get("game_name"),
                        "created_at": clip.get("created_at"),
                        "duration": float(clip.get("duration", 0.0)),
                        "language": clip.get("language")
                    }
                    all_unique_clips[clip['id']] = clip_info
            print(f"    Collecté {len(clips_data)} clips (uniques et pertinents: {len(all_unique_clips)}).")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des clips Twitch pour game_id {game_id} : {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"    Contenu de la réponse API Twitch: {e.response.content.decode()}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON pour game_id {game_id}: {e}")
            if hasattr(response, 'content') and response.content is not None:
                print(f"    Contenu brut de la réponse: {response.content.decode()}")

    # --- Phase 3: Construction de la compilation finale avec l'ordre de priorité souhaité ---
    print("\n--- Phase 3: Construction de la compilation finale (Priorisation par Broadcaster ID) ---")

    final_clips_for_compilation = []
    current_duration_sum = 0.0

    # Créer un pool de clips modifiable pour piocher dedans
    current_clip_pool = list(all_unique_clips.values())
    
    # Liste pour stocker les clips dans l'ordre final désiré
    ordered_clips_for_selection = []

    # 1. Prioriser les clips des broadcasters dans l'ordre de BROADCASTER_IDS
    for priority_broadcaster_id in BROADCASTER_IDS:
        # Filtrer les clips de ce broadcaster
        broadcaster_clips = [
            clip for clip in current_clip_pool 
            if clip.get('broadcaster_id') == priority_broadcaster_id
        ]
        
        # Trier ces clips par vues (le plus populaire de ce streamer d'abord)
        broadcaster_clips_sorted = sorted(broadcaster_clips, key=lambda x: x.get('viewer_count', 0), reverse=True)
        
        # Ajouter les clips triés de ce streamer à la liste ordonnée
        ordered_clips_for_selection.extend(broadcaster_clips_sorted)
        
        # Retirer ces clips du pool pour ne pas les traiter à nouveau
        current_clip_pool = [
            clip for clip in current_clip_pool 
            if clip.get('broadcaster_id') != priority_broadcaster_id
        ]

    # 2. Ajouter les clips restants (ceux des GAME_IDS ou autres broadcasters non listés)
    # Ils seront triés par vues car c'est la seule priorité restante
    remaining_clips_sorted_by_views = sorted(current_clip_pool, key=lambda x: x.get('viewer_count', 0), reverse=True)
    ordered_clips_for_selection.extend(remaining_clips_sorted_by_views)

    # 3. Sélection finale des clips pour atteindre la durée minimale
    for clip in ordered_clips_for_selection:
        clip_duration = clip.get('duration', 0.0)
        
        final_clips_for_compilation.append(clip)
        current_duration_sum += clip_duration
        print(f"  Ajouté : '{clip.get('title', 'N/A')}' par {clip.get('broadcaster_name', 'N/A')} ({clip_duration:.1f}s, Vues: {clip.get('viewer_count', 0)}, Langue: {clip.get('language')}). Durée cumulée: {current_duration_sum:.1f}s")
        
        # Vérifie si la durée minimale est atteinte ET qu'il y a un nombre suffisant de clips (ex: au moins 3)
        if current_duration_sum >= MIN_VIDEO_DURATION_SECONDS and len(final_clips_for_compilation) >= 3: 
            print(f"  ✅ Durée minimale ({MIN_VIDEO_DURATION_SECONDS}s) atteinte avec {len(final_clips_for_compilation)} clips.")
            break 

    if current_duration_sum < MIN_VIDEO_DURATION_SECONDS and final_clips_for_compilation:
        print(f"⚠️ ATTENTION: Impossible d'atteindre la durée minimale de {MIN_VIDEO_DURATION_SECONDS} secondes ({MIN_VIDEO_DURATION_SECONDS / 60:.2f} minutes) avec les clips francophones pertinents disponibles. Durée finale: {current_duration_sum:.1f}s")
    
    if not final_clips_for_compilation:
        print("❌ Aucun clip francophone viable n'a été sélectionné pour la compilation. Le fichier top_clips.json sera vide.")
        sys.exit(0) 

    final_clips = final_clips_for_compilation

    # --- DÉBUGGAGE : Affiche les clips finaux avant de les écrire dans le JSON ---
    print("\n--- CLIPS FINAUX SÉLECTIONNÉS POUR SAUVEGARDE ---")
    if final_clips:
        for i, clip in enumerate(final_clips):
            print(f"{i+1}. Title: {clip.get('title', 'N/A')}, Broadcaster: {clip.get('broadcaster_name', 'N/A')}, Views: {clip.get('viewer_count', 0)}, Duration: {clip.get('duration', 'N/A')}s, Language: {clip.get('language', 'N/A')}, URL: {clip.get('url', 'N/A')}")
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
        get_top_clips(token, num_clips_per_source=100, days_ago=3)