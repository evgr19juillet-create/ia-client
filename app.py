import streamlit as st
import google.generativeai as genai
import json
import os

# --- 1. CONFIGURATION ---
try:
    # On récupère la clé secrète
    api_key = st.secrets["GEMINI_KEY"]
except:
    # Cas de secours
    api_key = os.getenv("GEMINI_KEY")

if not api_key:
    st.error("Oups ! La clé secrète est introuvable.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. LE CERVEAU (Modèle standard) ---
def get_model():
    # On utilise 'gemini-pro' qui est le modèle le plus stable
    return genai.GenerativeModel('gemini-pro')

# --- 3. FONCTIONS IA ---
def analyser(text):
    model = get_model()
    prompt = f"""
    Analyse ce message et renvoie UNIQUEMENT un format JSON valide.
    Message : "{text}"
    Format attendu :
    {{
        "sentiment": "Positif/Négatif/Neutre",
        "category": "Problème technique/Livraison/Facturation/Autre",
        "summary": "Résumé en 10 mots max"
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Nettoyage de la réponse pour éviter les bugs de format
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return {"sentiment": "Erreur", "category": "Inconnu", "summary": "Impossible d'analyser"}

def repondre(text, analysis):
    model = get_model()
    prompt = f"""
    Tu es un expert du service client.
    Le client est : {analysis.get('sentiment')}.
    Le problème est : {analysis.get('category')}.
    Message du client : "{text}"
    
    Rédige une réponse courte, professionnelle et bienveillante.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Désolé, je ne peux pas générer de réponse pour le moment."

# --- 4. L'INTERFACE WEB ---
st.set_page_config(page_title="Mon Service Client IA", page_icon="🤖")

st.title("🤖 Assistant Service Client")
st.write("Cette IA analyse vos réclamations et propose une réponse.")

message = st.text_area("Collez le message du client ici :", height=150)

if st.button("Lancer l'analyse 🚀"):
    if message:
        with st.spinner("L'IA réfléchit..."):
            # Étape 1 : Analyse
            resultat = analyser(message)
            
            # Affichage des résultats
            col1, col2 = st.columns(2)
            col1.metric("Humeur détectée", resultat.get("sentiment"))
            col2.metric("Type de problème", resultat.get("category"))
            st.info(f"Résumé : {resultat.get('summary')}")
            
            st.divider()
            
            # Étape 2 : Réponse
            st.subheader("Proposition de réponse :")
            reponse_ia = repondre(message, resultat)
            st.success(reponse_ia)
    else:
        st.warning("Veuillez écrire un message d'abord !")
