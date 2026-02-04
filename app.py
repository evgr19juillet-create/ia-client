import streamlit as st
import google.generativeai as genai
import json
import os

# --- 1. CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_KEY"]
except:
    api_key = os.getenv("GEMINI_KEY")

if not api_key:
    st.error("Clé API manquante.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. LE SELECTEUR INTELLIGENT ---
def trouver_modele_disponible():
    """Demande à Google quel modèle est disponible pour cette clé API"""
    try:
        # On demande la liste officielle à Google
        liste_modeles = genai.list_models()
        for m in liste_modeles:
            # On cherche un modèle capable de générer du texte
            if 'generateContent' in m.supported_generation_methods:
                # On privilégie le modèle rapide "flash" s'il existe
                if 'flash' in m.name:
                    return m.name
        
        # Si on n'a pas trouvé de "flash", on refait un tour et on prend le premier qui vient
        liste_modeles = genai.list_models()
        for m in liste_modeles:
            if 'generateContent' in m.supported_generation_methods:
                return m.name
                
    except Exception as e:
        return None
    
    # Si tout échoue, on tente le nom standard par défaut
    return "models/gemini-1.5-flash"

# --- 3. FONCTIONS IA ---
def analyser(text):
    nom_modele = trouver_modele_disponible()
    if not nom_modele:
        return {"sentiment": "Erreur", "category": "Erreur", "summary": "Connexion Google échouée"}
        
    model = genai.GenerativeModel(nom_modele)
    
    prompt = f"""
    Analyse ce message en JSON strict.
    Message : "{text}"
    Format : {{"sentiment": "Positif/Négatif", "category": "Sujet", "summary": "Résumé court"}}
    """
    try:
        response = model.generate_content(prompt)
        clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        return {"sentiment": "Erreur", "category": "Erreur", "summary": f"Erreur technique : {e}"}

def repondre(text, analysis):
    nom_modele = trouver_modele_disponible()
    model = genai.GenerativeModel(nom_modele)
    
    prompt = f"Réponds poliment à ce client : {text}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Impossible de rédiger la réponse."

# --- 4. INTERFACE ---
st.set_page_config(page_title="Service Client IA", page_icon="🤖")
st.title("🤖 Assistant Intelligent")

# On affiche quel modèle a été trouvé (pour vérifier que ça marche)
modele_actuel = trouver_modele_disponible()
st.caption(f"✅ Connecté au cerveau : {modele_actuel}")

message = st.text_area("Votre réclamation :", height=150)

if st.button("Analyser"):
    if message:
        with st.spinner("Analyse en cours..."):
            res = analyser(message)
            
            c1, c2 = st.columns(2)
            c1.metric("Humeur", res.get("sentiment"))
            c2.metric("Sujet", res.get("category"))
            st.info(f"Résumé : {res.get('summary')}")
            
            st.divider()
            st.write(repondre(message, res))
