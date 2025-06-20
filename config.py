# Fichier: config.py
# Description: Configuration robuste pour l'API Gemini, compatible local et déploiement.

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Charge les variables du fichier .env dans l'environnement du système.
# C'est ce qui permet à votre projet de fonctionner en local.
load_dotenv()

# Récupère la clé API.
# os.getenv va d'abord chercher dans les variables d'environnement de Render (en production)
# puis dans celles chargées par load_dotenv() depuis le fichier .env (en local).
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Vérification de sécurité : si la clé n'est pas trouvée, on arrête l'application
# avec une erreur claire.
if not GEMINI_API_KEY:
    # Cette erreur s'affichera sur Render si la variable n'est pas configurée.
    raise ValueError("Clé API Gemini non trouvée. Assurez-vous de l'avoir définie dans votre fichier .env ou dans les variables d'environnement de Render.")

# Configuration du client Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialisation du modèle que vous souhaitez utiliser.
# On garde bien 'gemini-1.5-flash' comme dans votre version.
model = genai.GenerativeModel('gemini-2.0-flash')