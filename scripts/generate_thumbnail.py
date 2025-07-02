import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont # Nécessite Pillow
from io import BytesIO

# Chemins des fichiers
INPUT_CLIPS_JSON = os.path.join("data", "top_clips.json")
OUTPUT_THUMBNAIL_PATH = os.path.join("data", "thumbnail.jpg") # Miniature finale
LOGO_PATH = os.path.join("assets", "your_logo.png") # Chemin vers votre logo PNG

# Dimensions de la miniature YouTube standard
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

def download_image(url):
    """Télécharge une image depuis une URL et la retourne sous forme d'objet Image PIL."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB") # Convertir en RGB pour éviter problèmes de mode (RGBA, P, etc.)
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors du téléchargement de l'image {url}: {e}")
        return None
    except IOError as e:
        print(f"❌ Erreur lors de l'ouverture ou du traitement de l'image téléchargée {url}: {e}")
        return None

def generate_thumbnail():
    print("🏞️ Génération de la miniature personnalisée...")

    if not os.path.exists(INPUT_CLIPS_JSON):
        print(f"❌ Erreur: Le fichier '{INPUT_CLIPS_JSON}' est introuvable. Assurez-vous que la récupération des clips a réussi.")
        exit(1)

    with open(INPUT_CLIPS_JSON, "r", encoding="utf-8") as f:
        clips_data = json.load(f)

    if not clips_data:
        print("⚠️ Aucune donnée de clip à traiter. Le fichier top_clips.json est vide. Génération d'une miniature par défaut ou simple.")
        # Crée une miniature noire si pas de clips
        empty_thumbnail = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color = 'black')
        draw = ImageDraw.Draw(empty_thumbnail)
        try:
            # Essayer de charger une police pour le texte
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Chemin générique pour Linux (GitHub Actions)
            if os.path.exists(font_path):
                 font = ImageFont.truetype(font_path, 40)
            else:
                font = ImageFont.load_default()
        except IOError:
            font = ImageFont.load_default()
        text = "Aucun clip trouvé pour aujourd'hui."
        text_width, text_height = draw.textsize(text, font=font)
        draw.text(((THUMBNAIL_WIDTH - text_width) / 2, (THUMBNAIL_HEIGHT - text_height) / 2), text, font=font, fill=(255, 255, 255))
        empty_thumbnail.save(OUTPUT_THUMBNAIL_PATH)
        print(f"✅ Miniature par défaut générée et sauvegardée dans {OUTPUT_THUMBNAIL_PATH}.")
        exit(0) # Sortie propre

    # Récupérer les 4 premières vignettes. S'il n'y en a pas 4, utiliser moins ou des placeh olders.
    thumbnail_urls = [clip.get("thumbnail_url") for clip in clips_data if clip.get("thumbnail_url")][:4]

    if not thumbnail_urls:
        print("⚠️ Aucune URL de vignette trouvée dans les données des clips. Impossible de créer la miniature. Génération d'une miniature noire.")
        empty_thumbnail = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color = 'black')
        empty_thumbnail.save(OUTPUT_THUMBNAIL_PATH)
        print(f"✅ Miniature noire générée et sauvegardée dans {OUTPUT_THUMBNAIL_PATH}.")
        exit(0)

    # Créer l'image finale vide
    final_image = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))

    # Dimensions pour chaque quadrant (2x2 grille)
    quadrant_width = THUMBNAIL_WIDTH // 2
    quadrant_height = THUMBNAIL_HEIGHT // 2

    positions = [
        (0, 0),                       # Top-left
        (quadrant_width, 0),          # Top-right
        (0, quadrant_height),         # Bottom-left
        (quadrant_width, quadrant_height) # Bottom-right
    ]

    downloaded_images = []
    for url in thumbnail_urls:
        img = download_image(url)
        if img:
            downloaded_images.append(img)
        if len(downloaded_images) >= 4: # On a besoin de 4 images max pour les quadrants
            break
    
    # Remplir avec des images noires si moins de 4 images ont été téléchargées
    while len(downloaded_images) < 4:
        downloaded_images.append(Image.new('RGB', (quadrant_width, quadrant_height), color='black'))


    # Coller les images dans les quadrants
    for i, img in enumerate(downloaded_images):
        if i < len(positions): # S'assurer qu'on ne dépasse pas les 4 positions
            # Redimensionner l'image pour qu'elle s'adapte au quadrant
            img = img.resize((quadrant_width, quadrant_height), Image.Resampling.LANCZOS)
            final_image.paste(img, positions[i])

    # --- Superposer le logo au centre ---
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA") # Garder le canal alpha pour la transparence
            # Redimensionner le logo si nécessaire (ex: 30% de la largeur de la miniature)
            logo_max_width = int(THUMBNAIL_WIDTH * 1) # Le logo prend 50% de la largeur max
            logo_max_height = int(THUMBNAIL_HEIGHT * 1) # Le logo prend 50% de la hauteur max
            
            # Calculer le ratio pour redimensionner le logo sans déformer
            logo_ratio = min(logo_max_width / logo.width, logo_max_height / logo.height)
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