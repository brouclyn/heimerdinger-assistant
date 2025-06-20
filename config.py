# Fichier: config.py
# Description: Version de débogage pour le déploiement sur Render.

import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

print("--- [CONFIG.PY] Début du chargement du module de configuration. ---")

# Variable globale privée pour "cacher" l'instance du modèle
_model = None

@st.cache_resource
def get_model():
    """
    Initialise et retourne le modèle Gemini en utilisant une méthode de cache sécurisée.
    """
    print("--- [CONFIG.PY] Appel de la fonction get_model(). ---")
    global _model
    if _model is None:
        print("--- [CONFIG.PY] Le modèle n'est pas encore initialisé. Tentative de configuration. ---")
        
        # Charge les variables du fichier .env (utile pour le développement local)
        load_dotenv()
        print("--- [CONFIG.PY] load_dotenv() a été appelé. ---")
        
        # Récupère la clé API depuis l'environnement
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        
        # Log de débogage pour voir ce que Render trouve
        if GEMINI_API_KEY:
            print(f"--- [CONFIG.PY] Clé API trouvée via os.getenv ! La clé commence par: {GEMINI_API_KEY[:4]}... ---")
        else:
            print("--- [CONFIG.PY] Clé API NON TROUVÉE via os.getenv. Vérifiez la variable d'environnement sur Render. ---")
            raise ValueError("Clé API Gemini non trouvée. Assurez-vous que la variable d'environnement 'GEMINI_API_KEY' est correctement configurée sur Render.")

        print("--- [CONFIG.PY] Configuration de l'API Gemini avec la clé. ---")
        genai.configure(api_key=GEMINI_API_KEY)
        
        _model = genai.GenerativeModel('gemini-2.0-flash')
        print("--- [CONFIG.PY] Modèle Gemini initialisé avec succès. ---")
        
    else:
        print("--- [CONFIG.PY] Le modèle était déjà initialisé. Retour de l'instance existante. ---")
        
    return _model
