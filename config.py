# Fichier: config.py
# Description: Version finale et corrigée pour le déploiement sur Render.
# Utilise les variables d'environnement pour la clé API et un nom de modèle valide.

import os
import streamlit as st
import google.generativeai as genai

print("--- [CONFIG.PY] Début du chargement du module de configuration. ---")

# La décoration @st.cache_resource garantit que cette fonction n'est exécutée qu'une seule fois.
@st.cache_resource
def get_model():
    """
    Initialise et retourne le modèle génératif Gemini.
    """
    print("--- [CONFIG.PY] Appel de la fonction get_model() pour initialisation du modèle. ---")
    
    # 1. Récupérer la clé API depuis les variables d'environnement de Render
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    # 2. Vérifier si la clé API a bien été trouvée
    if not gemini_api_key:
        print("--- [CONFIG.PY] ERREUR : Clé API 'GEMINI_API_KEY' non trouvée dans les variables d'environnement. ---")
        st.error("ERREUR DE CONFIGURATION : La clé API de Gemini n'est pas définie.")
        st.info("Le propriétaire de l'application doit configurer la variable d'environnement 'GEMINI_API_KEY' dans les paramètres du service sur Render.")
        st.stop()

    # 3. Configurer l'API et initialiser le modèle
    try:
        print("--- [CONFIG.PY] Clé API trouvée. Configuration de genai... ---")
        genai.configure(api_key=gemini_api_key)
        
        # Utilisation d'un nom de modèle récent et valide.
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        print(f"--- [CONFIG.PY] Modèle '{model.model_name}' initialisé avec succès. ---")
        return model
        
    except Exception as e:
        print(f"--- [CONFIG.PY] ERREUR : Une exception est survenue lors de l'initialisation du modèle : {e} ---")
        st.error(f"Une erreur est survenue lors de la connexion à l'API Gemini.")
        st.exception(e)
        st.stop()
