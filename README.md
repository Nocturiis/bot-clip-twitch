# 🚀 Twitch Clip Compiler - Générateur Automatique de Compilations YouTube

Ce projet est une solution automatisée pour générer des compilations de clips Twitch populaires et les publier directement sur YouTube. Il est conçu pour les créateurs de contenu, les gestionnaires de communauté ou toute personne souhaitant créer rapidement des "Best Of" de moments Twitch marquants, en se concentrant sur le contenu francophone.

## ✨ Fonctionnalités

  * **Récupération de Clips Intelligente :** Collecte les clips les plus populaires de jeux spécifiques et/ou de streamers Twitch définis.
  * **Modes de Priorisation Avancés :** Configurez la stratégie de sélection des clips :
      * **Priorisation Stricte des Streamers (`PRIORITIZE_BROADCASTERS_STRICTLY = True`) :** Le script privilégie strictement les clips des streamers définis (`BROADCASTER_IDS`) en premier. Il tente d'atteindre la durée vidéo minimale avec ces clips avant d'intégrer des clips de jeux. L'ordre des streamers dans la liste peut influencer la priorité.
      * **Mode Classique (`PRIORITIZE_BROADCASTERS_STRICTLY = False`) :** Tous les clips collectés (streamers et jeux) sont combinés puis triés globalement par nombre de vues (les plus vus en premier), assurant une sélection basée sur la popularité générale.
  * **Limite de Clips par Streamer :** Une limite configurable (`MAX_CLIPS_PER_BROADCASTER_IN_FINAL_COMPILATION`) est appliquée pour assurer une diversité de contenu et éviter qu'un seul streamer ne domine la compilation finale.
  * **Filtrage Robuste :**
      * Filtre les clips par langue (`CLIP_LANGUAGE`, par défaut `fr` pour le français).
      * Exclut les clips de durée nulle ou les titres de clips génériques/de test.
  * **Téléchargement Automatisé :** Télécharge les fichiers vidéo des clips Twitch et extrait la première frame de chaque clip pour une utilisation potentielle en vignette.
  * **Déduplication des Clips :** Le processus de collecte assure que chaque clip n'apparaît qu'une seule fois dans la compilation, même s'il est trouvé via différentes recherches (par jeu et par streamer).
  * **Génération Vidéo :** Assemble les clips téléchargés en une seule vidéo MP4, avec un son uniforme et un potentiel fondu entre les clips.
  * **Génération de Vignettes Personnalisées :** Crée une vignette attrayante pour la vidéo en utilisant la première frame d'un clip sélectionné et un logo personnalisable, le tout sauvegardé sous `data/thumbnail.jpg`.
  * **Mise en Ligne YouTube :** Uploade automatiquement la compilation vidéo sur une chaîne YouTube spécifiée, avec un titre et une description générés dynamiquement et une miniature personnalisée.
  * **Gestion des Métadonnées :** Crée un fichier JSON (`data/video_metadata.json`) avec les détails des clips sélectionnés, ainsi que le titre, la description et les tags de la vidéo finale.
  * **Intégration GitHub Actions :** Conçu pour s'exécuter de manière entièrement automatisée via des workflows GitHub Actions, permettant des compilations régulières sans intervention manuelle.

## 🛠️ Technologies Utilisées

  * **Python 3.x :** Langage de programmation principal.
  * **Twitch API (Helix) :** Pour la récupération des données de clips.
  * **YouTube Data API v3 :** Pour l'upload des vidéos.
  * **`requests` :** Bibliothèque Python pour les requêtes HTTP.
  * **`moviepy` :** Bibliothèque Python pour le montage vidéo (concaténation, ajustement audio).
  * **`Pillow (PIL)` :** Bibliothèque Python pour la manipulation d'images et la génération de vignettes.
  * **`google-auth-oauthlib`, `google-api-python-client` :** Pour l'authentification et l'interaction avec l'API YouTube.
  * **`yt-dlp` :** Outil externe (appelé via `subprocess`) pour le téléchargement robuste des clips Twitch.
  * **GitHub Actions :** Pour l'orchestration et l'automatisation du workflow.

## ⚙️ Configuration Requise

Pour faire fonctionner ce projet, vous aurez besoin de clés d'API et de fichiers de configuration pour Twitch et YouTube.

### 1\. Twitch API

1.  **Créez une application Twitch Developers :**
      * Allez sur le [portail des développeurs Twitch](https://dev.twitch.tv/).
      * Connectez-vous et allez dans **"Applications"**.
      * Cliquez sur **"Enregistrer votre application"** (Register Your Application).
      * Remplissez les champs :
          * **Nom (Name) :** Un nom pour votre application (ex: "Mon Compilateur de Clips").
          * **URL de redirection OAuth (OAuth Redirect URLs) :** `http://localhost:8080` (utilisé pour le script d'authentification YouTube, même s'il n'est pas directement pour Twitch).
          * **Catégorie (Category) :** Choisissez `Application intégrée` ou `Outils`.
      * Cliquez sur **"Créer"**.
2.  **Récupérez les identifiants :**
      * Une fois l'application créée, vous verrez votre **`Client ID`**.
      * Cliquez sur **"Gérer"** (Manage) pour votre application.
      * Sous "Client Secret", cliquez sur **"Nouveau secret"** (New Secret) pour générer votre **`Client Secret`**.
      * **Conservez ces deux valeurs en toute sécurité.**

### 2\. YouTube Data API

1.  **Créez un projet Google Cloud Platform :**
      * Allez sur la [console Google Cloud](https://console.cloud.google.com/).
      * Créez un nouveau projet (ou sélectionnez un projet existant).
2.  **Activez l'API YouTube Data API v3 :**
      * Dans la console GCP, allez dans **"APIs et Services" \> "Bibliothèque"**.
      * Recherchez **"YouTube Data API v3"** et activez-la.
3.  **Créez des identifiants OAuth 2.0 :**
      * Allez dans **"APIs et Services" \> "Identifiants"**.
      * Cliquez sur **"Créer des identifiants" \> "ID client OAuth"**.
      * Choisissez **"Application de bureau"** comme type d'application.
      * Donnez un nom à votre client (ex: "Desktop Client for YouTube Upload").
      * Cliquez sur **"Créer"**.
      * Notez votre **`ID client`** et votre **`Secret client`**.
      * Téléchargez le fichier JSON des identifiants (bouton "Télécharger le client OAuth") et **renommez-le en `client_secrets.json`**. Placez ce fichier à la racine de votre projet.
4.  **Authentification YouTube (première exécution) :**
      * La première fois que vous essaierez d'uploader une vidéo via l'API, le script vous demandera d'autoriser l'application via un navigateur web. Le fichier `token.json` sera créé, stockant les informations d'authentification pour les exécutions futures.

### 3\. GitHub Secrets

Pour des raisons de sécurité, ne codez jamais en dur vos identifiants API dans votre code. Utilisez les secrets GitHub pour les stocker.

1.  Sur votre dépôt GitHub, allez dans **"Settings" \> "Secrets and variables" \> "Actions"**.
2.  Cliquez sur **"New repository secret"** et ajoutez les secrets suivants :
      * `TWITCH_CLIENT_ID` : Votre Client ID Twitch.
      * `TWITCH_CLIENT_SECRET` : Votre Client Secret Twitch.
      * `YOUTUBE_CLIENT_ID` : Votre ID client OAuth de Google.
      * `YOUTUBE_CLIENT_SECRET` : Votre Secret client OAuth de Google.
      * `YOUTUBE_REFRESH_TOKEN`: Ce secret sera ajouté ***après*** la première authentification manuelle (voir section "Configuration du token YouTube pour GitHub Actions").

## 🚀 Utilisation

### 1\. Préparation de l'environnement (Local)

1.  **Cloner le dépôt :**
    ```bash
    git clone https://github.com/votre_utilisateur/votre_repo.git
    cd votre_repo
    ```
2.  **Créer un environnement virtuel (recommandé) :**
    ```bash
    python -m venv venv
    # Sur Windows
    venv\Scripts\activate
    # Sur macOS/Linux
    source venv/bin/activate
    ```
3.  **Installer les dépendances Python :**
    ```bash
    pip install -r requirements.txt
    ```
    (Note : `yt-dlp` sera installé via `requirements.txt`.)

### 2\. Configuration des Listes d'IDs et Paramètres

Les fichiers de configuration clés sont situés dans le dossier `scripts/`.

  * **`scripts/get_top_clips.py` :**
      * **`PRIORITIZE_BROADCASTERS_STRICTLY` :** (True/False) Définissez `True` pour prioriser strictement les streamers, ou `False` pour une sélection globale par vues.
      * **`GAME_IDS` :** Modifiez cette liste avec les IDs des jeux Twitch dont vous souhaitez récupérer les clips.
      * **`BROADCASTER_IDS` :** Modifiez cette liste avec les IDs des streamers Twitch que vous souhaitez inclure. L'ordre de cette liste est important en mode de priorisation stricte.
      * **`MIN_VIDEO_DURATION_SECONDS` :** Ajustez la durée minimale souhaitée pour la compilation vidéo finale (en secondes).
      * **`MAX_CLIPS_PER_BROADCASTER_IN_FINAL_COMPILATION` :** Modifiez cette valeur pour limiter le nombre maximal de clips par streamer dans la compilation finale (par défaut à 3 dans le script).
      * **`CLIP_LANGUAGE` :** (ex: `"fr"`) Code ISO 639-1 pour la langue des clips à récupérer.

*Comment trouver un `BROADCASTER_ID` ou `GAME_ID`?*
Exécutez `python scripts/get_broadcaster_id.py` et suivez les instructions. Il vous demandera un nom d'utilisateur Twitch ou un nom de jeu et affichera son ID.

### 3\. Authentification YouTube pour GitHub Actions (Une fois)

La première authentification YouTube doit être faite manuellement pour obtenir le `refresh_token` qui sera utilisé par GitHub Actions.

1.  Assurez-vous que `client_secrets.json` (téléchargé depuis Google Cloud) est à la racine de votre projet.
2.  **Exécutez `scripts/upload_youtube.py` localement pour la première fois :**
    ```bash
    python scripts/upload_youtube.py
    ```
3.  Cela ouvrira une page dans votre navigateur. Connectez-vous à votre compte Google/YouTube et autorisez l'application.
4.  Une fois autorisé, le script va probablement échouer l'upload (car il n'aura pas encore de clips à uploader) mais il aura créé un fichier `token.json` à la racine de votre projet.
5.  **Ouvrez `token.json`** et copiez la valeur de `refresh_token`.
6.  **Ajoutez ce `refresh_token` comme un secret GitHub** nommé `YOUTUBE_REFRESH_TOKEN` dans les paramètres de votre dépôt GitHub (voir section "GitHub Secrets" ci-dessus).

### 4\. Exécution (Local)

Vous pouvez exécuter les scripts individuellement pour les tests :

1.  **Récupérer et prétraiter les clips :**

    ```bash
    python scripts/get_top_clips.py
    ```

    Cela va générer `data/top_clips.json` et télécharger les clips dans `data/raw_clips/`.

2.  **Télécharger les clips individuels et extraire les frames :**

    ```bash
    python scripts/download_clips.py
    ```

    Cela télécharge les clips sélectionnés dans `data/raw_clips/` et leurs premières frames dans `data/clip_frames/`.

3.  **Compiler la vidéo :**

    ```bash
    python scripts/compile_video.py
    ```

    Cela créera `output/compiled_video.mp4`.

4.  **Générer les métadonnées de la vidéo :**

    ```bash
    python scripts/generate_metadata.py
    ```

    Cela générera le titre, la description et les tags dans `data/video_metadata.json`.

5.  **Générer la miniature personnalisée :**

    ```bash
    python scripts/generate_thumbnail.py
    ```

    Cela créera `data/thumbnail.jpg`.

6.  **Uploader sur YouTube :**

    ```bash
    python scripts/upload_youtube.py
    ```

    Cela utilisera `data/video_metadata.json` pour les informations de la vidéo, `output/compiled_video.mp4` pour le fichier vidéo et `data/thumbnail.jpg` pour la miniature.

### 5\. Exécution (GitHub Actions - Recommandé)

Le projet est configuré pour une automatisation complète via GitHub Actions. Les workflows se trouvent dans le dossier `.github/workflows/`.

  * Le workflow principal (`twitch_daily_clips.yml`) est déclenché par un push sur `main` ou un calendrier (cron job).
  * Il exécutera séquentiellement les étapes pour :
    1.  Cloner le dépôt (`Checkout code`).
    2.  Installer Python et les dépendances.
    3.  Créer les dossiers de travail.
    4.  Récupérer les clips Twitch (`get_top_clips.py`).
    5.  Télécharger les clips et extraire les frames (`download_clips.py`).
    6.  Compiler la vidéo (`compile_video.py`).
    7.  Uploader la vidéo compilée comme artefact (facultatif, pour archivage).
    8.  Générer les métadonnées de la vidéo (`generate_metadata.py`).
    9.  Générer la miniature (`generate_thumbnail.py`).
    10. Uploader sur YouTube (`upload_youtube.py`).
    11. Nettoyer les fichiers temporaires.

**Pour lancer une exécution manuelle sur GitHub Actions :**

1.  Allez dans l'onglet **"Actions"** de votre dépôt GitHub.
2.  Sélectionnez votre workflow (ex: "Twitch Daily Top 10 Clips").
3.  Cliquez sur **"Run workflow"** pour déclencher une exécution manuelle.

### 6\. Configuration du Cron Job

Le workflow est programmé pour s'exécuter automatiquement. Dans votre fichier `.github/workflows/twitch_daily_clips.yml`, la ligne `cron: '0 15 * * *'` signifie que le workflow s'exécutera tous les jours à **15h00 UTC**.

  * Pour **Herve, Wallonia, Belgium** (CEST), cela correspond à **17h00 CEST** (UTC+2 en heure d'été). Ajustez l'heure UTC dans le cron si vous souhaitez une heure d'exécution différente.

## 🗄️ Structure du Projet

```
.
├── .github/                  # Dossier de configuration GitHub Actions
│   └── workflows/
│       └── twitch_daily_clips.yml # Workflow principal pour l'automatisation
├── scripts/                  # Scripts Python du projet
│   ├── get_broadcaster_id.py # Aide à trouver les IDs de streamers/jeux
│   ├── get_top_clips.py      # Récupère et sélectionne les clips de Twitch
│   ├── download_clips.py     # Télécharge les clips et extrait les premières frames
│   ├── compile_video.py      # Compile les clips en une vidéo finale
│   ├── generate_metadata.py  # Génère le titre, la description et les tags de la vidéo
│   ├── generate_thumbnail.py # Génère la miniature personnalisée
│   └── upload_youtube.py     # Uploade la vidéo sur YouTube
├── data/                     # Dossier pour les données temporaires
│   ├── top_clips.json        # Informations sur les clips sélectionnés
│   ├── video_metadata.json   # Métadonnées (titre, description, tags) de la vidéo finale
│   ├── thumbnail.jpg         # La miniature générée pour YouTube
│   ├── raw_clips/            # Sous-dossier pour les fichiers vidéo de clips bruts téléchargés
│   ├── processed_clips/      # Sous-dossier pour les clips traités (audio ajusté, etc.)
│   └── clip_frames/          # Sous-dossier pour les premières frames extraites des clips
├── output/                   # Dossier pour les fichiers de sortie
│   └── compiled_video.mp4    # La vidéo de compilation finale
├── client_secrets.json       # Vos identifiants OAuth YouTube (NE PAS COMMETTRE SUR GIT APRÈS UTILISATION INITIALE !)
├── token.json                # Jeton d'authentification YouTube (GÉNÉRÉ APRÈS LA 1ÈRE AUTH ET NE PAS COMMETTRE SUR GIT !)
├── requirements.txt          # Dépendances Python du projet
└── README.md                 # Ce fichier !
```

## ⚠️ Notes Importantes et Dépannage

  * **Limites d'API :** Soyez conscient des limites de requêtes de l'API Twitch et YouTube. Des requêtes trop fréquentes peuvent entraîner des blocages temporaires.
  * **Limites d'Upload YouTube :** Si vous rencontrez l'erreur "uploadLimitExceeded", cela signifie que votre compte YouTube a atteint sa limite quotidienne d'upload. Vous devrez attendre 24h ou vérifier/augmenter les limites dans votre YouTube Studio (Paramètres \> Chaîne \> Éligibilité des fonctionnalités).
  * **Audio Mixage :** Le script essaie d'unifier le volume des clips. Si le mixage audio n'est pas idéal, des ajustements dans `compile_video.py` peuvent être nécessaires (ex: `clip.set_audio(clip.audio.volumex(0.8))`).
  * **Fichiers temporaires :** Les dossiers `data/` et `output/` peuvent devenir volumineux. Ils sont automatiquement nettoyés à la fin du workflow GitHub Actions.
  * **Fuseau horaire :** Toutes les dates sont gérées en UTC (`timezone.utc`) pour la cohérence avec l'API Twitch.
  * **Sécurité des secrets :** Ne jamais exposer vos clés API directement dans le code ou les commits Git. Utilisez toujours les secrets GitHub.

-----

N'hésitez pas à contribuer, à signaler des problèmes ou à suggérer des améliorations \!
