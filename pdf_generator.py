# Fichier : pdf_generator.py
# Description : Correction du bug de génération PDF.

from fpdf import FPDF
import requests
from io import BytesIO
import streamlit as st

# --- Paramètres globaux pour le style des PDF ---
PDF_FONT_FAMILY = "Arial"
PDF_TITLE_FONT_SIZE = 16
PDF_H2_FONT_SIZE = 14
PDF_BODY_FONT_SIZE = 12
PDF_ACCENT_COLOR = (200, 155, 60) # Couleur Or de LoL (en RVB)

class PDF(FPDF):
    """ Classe PDF personnalisée avec en-tête et pied de page. """
    def header(self):
        self.set_font(PDF_FONT_FAMILY, 'B', 12)
        self.cell(0, 10, 'Export - Heimerdinger Assistant', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(PDF_FONT_FAMILY, 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font(PDF_FONT_FAMILY, 'B', PDF_TITLE_FONT_SIZE)
        self.set_text_color(*PDF_ACCENT_COLOR)
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def chapter_body(self, text):
        self.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 10, safe_text)
        self.ln()
        
    def add_image_from_url(self, url, w=0):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            img = BytesIO(response.content)
            x_pos = (self.w - w) / 2 if w > 0 else None
            self.image(img, x=x_pos, w=w)
        except Exception as e:
            self.set_font(PDF_FONT_FAMILY, 'I', 8)
            self.cell(0, 10, f"[Image indisponible : {e}]")
            self.ln()

# --- Fonctions de construction pour chaque type de contenu ---
def build_character_sheet_pdf(pdf, content):
    pdf.chapter_title(f"{content['name']} - {content['title']}")
    pdf.add_image_from_url(content['splash_url'], w=pdf.w - 20)
    pdf.ln(5)
    pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_H2_FONT_SIZE)
    pdf.cell(0, 10, "Histoire", 0, 1)
    pdf.chapter_body(content.get('lore', 'Non disponible.'))
    pdf.cell(0, 10, "Relations", 0, 1)
    pdf.chapter_body(content.get('relations', 'Non disponible.'))
    pdf.add_page()
    pdf.cell(0, 10, "Compétences", 0, 1)
    for spell in content.get('spells', []):
        pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_BODY_FONT_SIZE)
        pdf.cell(0, 10, spell.get('name', 'Compétence Inconnue'), 0, 1)
        pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
        pdf.chapter_body(spell.get('description', 'Pas de description.'))

def build_draft_suggestion_pdf(pdf, content):
    pdf.chapter_title("Analyse de Draft - Homo Draftus")
    pdf.chapter_body(content.get('analysis', 'Aucune analyse disponible.'))

def build_ultimate_bravery_pdf(pdf, content):
    pdf.chapter_title("Défi Ultimate Bravery")
    champ = content.get('champion', {})
    pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_H2_FONT_SIZE)
    pdf.cell(0, 10, f"Champion: {champ.get('name', '?')} - {champ.get('title', '?')}", 0, 1)
    pdf.cell(0, 10, f"Rôle: {content.get('role', '?')}", 0, 1)
    pdf.cell(0, 10, f"Ordre des Compétences: {' > '.join(content.get('skill_order', []))} > R", 0, 1)
    pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_H2_FONT_SIZE)
    pdf.cell(0, 10, "Sorts d'Invocateur", 0, 1)
    for spell in content.get('summoner_spells', []):
         pdf.cell(0, 10, f"- {spell.get('name', '?')}", 0, 1)
    pdf.cell(0, 10, "Build Final", 0, 1)
    for item in content.get('final_build', []):
         pdf.cell(0, 10, f"- {item.get('name', '?')}", 0, 1)

def build_simple_text_pdf(pdf, content):
    pdf.chapter_title("Réponse de l'Assistant")
    text_content = content.get('content', str(content))
    pdf.chapter_body(text_content)

# --- Fonction principale du générateur ---
@st.cache_data(show_spinner=False)
def generate_pdf_from_content(content):
    pdf = PDF()
    pdf.add_page()
    content_type = content.get("type") if isinstance(content, dict) else "simple_text"
    builders = {
        "character_sheet": build_character_sheet_pdf,
        "draft_suggestion": build_draft_suggestion_pdf,
        "ultimate_bravery": build_ultimate_bravery_pdf,
        "simple_text": build_simple_text_pdf,
    }
    builder_func = builders.get(content_type, build_simple_text_pdf)
    builder_func(pdf, content)
    # --- CORRECTION : On retourne directement le résultat de pdf.output() ---
    return pdf.output()

