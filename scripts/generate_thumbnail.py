import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from io import BytesIO
from datetime import datetime

# Chemins des fichiers
INPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")
OUTPUT_THUMBNAIL_PATH = os.path.join("data", "thumbnail.jpg") # Miniature finale
LOGO_PATH = os.path.join("assets", "your_logo.png") # Chemin vers votre logo PNG

# Dimensions de la miniature YouTube standard
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

def get_font(size):
    """Tente de charger une police TrueType ou utilise la police par défaut."""
    # Chemins courants pour les polices sur différents systèmes
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # Linux (souvent sur GitHub Actions)
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",    # macOS
        "C:/Windows/Fonts/arialbd.ttf"                          # Windows
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except IOError:
                continue # Essayer le chemin suivant si la police est corrompue ou illisible
            
    # Si aucune police TrueType n'est trouvée/utilisable, charge la police par défaut de Pillow
    print("⚠️ Aucune police TrueType trouvée. Utilisation de la police par défaut de Pillow.")
    return ImageFont.load_default()

def download_image(url):
    """Télécharge une image depuis une URL et la retourne sous forme d'objet Image PIL."""
    try:
        response = requests.get(url, stream=True, timeout=10) # Ajout d'un timeout
        response.raise_for_status()
        # Lire le contenu une seule fois
        image_content = BytesIO(response.content)
        img = Image.open(image_content).convert("RGB") # Convertir en RGB pour éviter problèmes de mode (RGBA, P, etc.)
        return img
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors du téléchargement de l'image {url}: {e}")
        return None
    except UnidentifiedImageError: # Gère les cas où le fichier n'est pas une image valide
        print(f"❌ Erreur: Le fichier téléchargé depuis {url} n'est pas une image valide ou est corrompu.")
        return None
    except IOError as e:
        print(f"❌ Erreur lors de l'ouverture ou du traitement de l'image téléchargée {url}: {e}")
        return None

def generate_thumbnail():
    print("🏞️ Démarrage de la génération de la miniature personnalisée...")

    # Assurez-vous que le dossier 'data' existe pour la miniature finale
    data_dir = os.path.dirname(OUTPUT_THUMBNAIL_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Dossier de données créé : {data_dir}")

    if not os.path.exists(INPUT_CLIPS_JSON):
        print(f"❌ Erreur: Le fichier '{INPUT_CLIPS_JSON}' est introuvable. Assurez-vous que la récupération des clips a réussi.")
        # Générer une miniature par défaut si le fichier source est manquant
        generate_default_thumbnail("Fichier de clips introuvable.")
        return # Ne pas utiliser sys.exit(1) ici pour permettre au workflow de continuer

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips_data = json.load(f)

    # Récupérer la date actuelle pour la miniature par défaut
    today_date = datetime.now()
    date_str = today_date.strftime("%d/%m/%Y")

    if not clips_data:
        print("⚠️ Aucune donnée de clip à traiter. Le fichier top_clips.json est vide. Génération d'une miniature par défaut.")
        generate_default_thumbnail(f"Aucun clip trouvé pour aujourd'hui ({date_str}).")
        return # Ne pas utiliser sys.exit(0) ici

    # Sélectionner les 4 premières vignettes uniques pour éviter les doublons
    selected_thumbnail_urls = []
    seen_urls = set()
    for clip in clips_data:
        url = clip.get("thumbnail_url")
        # Twitch thumbnails often have a resolution string like "-{width}x{height}.jpg"
        # We can try to get a higher resolution version if available, or remove it for the base image
        if url:
            # Remove resolution suffix to get a more generic URL, then try to replace with a larger one
            # Example: https://clips-media-assets2.twitch.tv/AT-cm%7C123456789-preview-480x272.jpg
            # becomes https://clips-media-assets2.twitch.tv/AT-cm%7C123456789-preview.jpg
            base_url = url.split('-preview-')[0] + '-preview.jpg' # Simplified approach
            # Or, for higher quality, try to replace the size part
            high_res_url = url.replace("-480x272.jpg", "-1280x720.jpg") # Assuming this is a common pattern

            if high_res_url not in seen_urls: # Prioritize high-res if it's different
                selected_thumbnail_urls.append(high_res_url)
                seen_urls.add(high_res_url)
            elif base_url not in seen_urls: # Fallback to base if high-res is same or not found
                selected_thumbnail_urls.append(base_url)
                seen_urls.add(base_url)
        
        if len(selected_thumbnail_urls) >= 4:
            break

    if not selected_thumbnail_urls:
        print("⚠️ Aucune URL de vignette valide trouvée dans les données des clips. Impossible de créer la miniature basée sur les clips. Génération d'une miniature par défaut.")
        generate_default_thumbnail(f"Aucune vignette disponible ({date_str}).")
        return # Ne pas utiliser sys.exit(0) ici

    # Créer l'image finale vide
    final_image = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color=(0, 0, 0)) # Initialiser avec du noir pour les zones non remplies

    # Dimensions pour chaque quadrant (2x2 grille)
    quadrant_width = THUMBNAIL_WIDTH // 2
    quadrant_height = THUMBNAIL_HEIGHT // 2

    positions = [
        (0, 0),                                # Top-left
        (quadrant_width, 0),                   # Top-right
        (0, quadrant_height),                  # Bottom-left
        (quadrant_width, quadrant_height)      # Bottom-right
    ]

    downloaded_images = []
    for url in selected_thumbnail_urls: # Utilise la liste filtrée
        img = download_image(url)
        if img:
            downloaded_images.append(img)
        else:
            print(f"  ❌ Échec du téléchargement de la vignette : {url}. Remplacement par une image noire.")
            downloaded_images.append(Image.new('RGB', (quadrant_width, quadrant_height), color='black')) # Ajoute une image noire en cas d'échec

    # S'assurer qu'il y a exactement 4 images (remplir avec du noir si moins de 4 ont été téléchargées/récupérées)
    while len(downloaded_images) < 4:
        downloaded_images.append(Image.new('RGB', (quadrant_width, quadrant_height), color='black'))

    # Coller les images dans les quadrants
    for i, img in enumerate(downloaded_images):
        if i < len(positions):
            # Redimensionner l'image pour qu'elle s'adapte au quadrant
            img = img.resize((quadrant_width, quadrant_height), Image.Resampling.LANCZOS)
            final_image.paste(img, positions[i])

    # --- Superposer le logo au centre ---
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA") # Garder le canal alpha pour la transparence
            
            # NE PAS REDIMENSIONNER LE LOGO ICI - Utiliser sa taille d'origine
            # target_logo_width = int(THUMBNAIL_WIDTH * 0.4) # Ancien code de redimensionnement
            # target_logo_height = int(THUMBNAIL_HEIGHT * 0.4)
            # logo_ratio = min(target_logo_width / logo.width, target_logo_height / logo.height)
            # new_logo_size = (int(logo.width * logo_ratio), int(logo.height * logo_ratio))
            # logo = logo.resize(new_logo_size, Image.Resampling.LANCZOS)

            # Calculer la position centrale du logo avec sa taille d'origine
            logo_x = (THUMBNAIL_WIDTH - logo.width) // 2
            logo_y = (THUMBNAIL_HEIGHT - logo.height) // 2
            
            # Superposer le logo (handle alpha for transparency)
            final_image.paste(logo, (logo_x, logo_y), logo) # Le 3ème argument 'logo' est le masque alpha
            print("✅ Logo superposé.")
        except Exception as e:
            print(f"❌ Erreur lors de la superposition du logo : {e}")
    else:
        print(f"⚠️ Fichier logo introuvable à {LOGO_PATH}. La miniature sera générée sans logo.")

    # Sauvegarder la miniature finale
    try:
        final_image.save(OUTPUT_THUMBNAIL_PATH)
        print(f"✅ Miniature générée et sauvegardée avec succès dans {OUTPUT_THUMBNAIL_PATH}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de la miniature finale : {e}")

def generate_default_thumbnail(message):
    """Génère une miniature par défaut avec un message."""
    print(f"Génération d'une miniature par défaut : {message}")
    default_thumbnail = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color = 'black')
    draw = ImageDraw.Draw(default_thumbnail)
    
    font = get_font(40)
    # Utiliser textbbox pour un calcul de taille plus précis avec Pillow 9.0+
    bbox = draw.textbbox((0, 0), message, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    draw.text(((THUMBNAIL_WIDTH - text_width) / 2, (THUMBNAIL_HEIGHT - text_height) / 2), message, font=font, fill=(255, 255, 255))
    
    try:
        default_thumbnail.save(OUTPUT_THUMBNAIL_PATH)
        print(f"✅ Miniature par défaut générée et sauvegardée dans {OUTPUT_THUMBNAIL_PATH}.")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de la miniature par défaut : {e}")


if __name__ == "__main__":
    generate_thumbnail()