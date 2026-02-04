import streamlit as st
import google.generativeai as genai
import json

# --- CONFIGURATION SÉCURISÉE ---
# L'application va chercher la clé dans les "coffres-forts" du serveur
try:
    api_key = st.secrets["GEMINI_KEY"]
except:
    # Si on est en local et qu'on a oublié de configurer, on met un message d'aide
    st.error("Clé API manquante. Ajoutez-la dans les 'Secrets' de Streamlit Cloud.")
    st.stop()

genai.configure(api_key=api_key)

# --- FONCTIONS IA ---
def get_model():
    # On force un modèle standard pour éviter les erreurs
    return genai.GenerativeModel('gemini-1.5-flash')

def analyser(text):
    model = get_model()
    prompt = f"""
    Analyse ce message. Réponds UNIQUEMENT avec ce JSON :
    {{
        "sentiment": "Négatif/Neutre/Positif",
        "category": "Livraison/Produit/Service/Autre",
        "summary": "Résumé en 1 phrase"
    }}
    Message : "{text}"
    """
    try:
        response = model.generate_content(prompt)
        clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return {"sentiment": "Erreur", "category": "Erreur", "summary": "L'IA n'a pas pu lire le message"}

def repondre(text, analysis):
    model = get_model()
    prompt = f"""
    Agis comme un service client pro.
    Client : {analysis.get('sentiment')}. Problème : {analysis.get('category')}.
    Message original : "{text}"
    
    Rédige une réponse courte et empathique.
    """
    response = model.generate_content(prompt)
    return response.text

# --- INTERFACE ---
st.set_page_config(page_title="Service Client IA", page_icon="🤖")
st.title("🤖 Réponse Automatique")

message = st.text_area("Collez la réclamation ici :", height=150)

if st.button("Analyser"):
    if message:
        with st.spinner("Analyse en cours..."):
            analyse = analyser(message)
            
            c1, c2 = st.columns(2)
            c1.metric("Emotion", analyse.get("sentiment"))
            c2.metric("Sujet", analyse.get("category"))
            st.info(analyse.get("summary"))
            
            st.subheader("Proposition de réponse :")
            st.write(repondre(message, analyse))
    else:
        st.warning("Il faut écrire un message !")