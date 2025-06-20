# Fichier : gemini_logic.py
# Description : Ajout d'un outil dédié pour l'export direct de fiches champions en PDF.

import streamlit as st
import requests
import re
import unidecode
import random
from google.generativeai import types

# --- Imports depuis vos autres fichiers ---
from config import model
from lol_api import get_latest_version, get_all_champions_list, get_all_items_data, get_all_summoner_spells_data
from rag_handler import query_rag_system
from pdf_generator import generate_pdf_from_content

# ───── DÉCLARATION DES FONCTIONS POUR GEMINI ─────
function_declarations = [
    {
        "name": "get_character_sheet",
        "description": "DOIT ÊTRE UTILISÉ pour une question générale sur un champion. Ex: 'Qui est Garen ?'. Génère une fiche visuelle complète.",
        "parameters": {"type": "object", "properties": {"champion": {"type": "string"}}, "required": ["champion"]},
    },
    {
        "name": "export_to_pdf",
        "description": "Exporte la DERNIÈRE réponse de l'assistant en fichier PDF. Ne pas utiliser si le sujet n'a pas déjà été affiché.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "generate_champion_sheet_pdf",
        "description": "Génère DIRECTEMENT un PDF de la fiche d'un champion. Utiliser pour des demandes comme 'Exporte la fiche de Garen en PDF'.",
        "parameters": {"type": "object", "properties": {"champion": {"type": "string"}}, "required": ["champion"]},
    },
    {
        "name": "get_champion_spells",
        "description": "Donne la description DÉTAILLÉE des sorts d'un champion.",
        "parameters": {"type": "object", "properties": {"champion": {"type": "string"}}, "required": ["champion"]},
    },
    {
        "name": "compare_champions",
        "description": "Compare deux champions en analysant leurs forces et faiblesses relatives.",
        "parameters": {
            "type": "object", "properties": {
                "champion1": {"type": "string", "description": "Le premier champion à comparer."},
                "champion2": {"type": "string", "description": "Le second champion à comparer."}
            }, "required": ["champion1", "champion2"]
        },
    },
    {
        "name": "get_item_info",
        "description": "Retourne les stats et la description d’un objet.",
        "parameters": {"type": "object", "properties": {"item": {"type": "string"}}, "required": ["item"]},
    },
    {
        "name": "get_draft_suggestion",
        "description": "Analyse une draft ennemie et suggère des champions à jouer pour un rôle spécifique.",
        "parameters": {
            "type": "object", "properties": {
                "enemy_champions": {"type": "array", "description": "Liste des champions ennemis.", "items": {"type": "string"}},
                "my_role": {"type": "string", "description": "Le rôle que l'utilisateur va jouer."}
            }, "required": ["enemy_champions", "my_role"]
        },
    },
    {
        "name": "generate_ultimate_bravery_challenge",
        "description": "Génère un défi 'Ultimate Bravery' complètement aléatoire.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "answer_from_knowledge_base",
        "description": "Consulte la base de connaissances pour des questions sur les patchs, stratégies, etc.",
        "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
    }
]

# ─── FONCTIONS UTILITAIRES ───
def normalize_text(text): return unidecode.unidecode(text).lower().replace("'", "").replace(".", "").replace(" ", "")
def find_champion_id_by_name(champion_name):
    all_champions = get_all_champions_list()
    if not all_champions: return None
    normalized_input = normalize_text(champion_name)
    for champion_id, champion_data in all_champions.items():
        if normalize_text(champion_data['name']) == normalized_input: return champion_id
    return None
def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).replace('&nbsp;', ' ')
@st.cache_data
def get_champion_data(champion_name):
    champion_id = find_champion_id_by_name(champion_name)
    if not champion_id: return None
    version = get_latest_version()
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR/champion/{champion_id}.json"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()["data"][champion_id]
    except (requests.RequestException, KeyError): return None
def get_generative_response(history, model_instance):
    response = model_instance.generate_content(history)
    return response.text.strip()


# ───── FONCTIONS RÉELLES (OUTILS) ─────
def get_character_sheet(champion: str):
    st.caption(f"--- Fiche Personnage pour {champion} ---")
    api_data = get_champion_data(champion)
    if not api_data: return f"Impossible de trouver les données pour '{champion}'."
    relations_question = f"Fais un résumé des relations de {api_data['name']}."
    relations_info = query_rag_system(relations_question)
    version = get_latest_version()
    base_img_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img"
    character_sheet = { "type": "character_sheet", "source": "API & RAG", "name": api_data['name'], "title": api_data['title'], "splash_url": f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{api_data['id']}_0.jpg", "lore": api_data['lore'], "relations": relations_info, "spells": [] }
    character_sheet['spells'].append({ "name": f"Passif - {api_data['passive']['name']}", "icon_url": f"{base_img_url}/passive/{api_data['passive']['image']['full']}", "description": clean_html(api_data['passive']['description']) })
    for spell in api_data['spells']:
        character_sheet['spells'].append({ "name": spell['name'], "icon_url": f"{base_img_url}/spell/{spell['image']['full']}", "description": clean_html(spell['description']) })
    return character_sheet

def generate_champion_sheet_pdf(champion: str):
    """Génère une fiche champion et la convertit directement en PDF."""
    st.caption(f"--- Génération du PDF pour {champion} ---")
    
    # 1. Obtenir les données de la fiche champion
    sheet_data = get_character_sheet(champion)
    if not isinstance(sheet_data, dict):
        return {"type": "simple_text", "content": f"Impossible de générer la fiche pour {champion}."}

    # 2. Convertir ces données en PDF
    try:
        pdf_data = generate_pdf_from_content(sheet_data)
        file_name = f"fiche_{sheet_data.get('name', 'champion').replace(' ', '_')}.pdf"
        
        # 3. Retourner la structure pour le bouton de téléchargement
        return {
            "type": "file_download",
            "data": pdf_data,
            "file_name": file_name,
            "label": f"Télécharger la fiche de {champion}"
        }
    except Exception as e:
        return {"type": "simple_text", "content": f"Désolé, une erreur est survenue lors de la création du PDF : {e}"}

def export_to_pdf():
    st.caption("--- Préparation de l'export PDF ---")
    last_assistant_message = None
    for message in reversed(st.session_state.messages):
        if message["role"] == "assistant":
            if isinstance(message["content"], dict) and message["content"].get("type") == "file_download":
                continue
            last_assistant_message = message
            break
    if not last_assistant_message:
        return {"type": "simple_text", "content": "Je n'ai pas trouvé de réponse précédente à exporter."}
    content_to_export = last_assistant_message["content"]
    try:
        pdf_data = generate_pdf_from_content(content_to_export)
        file_name = "export_heimerdinger.pdf"
        if isinstance(content_to_export, dict):
             if content_to_export.get("type") == "character_sheet":
                file_name = f"fiche_{content_to_export.get('name', 'champion').replace(' ', '_')}.pdf"
             elif content_to_export.get("type"):
                file_name = f"{content_to_export.get('type')}_export.pdf"
        return { "type": "file_download", "data": pdf_data, "file_name": file_name, "label": "Télécharger le PDF" }
    except Exception as e:
        return {"type": "simple_text", "content": f"Désolé, une erreur est survenue lors de la création du PDF : {e}"}

def get_champion_spells(champion):
    data = get_champion_data(champion)
    if not data: return f"Impossible de trouver les données pour '{champion}'."
    version = get_latest_version()
    base_img_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img"
    spell_data = { "type": "spells_info", "source": "API Riot", "champion_name": data['name'], "champion_title": data['title'], "splash_url": f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{data['id']}_0.jpg", "passive": {"name": data['passive']['name'], "description": clean_html(data['passive']['description']), "icon_url": f"{base_img_url}/passive/{data['passive']['image']['full']}"}, "spells": [] }
    for spell in data['spells']:
        spell_data['spells'].append({"id": spell['id'][-1], "name": spell['name'], "description": clean_html(spell['description']), "icon_url": f"{base_img_url}/spell/{spell['image']['full']}"})
    return spell_data

def get_item_info(item: str):
    all_items = get_all_items_data()
    if not all_items: return "Désolé, impossible de charger les données des objets."
    found_item_data = next((d for _, d in all_items.items() if normalize_text(d['name']) == normalize_text(item)), None)
    if not found_item_data: return f"Désolé, je n'ai pas trouvé l'objet '{item}'."
    version = get_latest_version()
    icon_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{found_item_data['image']['full']}"
    return { "type": "item_info", "source": "API Riot", "name": found_item_data['name'], "icon_url": icon_url, "description": clean_html(found_item_data['description']), "cost": found_item_data['gold']['total'] }

def answer_from_knowledge_base(question: str):
    return {"source": "Base de Connaissances", "content": query_rag_system(question)}

def compare_champions(champion1: str, champion2: str):
    data1 = get_champion_data(champion1)
    data2 = get_champion_data(champion2)
    if not data1 or not data2: return "Impossible de trouver les données pour l'un des champions."
    analysis_prompt = f"Compare brièvement {data1['name']} et {data2['name']} pour un combat. Analyse leurs forces et faiblesses principales en te basant sur ces tags: {data1['name']} ({', '.join(data1['tags'])}) vs {data2['name']} ({', '.join(data2['tags'])})."
    response_text = get_generative_response([{'role': 'user', 'parts': [analysis_prompt]}], model)
    return { "type": "comparison", "champion1": {"name": data1['name'], "splash_url": f"https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{data1['id']}_0.jpg"}, "champion2": {"name": data2['name'], "splash_url": f"https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{data2['id']}_0.jpg"}, "analysis": response_text }

def generate_ultimate_bravery_challenge():
    st.caption("--- Génération d'un défi Ultimate Bravery ---")
    all_champions = get_all_champions_list()
    if not all_champions: return "Erreur: impossible de charger les champions."
    champion = random.choice(list(all_champions.values()))
    role = random.choice(['Top', 'Jungle', 'Mid', 'ADC', 'Support'])
    all_spells = get_all_summoner_spells_data()
    valid_spells = [s for s in all_spells.values() if 'CLASSIC' in s['modes']]
    summoner_spells = random.sample(valid_spells, 2)
    skill_order = random.sample(['A', 'Z', 'E'], 3)
    all_items = get_all_items_data()
    purchasable_items = [item for item in all_items.values() if item['gold']['purchasable'] and 'into' not in item and item['gold']['total'] > 1500 and 'Boots' not in item.get('tags', [])]
    boots = [item for item in all_items.values() if 'Boots' in item.get('tags', []) and item['gold']['total'] > 300]
    chosen_boots = random.choice(boots)
    chosen_items = random.sample(purchasable_items, 5)
    final_build = [chosen_boots] + chosen_items
    version = get_latest_version()
    base_img_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img"
    return { "type": "ultimate_bravery", "champion": {"name": champion['name'], "title": champion['title'], "splash_url": f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion['id']}_0.jpg"}, "role": role, "skill_order": skill_order, "summoner_spells": [{"name": s['name'], "icon_url": f"{base_img_url}/spell/{s['image']['full']}"} for s in summoner_spells], "final_build": [{"name": i['name'], "icon_url": f"{base_img_url}/item/{i['image']['full']}"} for i in final_build] }
    
def get_draft_suggestion(enemy_champions: list, my_role: str):
    st.caption(f"--- Analyse de Draft : Homo Draftus ---")
    enemy_data = [get_champion_data(name) for name in enemy_champions if get_champion_data(name)]
    if not enemy_data: return "Impossible d'analyser : aucun champion ennemi valide fourni."
    enemy_composition_str = ", ".join([f"{e['name']} ({', '.join(e['tags'])})" for e in enemy_data])
    prompt = f"Tu es 'Homo Draftus', un coach stratégique de niveau Challenger pour League of Legends. Analyse la situation suivante :\n- Mon rôle : **{my_role}**\n- Composition ennemie : **{enemy_composition_str}**\n\n**Instructions :**\n1. **Analyse de la composition ennemie (2-3 lignes) :** Décris leurs forces et faiblesses.\n2. **Recommandations de picks (3 choix) :** Propose trois champions pour le rôle de **{my_role}**. Pour chaque champion, donne un **Nom de Stratégie** et explique en 2-3 lignes *pourquoi* c'est un bon choix contre *cette composition*."
    analysis = get_generative_response([{'role': 'user', 'parts': [prompt]}], model)
    return {"type": "draft_suggestion", "analysis": analysis}

# ───── APPEL INTELLIGENT DE GEMINI ─────
def call_gemini_with_tools(messages_history, model_instance, mode):
    available_functions = {
        "get_character_sheet": get_character_sheet,
        "export_to_pdf": export_to_pdf,
        "generate_champion_sheet_pdf": generate_champion_sheet_pdf,
        "get_champion_spells": get_champion_spells,
        "compare_champions": compare_champions,
        "get_item_info": get_item_info,
        "get_draft_suggestion": get_draft_suggestion,
        "generate_ultimate_bravery_challenge": generate_ultimate_bravery_challenge,
        "answer_from_knowledge_base": answer_from_knowledge_base,
    }
    persona_prompts = { "Général": "Tu es un assistant serviable.", "Lore": "Tu es un conteur passionné.", "Stratégie": "Tu es un coach expert.", "Création RP": "Tu es un maître de jeu." }
    system_instruction = persona_prompts.get(mode, persona_prompts["Général"])
    gemini_history = [{'role': 'user', 'parts': [system_instruction]}, {'role': 'model', 'parts': ["Entendu."]}]
    for role, text in messages_history:
        gemini_role = "model" if role == "assistant" else "user"
        gemini_history.append({'role': gemini_role, 'parts': [text]})
    tools = types.Tool(function_declarations=function_declarations)
    config = types.GenerationConfig(temperature=0.7)
    try:
        response = model_instance.generate_content(gemini_history, tools=[tools], generation_config=config)
        part = response.candidates[0].content.parts[0]
        if hasattr(part, "function_call"):
            call = part.function_call
            function_to_call = available_functions.get(call.name)
            if function_to_call:
                return function_to_call(**{k: v for k, v in call.args.items()})
            else:
                return get_generative_response(gemini_history, model_instance)
        else:
            return part.text if hasattr(part, 'text') and part.text else get_generative_response(gemini_history, model_instance)
    except Exception as e:
        st.error(f"Une erreur est survenue avec Gemini : {e}")
        return "Désolé, une erreur est survenue."

