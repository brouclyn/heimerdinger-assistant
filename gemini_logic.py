# Fichier: config.py
# Description: Configuration pour le déploiement sur Render.

import os
import streamlit as st
import google.generativeai as genai

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
        
        # Sur Render, les variables d'environnement sont chargées automatiquement.
        # load_dotenv() n'est pas nécessaire ici.
        
        # Récupère la clé API depuis l'environnement
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        
        # Log de débogage pour voir ce que Render trouve
        if GEMINI_API_KEY:
            print(f"--- [CONFIG.PY] Clé API trouvée via os.getenv ! ---")
        else:
            print("--- [CONFIG.PY] Clé API NON TROUVÉE via os.getenv. Vérifiez la variable d'environnement sur Render. ---")
            # Cette erreur s'affichera dans les logs de Render si la variable n'est pas définie.
            st.error("La clé API Gemini n'est pas configurée. Le propriétaire de l'application doit la définir dans les variables d'environnement sur Render.")
            st.stop() # Arrête l'exécution de l'application proprement

        print("--- [CONFIG.PY] Configuration de l'API Gemini avec la clé. ---")
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            _model = genai.GenerativeModel('gemini-pro') # 'gemini-2.0-flash' n'est peut-être pas un nom de modèle valide, 'gemini-pro' est plus courant.
            print("--- [CONFIG.PY] Modèle Gemini initialisé avec succès. ---")
        except Exception as e:
            st.error(f"Une erreur est survenue lors de la configuration de Gemini : {e}")
            st.stop()
            
    else:
        print("--- [CONFIG.PY] Le modèle était déjà initialisé. Retour de l'instance existante. ---")
        
    return _model
