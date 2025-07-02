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
# Exemples d'IDs de jeux populaires :
#   "509670": "Just Chatting" (Très général, souvent en français)
#   "32982": "Grand Theft Auto V"
#   "512965": "Valorant"
#   "21779": "League of of Legends"
# Ajoutez d'autres IDs de jeux si vous le souhaitez.
GAME_IDS = ["509670", "32982", "512965", "21779"] # Exemples, à ajuster

# Liste des IDs de streamers francophones populaires.
# C'est le MEILLEUR moyen de cibler le contenu francophone.
# Pour trouver l'ID d'un streamer, utilisez le script get_broadcaster_id.py.
BROADCASTER_IDS = [
    "52130765",  # Squeezie
    "41719107",  # ZeratoR
    "24147592",  # Gotaga
    "134966333", # Kameto
    "737048563", # Anyme023
    "496105401", # byilhann
    "887001013", # Nico_la
    "60256640",  # Flamby
    "253195796", # helydia
    "80716629",  # Inoxtag
    "175560856"  # Hctuan
    # Ajoutez d'autres IDs de streamers francophones ici
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

def get_top_clips(access_token, num_clips_per_source=50, days_ago=3): # Augmenté days_ago à 3 par défaut pour plus de chances
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
            "game_id": game_id,
            "language": "fr" # <-- AJOUT CLÉ ICI POUR FILTRER PAR LANGUE
        }
        
        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json()
            
            if not clips_data.get("data"):
                print(f"  ⚠️ Aucune donnée de clip trouvée pour game_id {game_id} dans la période spécifiée.")
                continue

            for clip in clips_data.get("data", []):
                # Ajout d'une vérification explicite de la langue au cas où l'API renverrait des choses non "fr"
                if clip.get('language') == 'fr':
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
                        "duration": float(clip.get("duration", 0.0)),
                        "language": clip.get("language") # Garder la langue pour le débogage/vérification
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
            "broadcaster_id": broadcaster_id,
            "language": "fr" # <-- AJOUT CLÉ ICI POUR FILTRER PAR LANGUE
        }

        try:
            response = requests.get(TWITCH_API_URL, headers=headers, params=params)
            response.raise_for_status()
            clips_data = response.json()

            if not clips_data.get("data"):
                print(f"  ⚠️ Aucune donnée de clip trouvée pour broadcaster_id {broadcaster_id} dans la période spécifiée.")
                continue

            for clip in clips_data.get("data", []):
                # Ajout d'une vérification explicite de la langue au cas où l'API renverrait des choses non "fr"
                if clip.get('language') == 'fr':
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
                        "duration": float(clip.get("duration", 0.0)),
                        "language": clip.get("language") # Garder la langue pour le débogage/vérification
                    })
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des clips Twitch pour broadcaster_id {broadcaster_id} : {e}")
            if response.content:
                print(f"    Contenu de la réponse API Twitch: {response.content.decode()}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON pour broadcaster_id {broadcaster_id}: {e}")
            if response.content:
                print(f"    Contenu brut de la réponse: {response.content.decode()}")

    # Filtrer les doublons (par ID de clip)
    unique_clips = {clip['id']: clip for clip in all_top_clips}.values()
    # Trier globalement tous les clips collectés par viewer_count (descendant)
    sorted_clips_by_views = sorted(list(unique_clips), key=lambda x: x.get('viewer_count', 0), reverse=True)

    final_clips_for_compilation = []
    current_duration_sum = 0.0 # Utilisez un float pour la somme des durées

    print(f"\nSélection des clips pour atteindre au minimum {MIN_VIDEO_DURATION_SECONDS} secondes ({MIN_VIDEO_DURATION_SECONDS / 60:.2f} minutes)...")

    # Parcourt les clips du plus vu au moins vu
    for clip in sorted_clips_by_views:
        clip_duration = float(clip.get('duration', 0.0))
        
        # Filtres supplémentaires pour la qualité du clip et la langue (même si déjà demandé à l'API)
        # Exclure les clips avec des titres génériques/de test ("NUMBERz") et s'assurer que la durée est positive
        if clip_duration > 0 and clip.get('language') == 'fr' and not clip.get('title', '').startswith('NUMBERz'):
            final_clips_for_compilation.append(clip)
            current_duration_sum += clip_duration
            print(f"  Ajouté : '{clip.get('title', 'N/A')}' par {clip.get('broadcaster_name', 'N/A')} ({clip_duration:.1f}s, Vues: {clip.get('viewer_count', 0)}, Langue: {clip.get('language')}). Durée cumulée: {current_duration_sum:.1f}s")
            
            # Vérifie si la durée minimale est atteinte ET qu'il y a un nombre suffisant de clips (ex: au moins 3)
            # pour éviter une compilation d'un seul long clip si le premier suffit.
            if current_duration_sum >= MIN_VIDEO_DURATION_SECONDS and len(final_clips_for_compilation) >= 3: 
                print(f"  ✅ Durée minimale ({MIN_VIDEO_DURATION_SECONDS}s) atteinte avec {len(final_clips_for_compilation)} clips.")
                break # Arrêtez d'ajouter des clips une fois la durée minimale atteinte

    # Si la durée minimale n'est pas atteinte avec tous les clips disponibles,
    # mais qu'il y a quand même des clips à compiler, on peut décider de prendre tous les clips valides trouvés.
    if current_duration_sum < MIN_VIDEO_DURATION_SECONDS and final_clips_for_compilation:
        print(f"⚠️ ATTENTION: Impossible d'atteindre la durée minimale de {MIN_VIDEO_DURATION_SECONDS} secondes ({MIN_VIDEO_DURATION_SECONDS / 60:.2f} minutes) avec les clips francophones pertinents disponibles. Durée finale: {current_duration_sum:.1f}s")
    
    # Cas où aucun clip francophone viable n'a été sélectionné
    if not final_clips_for_compilation:
        print("❌ Aucun clip francophone viable n'a été sélectionné pour la compilation. Le fichier top_clips.json sera vide.")
        sys.exit(0) # Sortie normale si aucun clip n'est sélectionnable

    # La liste finale de clips à sauvegarder est celle qui respecte la durée minimale (ou tous les clips valides trouvés)
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
        # num_clips_per_source: Le nombre de clips à demander par requête pour chaque jeu/streamer.
        # Augmentez ce nombre si vous n'atteignez pas la durée minimale avec votre sélection actuelle de IDs.
        # days_ago: Définit sur combien de jours en arrière rechercher les clips. Augmentez si le volume est faible.
        get_top_clips(token, num_clips_per_source=100, days_ago=3) # Recommandé: 100 clips par source, 3 jours