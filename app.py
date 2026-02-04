import streamlit as st
import google.generativeai as genai
import json
import os
import urllib.parse # Nécessaire pour créer le lien mail

# --- 1. CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_KEY"]
except:
    api_key = os.getenv("GEMINI_KEY")

if not api_key:
    st.error("Clé API manquante.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. FONCTIONS ---
def trouver_modele_disponible():
    try:
        liste_modeles = genai.list_models()
        for m in liste_modeles:
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
        return "models/gemini-1.5-flash"
    except:
        return "models/gemini-pro"

def analyser(text):
    nom_modele = trouver_modele_disponible()
    model = genai.GenerativeModel(nom_modele)
    try:
        response = model.generate_content(f"Analyse ce problème en JSON (category, summary). Message : {text}")
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return {"category": "Litige", "summary": "Problème client"}

def generer_reclamation_client(text, analysis):
    nom_modele = trouver_modele_disponible()
    model = genai.GenerativeModel(nom_modele)
    
    prompt = f"""
    SITUATION : Client mécontent : "{text}" ({analysis.get('category')})
    MISSION : Rédige un mail de réclamation court, percutant et professionnel.
    Ne mets PAS les crochets [Nom] ou [Date], écris le texte brut prêt à être envoyé.
    Demande un remboursement ou un dédommagement clair.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur de rédaction."

# --- 3. INTERFACE ---
st.set_page_config(page_title="Mon Avocat IA", page_icon="⚖️")
st.title("⚖️ Avocat de Poche")

message = st.text_area("Expliquez votre problème :", height=100)

if st.button("Générer la réclamation ⚡"):
    with st.spinner("L'IA prépare votre défense..."):
        infos = analyser(message)
        lettre = generer_reclamation_client(message, infos)
        
        st.success("Dossier prêt !")
        st.text_area("Texte généré :", value=lettre, height=300)
        
        # --- LA MAGIE : Le lien mailto ---
        # On encode le texte pour qu'il passe dans une URL
        sujet = f"Réclamation : {infos.get('category')}"
        sujet_encode = urllib.parse.quote(sujet)
        corps_encode = urllib.parse.quote(lettre)
        
        # Création du lien qui ouvre votre boîte mail
        lien_mail = f"mailto:?subject={sujet_encode}&body={corps_encode}"
        
        st.link_button("📧 Ouvrir dans mon Gmail / Outlook", lien_mail)
