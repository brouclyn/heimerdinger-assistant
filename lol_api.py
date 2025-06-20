# Fichier : lol_api.py
# Description : Ajout de la récupération des sorts d'invocateur.

import streamlit as st
import requests

@st.cache_data(ttl=86400)
def get_latest_version():
    try:
        response = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
        response.raise_for_status()
        return response.json()[0]
    except requests.RequestException:
        return "14.12.1" 

@st.cache_data(ttl=86400)
def get_all_champions_list():
    version = get_latest_version()
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR/champion.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['data']
    except requests.RequestException:
        return None

@st.cache_data(ttl=86400)
def get_all_items_data():
    version = get_latest_version()
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR/item.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['data']
    except requests.RequestException:
        st.error("Impossible de charger les données des objets depuis l'API de Riot.")
        return None

# --- NOUVELLE FONCTION ---
@st.cache_data(ttl=86400)
def get_all_summoner_spells_data():
    """Récupère les données de tous les sorts d'invocateur."""
    version = get_latest_version()
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR/summoner.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['data']
    except requests.RequestException:
        st.error("Impossible de charger les données des sorts d'invocateur.")
        return None