# Fichier: config.py
# Description: Configuration robuste pour l'API Gemini, compatible local et déploiement.

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Variable globale privée pour "cacher" l'instance du modèle
_model = None

def get_model():
    """
    Initialise et retourne le modèle Gemini.
    Utilise un "singleton" pour s'assurer que le modèle n'est initialisé qu'une seule fois.
    """
    global _model
    if _model is None:
        # Charge les variables du fichier .env (pour le local)
        load_dotenv()
        
        # Récupère la clé API depuis l'environnement (fonctionne en local et sur Render)
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        
        if not GEMINI_API_KEY:
            raise ValueError("Clé API Gemini non trouvée. Assurez-vous de l'avoir définie dans votre fichier .env ou dans les variables d'environnement de Render.")
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Le modèle a été mis à jour
        _model = genai.GenerativeModel('gemini-2.0-flash')
        
    return _model
