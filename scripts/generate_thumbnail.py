import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError # Nécessite Pillow
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
        "C:/Windows/Fonts/arialbd.ttf"                         # Windows
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
    print("🏞️ Génération de la miniature personnalisée...")

    # Assurez-vous que le dossier 'output' existe si OUTPUT_THUMBNAIL_PATH le contient
    output_dir = os.path.dirname(OUTPUT_THUMBNAIL_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Dossier de sortie créé : {output_dir}")

    if not os.path.exists(INPUT_CLIPS_JSON):
        print(f"❌ Erreur: Le fichier '{INPUT_CLIPS_JSON}' est introuvable. Assurez-vous que la récupération des clips a réussi.")
        exit(1)

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips_data = json.load(f)

    # Récupérer la date actuelle pour la miniature par défaut
    today_date = datetime.now()
    date_str = today_date.strftime("%d/%m/%Y")

    if not clips_data:
        print("⚠️ Aucune donnée de clip à traiter. Le fichier top_clips.json est vide. Génération d'une miniature par défaut.")
        empty_thumbnail = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color = 'black')
        draw = ImageDraw.Draw(empty_thumbnail)
        
        font = get_font(40)
        text = f"Aucun clip trouvé pour aujourd'hui ({date_str})."
        # Utiliser textbbox pour un calcul de taille plus précis avec Pillow 9.0+
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        draw.text(((THUMBNAIL_WIDTH - text_width) / 2, (THUMBNAIL_HEIGHT - text_height) / 2), text, font=font, fill=(255, 255, 255))
        empty_thumbnail.save(OUTPUT_THUMBNAIL_PATH)
        print(f"✅ Miniature par défaut générée et sauvegardée dans {OUTPUT_THUMBNAIL_PATH}.")
        exit(0) # Sortie propre si aucun clip n'est trouvé

    # Sélectionner les 4 premières vignettes uniques pour éviter les doublons
    # Utiliser un set pour suivre les URLs déjà ajoutées
    selected_thumbnail_urls = []
    seen_urls = set()
    for clip in clips_data:
        url = clip.get("thumbnail_url")
        if url and url not in seen_urls:
            selected_thumbnail_urls.append(url)
            seen_urls.add(url)
        if len(selected_thumbnail_urls) >= 4:
            break

    if not selected_thumbnail_urls:
        print("⚠️ Aucune URL de vignette valide trouvée dans les données des clips. Impossible de créer la miniature. Génération d'une miniature noire.")
        empty_thumbnail = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color = 'black')
        draw = ImageDraw.Draw(empty_thumbnail)
        font = get_font(40)
        text = f"Aucune vignette disponible ({date_str})."
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(((THUMBNAIL_WIDTH - text_width) / 2, (THUMBNAIL_HEIGHT - text_height) / 2), text, font=font, fill=(255, 255, 255))
        empty_thumbnail.save(OUTPUT_THUMBNAIL_PATH)
        print(f"✅ Miniature noire générée et sauvegardée dans {OUTPUT_THUMBNAIL_PATH}.")
        exit(0)

    # Créer l'image finale vide
    final_image = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color=(0, 0, 0)) # Initialiser avec du noir pour les zones non remplies

    # Dimensions pour chaque quadrant (2x2 grille)
    quadrant_width = THUMBNAIL_WIDTH // 2
    quadrant_height = THUMBNAIL_HEIGHT // 2

    positions = [
        (0, 0),                            # Top-left
        (quadrant_width, 0),               # Top-right
        (0, quadrant_height),              # Bottom-left
        (quadrant_width, quadrant_height)  # Bottom-right
    ]

    downloaded_images = []
    for url in selected_thumbnail_urls: # Utilise la liste filtrée
        img = download_image(url)
        if img:
            downloaded_images.append(img)
    
    # Remplir avec des images noires si moins de 4 images ont été téléchargées
    while len(downloaded_images) < 4:
        # Créer une image noire de la taille du quadrant pour combler
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
            
            # Redimensionner le logo pour qu'il ne dépasse pas une certaine proportion
            # Par exemple, le logo ne devrait pas être plus large que 40% de la largeur de la miniature
            # et pas plus haut que 40% de la hauteur de la miniature. Ajustez selon le design.
            target_logo_width = int(THUMBNAIL_WIDTH * 1) 
            target_logo_height = int(THUMBNAIL_HEIGHT * 1)
            
            # Calculer le ratio pour redimensionner le logo sans déformer
            logo_ratio = min(target_logo_width / logo.width, target_logo_height / logo.height)
            new_logo_size = (int(logo.width * logo_ratio), int(logo.height * logo_ratio))
            logo = logo.resize(new_logo_size, Image.Resampling.LANCZOS)

            # Calculer la position centrale du logo
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
    final_image.save(OUTPUT_THUMBNAIL_PATH)
    print(f"✅ Miniature générée et sauvegardée dans {OUTPUT_THUMBNAIL_PATH}")

if __name__ == "__main__":
    generate_thumbnail()