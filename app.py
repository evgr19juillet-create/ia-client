import streamlit as st
import google.generativeai as genai
import json
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Justi-Bot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE VISUEL ---
st.markdown("""
<style>
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
        background-color: #FF4B4B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. RÉCUPÉRATION DES SECRETS (C'est ici que ça se joue !) ---
try:
    # On récupère les clés que tu as mises dans Streamlit Cloud
    api_key = st.secrets["GEMINI_KEY"]
    user_email = st.secrets["EMAIL_ADDRESS"]
    user_password = st.secrets["EMAIL_PASSWORD"]
except FileNotFoundError:
    # Si on lance en local sans secrets, on affiche une erreur ou on cherche ailleurs
    st.error("⚠️ Les secrets (clés) ne sont pas configurés sur Streamlit Cloud.")
    st.stop()

# Configuration de l'IA avec la clé récupérée
genai.configure(api_key=api_key)

# --- 4. FONCTIONS ---

def envoyer_mail_reel(destinataire, sujet, corps):
    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(corps, 'plain'))

    try:
        # Configuration SMTP pour Hostinger
        server = smtplib.SMTP('smtp.hostinger.com', 587)
        server.starttls()
        # Ici on utilise le mot de passe sécurisé récupéré plus haut
        server.login(user_email, user_password)
        server.send_message(msg)
        server.quit()
        return True, "✅ Courrier envoyé avec succès !"
    except Exception as e:
        return False, f"Erreur d'envoi : {str(e)}"

def trouver_modele_disponible():
    # Cherche le meilleur modèle Gemini disponible
    try:
        liste = genai.list_models()
        for m in liste:
            if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                return m.name
        return "models/gemini-1.5-flash"
    except:
        return "models/gemini-pro"

def analyser(text):
    model = genai.GenerativeModel(trouver_modele_disponible())
    try:
        # Demande une analyse structurée en JSON
        prompt = f"Analyse ce litige et renvoie un JSON {{'category': '...', 'summary': '...'}}. Contexte : {text}"
        response = model.generate_content(prompt)
        # Nettoyage de la réponse pour éviter les bugs de format
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return {"category": "Litige commercial", "summary": "Réclamation client"}

def generer_reclamation(text, analysis, user_infos):
    model = genai.GenerativeModel(trouver_modele_disponible())
    date_jour = datetime.now().strftime("%d/%m/%Y")
    
    profil = f"Nom: {user_infos['nom']}, Adresse: {user_infos['adresse']}, {user_infos['ville']}"
    
    prompt = f"""
    Rédige une mise en demeure formelle.
    CLIENT : {profil}
    DATE : {date_jour}
    SITUATION : "{text}"
    CATÉGORIE : {analysis.get('category')}
    
    RÈGLES :
    - Ton ton doit être juridique, ferme et menaçant.
    - Cite le Code Civil ou Code de la Consommation français.
    - Exige une réponse sous 8 jours.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur lors de la rédaction du courrier."

# --- 5. INTERFACE ---

with st.sidebar:
    st.title("👤 Vos Coordonnées")
    nom_client = st.text_input("Nom & Prénom")
    adresse_client = st.text_input("Adresse")
    ville_client = st.text_input("Code Postal & Ville")
    email_client_visuel = st.text_input("Votre Email (signature)")

st.title("⚖️ Justi-Bot : Assistant Juridique")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Le Litige")
    message = st.text_area("Décrivez le problème...", height=200)

with col2:
    st.subheader("Destinataire")
    email_destinataire = st.text_input("Email du SAV adverse")
    
    if st.button("Générer le courrier ⚡", type="primary"):
        if message and nom_client and ville_client:
            user_infos = {"nom": nom_client, "adresse": adresse_client, "ville": ville_client, "email_user": email_client_visuel}
            with st.spinner("L'IA analyse votre dossier..."):
                infos = analyser(message)
                lettre = generer_reclamation(message, infos, user_infos)
                st.session_state['lettre'] = lettre
                st.session_state['infos'] = infos
                st.session_state['etape'] = 2
        else:
            st.error("Remplissez vos coordonnées et le problème.")

if 'etape' in st.session_state and st.session_state['etape'] == 2:
    st.divider()
    st.success("✅ Courrier généré.")
    
    texte_final = st.text_area("Vérifiez le courrier :", value=st.session_state['lettre'], height=400)
    sujet = st.text_input("Objet du mail", value=f"MISE EN DEMEURE - {st.session_state['infos'].get('category')}")
    
    if st.button("🚀 ENVOYER MAINTENANT"):
        with st.spinner("Envoi en cours..."):
            succes, msg = envoyer_mail_reel(email_destinataire, sujet, texte_final)
            if succes:
                st.success(msg)
                st.balloons()
            else:
                st.error(msg)
