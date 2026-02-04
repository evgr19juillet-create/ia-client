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

# --- 2. CERVEAU INTELLIGENT ---
def trouver_modele_disponible():
    try:
        liste_modeles = genai.list_models()
        for m in liste_modeles:
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
        return "models/gemini-1.5-flash"
    except:
        return "models/gemini-pro"

# --- 3. FONCTIONS IA ---
def analyser(text):
    nom_modele = trouver_modele_disponible()
    model = genai.GenerativeModel(nom_modele)
    
    prompt = f"""
    Analyse ce problème client en JSON.
    Message : "{text}"
    Format : {{"category": "Le type de problème (ex: Retard, Casse, Vol)", "summary": "Résumé des faits"}}
    """
    try:
        response = model.generate_content(prompt)
        clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return {"category": "Problème", "summary": "Incident client"}

def generer_reclamation_client(text, analysis):
    nom_modele = trouver_modele_disponible()
    model = genai.GenerativeModel(nom_modele)
    
    # C'est ici qu'on change le comportement de l'IA
    prompt = f"""
    Tu es un assistant juridique expert en défense du consommateur.
    
    SITUATION :
    Un client a subi ce préjudice : "{text}"
    Catégorie : {analysis.get('category')}
    
    MISSION :
    Rédige une lettre de réclamation formelle et ferme adressée au Service Client de l'entreprise responsable.
    
    CONTENU OBLIGATOIRE :
    1. Un objet clair (ex: Mise en demeure, Réclamation).
    2. Un rappel factuel des faits (utilise le résumé).
    3. Une demande explicite de DÉDOMMAGEMENT, de GESTE COMMERCIAL ou de REMBOURSEMENT.
    4. Un ton courtois mais très ferme et juridique.
    5. Termine par une formule de politesse standard.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Impossible de rédiger la lettre."

# --- 4. INTERFACE ---
st.set_page_config(page_title="Générateur de Réclamation", page_icon="⚖️")

st.title("⚖️ Assistant Réclamation & Dédommagement")
st.caption("Ne vous laissez pas faire ! L'IA rédige votre demande de remboursement.")

message = st.text_area("Racontez votre mésaventure ici :", height=150, placeholder="Exemple : Mon train avait 4h de retard et la clim ne marchait pas...")

if st.button("Générer ma lettre de réclamation 📄"):
    if message:
        with st.spinner("Rédaction de votre courrier en cours..."):
            # Analyse rapide
            infos = analyser(message)
            
            st.success(f"Dossier identifié : {infos.get('category')}")
            
            st.divider()
            
            st.subheader("📩 Votre courrier prêt à envoyer :")
            # On génère la lettre
            lettre = generer_reclamation_client(message, infos)
            
            # On affiche la lettre dans une zone de code pour copier facilement
            st.text_area("Copiez ce texte :", value=lettre, height=400)
            
    else:
        st.warning("Décrivez d'abord votre problème !")
