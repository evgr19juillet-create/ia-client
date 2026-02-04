import streamlit as st
import google.generativeai as genai
import json
import os

# --- CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_KEY"]
except:
    api_key = os.getenv("GEMINI_KEY")

if not api_key:
    st.error("ERREUR CRITIQUE : La clé API est introuvable dans les secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- LE CERVEAU ---
def get_model():
    return genai.GenerativeModel('gemini-pro')

# --- ANALYSE ---
def analyser(text):
    model = get_model()
    prompt = f"""
    Analyse ce message et renvoie un JSON.
    Message : "{text}"
    Format : {{"sentiment": "X", "category": "Y", "summary": "Z"}}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        # ICI : On force l'affichage de l'erreur réelle pour le diagnostic
        return {"sentiment": "Erreur", "category": "Erreur", "summary": f"DÉTAIL ERREUR : {str(e)}"}

# --- REPONSE ---
def repondre(text, analysis):
    model = get_model()
    prompt = f"Réponds à ce client mécontent : {text}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Je ne peux pas répondre à cause de l'erreur suivante : {str(e)}"

# --- INTERFACE ---
st.set_page_config(page_title="Debug Service Client", page_icon="🔧")
st.title("🔧 Mode Diagnostic")

message = st.text_area("Message client :", value="Je suis déçu de ma commande.", height=100)

if st.button("Lancer le diagnostic 🕵️‍♂️"):
    with st.spinner("Test en cours..."):
        # Test direct de connexion
        try:
            # On tente une analyse
            res = analyser(message)
            st.metric("Résultat", res.get("sentiment"))
            
            # C'EST ICI QU'ON VERRA LE VRAI PROBLEME
            if "DÉTAIL ERREUR" in res.get("summary", ""):
                st.error(res.get("summary"))
            else:
                st.success(f"Analyse réussie : {res.get('summary')}")
                st.write(repondre(message, res))
                
        except Exception as e:
            st.error(f"Gros crash : {str(e)}")
