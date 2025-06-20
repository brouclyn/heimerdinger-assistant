# Fichier : app.py
# Description : Correction de l'alerte de dépréciation pour st.image.
print("--- DÉMARRAGE DE L'APPLICATION V4 ---")

import streamlit as st
import random
import time
from config import get_model

# --- Imports depuis les autres fichiers ---
from gemini_logic import call_gemini_with_tools, get_champion_data, generate_ultimate_bravery_challenge, get_draft_suggestion
from lol_api import get_all_champions_list
from rag_handler import create_vector_store, query_rag_system
from pdf_generator import generate_pdf_from_content

# --- Fonction pour charger notre CSS personnalisé ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Erreur: Le fichier de style '{file_name}' est introuvable.")

# --- CONSTANTES ET CONFIGURATION ---
ASSISTANT_MODES = ["Général", "Lore", "Stratégie", "Création RP"]
RAG_KEYWORDS = ["patch", "changement", "stratégie", "guide", "équilibrage", "dernier", "lore", "histoire", "relation"]
st.set_page_config(page_title="Heimerdinger Assistant", page_icon="🧠", layout="wide")
local_css("style.css")

# --- Initialisation du modèle ---
model = get_model()

# --- Le Mini-Jeu d'Entraînement au Smite ---
def display_smite_minigame():
    """Affiche et gère la logique du mini-jeu de timing de Smite."""
    st.header("Entraînement au Châtiment", anchor=False)

    TOTAL_HEALTH = 5000
    SMITE_DAMAGE = 900

    if 'game_state' not in st.session_state or st.session_state.get('game_type') != 'smite':
        st.session_state.game_state = "stopped"
        st.session_state.game_type = 'smite'
        st.session_state.result_message = ""
        st.session_state.game_current_health = TOTAL_HEALTH
        st.session_state.last_frame_time = 0
        st.session_state.current_dps = 0
        st.session_state.time_for_next_dps_change = 0

    baron_svg = """
    <svg width="100" height="100" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM16.5 16.5C16.5 17.33 15.83 18 15 18H9C8.17 18 7.5 17.33 7.5 16.5V15H16.5V16.5ZM16.5 13.5H7.5V12C7.5 10.07 9.07 8.5 11 8.5H13C14.93 8.5 16.5 10.07 16.5 12V13.5ZM11 11.5C10.45 11.5 10 11.05 10 10.5C10 9.95 10.45 9.5 11 9.5C11.55 9.5 12 9.95 12 10.5C12 11.05 11.55 11.5 11 11.5ZM13 11.5C12.45 11.5 12 11.05 12 10.5C12 9.95 12.45 9.5 13 9.5C13.55 9.5 14 9.95 14 10.5C14 11.05 13.55 11.5 13 11.5Z" fill="#8E44AD"/>
    </svg>
    """
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(baron_svg, unsafe_allow_html=True)
            st.subheader("Baron Nashor")
        
        with col2:
            if st.session_state.game_state == "stopped":
                st.session_state.result_message = ""
                st.info(f"Votre Châtiment inflige **{SMITE_DAMAGE}** points de dégâts. Soyez précis !")
                if st.button("Lancer le défi !"):
                    st.session_state.game_state = "running"
                    st.session_state.game_current_health = TOTAL_HEALTH
                    st.session_state.last_frame_time = time.time()
                    st.session_state.current_dps = random.randint(350, 550)
                    st.session_state.time_for_next_dps_change = time.time() + random.uniform(1.5, 3.0)
                    st.rerun()

            elif st.session_state.game_state == "running":
                now = time.time()
                delta_t = now - st.session_state.last_frame_time
                if now > st.session_state.time_for_next_dps_change:
                    st.session_state.current_dps = random.randint(200, 750)
                    st.session_state.time_for_next_dps_change = now + random.uniform(1.0, 2.5)
                    st.toast(f"💥 Burst de Dégâts ! DPS: {st.session_state.current_dps}")

                damage_dealt = delta_t * st.session_state.current_dps
                st.session_state.game_current_health -= damage_dealt
                st.session_state.last_frame_time = now
                current_health = st.session_state.game_current_health
                progress = max(0, current_health / TOTAL_HEALTH)
                st.progress(progress, text=f"{int(current_health)} / {TOTAL_HEALTH} PV")
                st.metric(label="Dégâts du Châtiment", value=f"{SMITE_DAMAGE} PV")
                
                if st.button("⚡ Châtiment !"):
                    st.session_state.game_state = "finished"
                    health_when_smited = current_health
                    if health_when_smited > SMITE_DAMAGE:
                        st.session_state.result_message = f"🤔 **Trop tôt !** Vous avez châtié à {int(health_when_smited)} PV. Le Châtiment n'aurait pas tué le Baron !"
                    else:
                        diff = SMITE_DAMAGE - health_when_smited
                        PERFECT_MARGIN = 25
                        SUCCESS_MARGIN = 120
                        if diff <= PERFECT_MARGIN:
                            st.session_state.result_message = f"🎉 **Smite PARFAIT !** Vous avez châtié à {int(health_when_smited)} PV (différence: {int(diff)}). Vous êtes le roi de la jungle !"
                        elif diff <= SUCCESS_MARGIN:
                            st.session_state.result_message = f"👍 **Excellent Châtiment !** Vous avez châtié à {int(health_when_smited)} PV. L'objectif est sécurisé !"
                        else:
                            st.session_state.result_message = f"😭 **Trop tard !** Vous avez châtié à {int(health_when_smited)} PV. L'ennemi a eu le temps de le voler !"
                    st.rerun()
                
                if current_health > 0:
                    time.sleep(0.05)
                    st.rerun()
                else:
                    st.session_state.game_state = "finished"
                    st.session_state.result_message = "Le Baron est mort sans votre aide. Dommage !"
                    st.rerun()

            elif st.session_state.game_state == "finished":
                st.info(st.session_state.result_message)
                if st.button("Réessayer"):
                    st.session_state.game_state = "stopped"
                    st.rerun()

# --- FONCTIONS D'AFFICHAGE ---
def display_spells_info(data):
    st.markdown(f"## {data['champion_name']}, *{data['champion_title'].capitalize()}*")
    st.divider()
    st.image(data['splash_url'], use_container_width=True) # <-- CORRIGÉ
    st.divider()
    st.subheader("Compétences")
    all_spells = []
    passive_info = data['passive']
    all_spells.append({ "key": "Passif", "name": passive_info['name'], "icon_url": passive_info['icon_url'], "description": passive_info['description'] })
    for spell in data['spells']:
        all_spells.append({ "key": spell['id'], "name": spell['name'], "icon_url": spell['icon_url'], "description": spell['description'] })
    cols = st.columns(5)
    for i, spell in enumerate(all_spells):
        with cols[i]:
            with st.container(border=True):
                st.image(spell['icon_url'])
                st.markdown(f"**{spell['name']} ({spell['key']})**")
                st.caption(spell['description'])

def display_character_sheet(data):
    st.markdown(f"# {data['name']} - *{data['title'].capitalize()}*")
    st.caption(f"ℹ️ Source : {data['source']}")
    st.image(data['splash_url'], use_container_width=True) # <-- CORRIGÉ
    st.markdown("---")
    tab_lore, tab_skills, tab_skins = st.tabs(["📖 Histoire & Relations", "✨ Compétences", "🎨 Skins"])
    with tab_lore:
        with st.container(border=True):
            st.markdown("### Histoire")
            with st.expander("Lire le lore complet..."):
                st.markdown(data['lore'])
            st.markdown("##### Relations Clés")
            st.markdown(data['relations'])
    with tab_skills:
        with st.container(border=True):
            st.markdown("### Aperçu des Compétences")
            for spell in data['spells']:
                icon_col, name_col = st.columns([1, 6])
                with icon_col:
                    st.image(spell['icon_url'], width=48)
                with name_col:
                    st.markdown(f"**{spell['name']}**")
                    description = spell.get('description', 'Pas de description disponible.')
                    preview_text = (description[:150] + '...') if len(description) > 150 else description
                    st.caption(preview_text)
                st.divider()
        if st.button(f"⚙️ Afficher les détails des compétences de {data['name']}", key=f"details_{data['name']}"):
            st.session_state.messages.append({"role": "user", "content": f"Quelles sont les compétences de {data['name']} ?"})
            st.rerun()
    with tab_skins:
        full_champion_data = get_champion_data(data['name'])
        if full_champion_data and 'skins' in full_champion_data:
            st.markdown("### Galerie des Skins")
            cols = st.columns(4)
            col_index = 0
            for skin in full_champion_data['skins']:
                skin_url = f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{full_champion_data['id']}_{skin['num']}.jpg"
                with cols[col_index]:
                    with st.container(border=True):
                        skin_name = skin['name'] if skin['name'] != 'default' else 'Classique'
                        st.image(skin_url, caption=skin_name)
                col_index = (col_index + 1) % 4

def display_item_info(data):
    st.subheader(data['name'])
    st.caption(f"ℹ️ Source : {data['source']} | Coût : {data['cost']} or")
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(data['icon_url'])
    with col2:
        st.markdown(data['description'])

def display_comparison(data):
    st.header(f"Analyse : {data['champion1']['name']} vs. {data['champion2']['name']}")
    col1, col2 = st.columns(2)
    with col1:
        st.image(data['champion1']['splash_url'])
    with col2:
        st.image(data['champion2']['splash_url'])
    st.markdown("---")
    st.markdown(data['analysis'])
    
def display_ultimate_bravery(data):
    st.header("Défi Ultimate Bravery Accepté !", anchor=False)
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(data['champion']['splash_url'])
            st.subheader(data['champion']['name'])
            st.caption(data['champion']['title'])
        with col2:
            st.info(f"**Rôle Assigné :** {data['role']}")
            st.error(f"**Ordre des Compétences :** {' > '.join(data['skill_order'])} > R")
            st.markdown("**Sorts d'Invocateur :**")
            s_col1, s_col2, s_col3 = st.columns([1,1,4])
            with s_col1:
                st.image(data['summoner_spells'][0]['icon_url'], width=48)
                st.caption(data['summoner_spells'][0]['name'])
            with s_col2:
                st.image(data['summoner_spells'][1]['icon_url'], width=48)
                st.caption(data['summoner_spells'][1]['name'])
            st.markdown("**Build Final :**")
            i_cols = st.columns(6)
            for i, item in enumerate(data['final_build']):
                with i_cols[i]:
                    st.image(item['icon_url'])
                    st.caption(item['name'])

def display_draft_suggestion(data):
    st.header("Analyse de Draft par Homo Draftus", anchor=False)
    with st.container(border=True):
        st.markdown(data['analysis'])

def display_message(message, message_index):
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, dict):
            type_de_contenu = content.get("type")
            if type_de_contenu == "smite_game": display_smite_minigame()
            elif type_de_contenu == "file_download":
                st.download_button(label=content.get("label", "Télécharger"), data=bytes(content.get("data")), file_name=content.get("file_name", "export.pdf"), mime="application/pdf", key=f"pdf_{message_index}")
            elif type_de_contenu == "character_sheet": display_character_sheet(content)
            elif type_de_contenu == "spells_info": display_spells_info(content)
            elif type_de_contenu == "item_info": display_item_info(content)
            elif type_de_contenu == "comparison": display_comparison(content)
            elif type_de_contenu == "ultimate_bravery": display_ultimate_bravery(content)
            elif type_de_contenu == "draft_suggestion": display_draft_suggestion(content)
            elif "source" in content:
                st.caption(f"ℹ️ Source : {content['source']}")
                st.markdown(content['content'])
        else:
            st.markdown(str(content))

# --- TITRE (LOGO) ---
col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    try:
        st.image("images/logo.png", use_container_width=True) # <-- CORRIGÉ
    except FileNotFoundError:
        st.title("Heimerdinger Assistant")
        st.warning("Logo introuvable. Assurez-vous d'avoir un dossier 'images' avec 'logo.png' à l'intérieur.")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("Contrôles")
    if st.button("🔄 Réinitialiser la conversation"):
        st.session_state.messages = []
        st.rerun()
    st.divider()

    st.header("🧠 Homo Draftus - Aide à la Draft")
    all_champions = get_all_champions_list()
    if all_champions:
        champion_names = sorted([data['name'] for id, data in all_champions.items()])
        enemy_picks = st.multiselect("Champions ennemis :", options=champion_names, max_selections=5)
        my_role = st.selectbox("Votre rôle :", options=["Top", "Jungle", "Mid", "ADC", "Support"])
        if st.button("Analyser la draft"):
            if enemy_picks and my_role:
                with st.spinner("Homo Draftus analyse la méta..."):
                    suggestion = get_draft_suggestion(enemy_champions=enemy_picks, my_role=my_role)
                    st.session_state.messages.append({"role": "assistant", "content": suggestion})
                    st.rerun()
            else:
                st.warning("Veuillez sélectionner au moins un champion ennemi et votre rôle.")
    st.divider()
    
    st.header("🔥 Ultimate Bravery")
    if st.button("Lancer un défi !"):
        challenge = generate_ultimate_bravery_challenge()
        st.session_state.messages.append({"role": "assistant", "content": challenge})
        st.rerun()
    st.divider()

    st.header("🔎 Explorateur de Champions")
    if all_champions:
        selected_champion = st.selectbox("Choisir un champion :", options=champion_names, index=None, placeholder="Sélectionnez...")
        if selected_champion and st.button(f"Afficher la fiche de {selected_champion}"):
            st.session_state.messages.append({"role": "user", "content": f"Qui est {selected_champion} ?"})
            st.rerun()
    st.divider()

    st.header("Base de connaissances (RAG)")
    if st.button("Construire / Mettre à jour"):
        with st.spinner("Construction de l'index vectoriel en cours..."):
            create_vector_store()
    st.caption("Cliquez ici pour indexer les fichiers du dossier 'knowledge_base'.")
    st.divider()

    st.header("Mode de l'Assistant")
    st.session_state.mode = st.radio("...", ASSISTANT_MODES, horizontal=True, label_visibility="collapsed")

# --- LOGIQUE PRINCIPALE DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for i, msg in enumerate(st.session_state.messages):
    display_message(msg, i)

if question := st.chat_input("Posez votre question sur League of Legends..."):
    st.session_state.messages.append({"role": "user", "content": question})
    if "jungle diff" in question.lower():
        st.session_state.messages.append({"role": "assistant", "content": {"type": "smite_game"}})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.spinner(f"Heimerdinger ({st.session_state.mode}) réfléchit..."):
        last_question = st.session_state.messages[-1]["content"]
        if any(keyword in last_question.lower() for keyword in RAG_KEYWORDS):
            response_content = {"source": "Base de Connaissances (Fichiers Locaux)", "content": query_rag_system(last_question)}
        else:
            history_for_gemini = [(msg["role"], msg["content"]) for msg in st.session_state.messages if isinstance(msg["content"], str)]
            response_content = call_gemini_with_tools(history_for_gemini, model, mode=st.session_state.mode)
        
        if not isinstance(response_content, dict):
            response_content = {"source": "Connaissances générales de l'IA (Gemini)", "content": response_content}

        assistant_message = {"role": "assistant", "content": response_content}
        st.session_state.messages.append(assistant_message)
        st.rerun()
