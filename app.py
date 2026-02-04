import streamlit as st
import google.generativeai as genai
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURATION DE LA PAGE (Look & Feel) ---
st.set_page_config(
    page_title="Justi-Bot",
    page_icon="⚖️",
    layout="wide", # On utilise toute la largeur de l'écran
    initial_sidebar_state="expanded"
)

# --- 2. STYLE PERSONNALISÉ (CSS) ---
# C'est ici qu'on met le "maquillage" du site
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    .reportview-container {
        background: #f0f2f6;
    }
    h1 {
        color: #0e1117;
        text-align: center;
    }
    .success-box {
        padding: 20px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CONFIGURATION SECRETS ---
try:
    api_key = st.secrets["GEMINI_KEY"]
    user_email = st.secrets["EMAIL_ADDRESS"]
    user_password = st.secrets["EMAIL_PASSWORD"]
except:
    api_key = os.getenv("GEMINI_KEY")
    user_email = os.getenv("EMAIL_ADDRESS")
    user_password = os.getenv("EMAIL_PASSWORD")

if not api_key:
    st.error("⚠️ Clé Gemini manquante.")
    st.stop()

genai.configure(api_key=api_key)

# --- 4. FONCTIONS (Moteur) ---
def envoyer_mail_reel(destinataire, sujet, corps):
    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(corps, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user_email, user_password)
        server.send_message(msg)
        server.quit()
        return True, "✅ Dossier transmis au tribunal (enfin, par mail) !"
    except Exception as e:
        return False, f"Erreur technique : {str(e)}"

def trouver_modele_disponible():
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
        response = model.generate_content(f"Analyse ce problème en JSON (category, summary). Contexte : {text}")
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return {"category": "Litige", "summary": "Problème commande"}

def generer_reclamation_offensive(text, analysis):
    model = genai.GenerativeModel(trouver_modele_disponible())
    prompt = f"""
    Tu es un avocat redoutable spécialisé en droit de la consommation.
    SITUATION : "{text}" (Catégorie: {analysis.get('category')})
    
    MISSION : Rédige une MISE EN DEMEURE formelle.
    EXIGE un remboursement immédiat ou un dédommagement chiffré.
    Cite des articles de loi fictifs ou réels pour impressionner.
    Ton : Froid, menaçant (juridiquement), professionnel.
    Pas de crochets [ ]. Texte prêt à l'emploi.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur de rédaction."

# --- 5. INTERFACE UTILISATEUR (Façade) ---

# Barre latérale (Menu de gauche)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4252/4252329.png", width=100)
    st.title("Justi-Bot 🤖")
    st.markdown("---")
    st.write("### 📖 Comment ça marche ?")
    st.info("1. Racontez vos malheurs.\n2. L'IA rédige une lettre juridique.\n3. Vous validez et l'IA l'envoie.")
    st.markdown("---")
    st.caption("© 2024 - Votre Avocat de Poche")

# Titre Principal
st.title("⚖️ Cabinet de Défense Automatisé")
st.markdown("#### *Ne laissez plus rien passer. Réclamez votre dû.*")
st.divider()

# Zone de saisie (2 colonnes pour faire pro)
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1. Les Faits")
    message = st.text_area("Décrivez le litige en détail :", height=200, placeholder="Exemple : J'ai reçu ma commande #12345 avec 3 semaines de retard et l'écran est fissuré...")

with col2:
    st.subheader("2. La Cible")
    email_destinataire = st.text_input("Email du Service Client :", placeholder="sav@arnaque.com")
    st.markdown("---")
    if st.button("Generer la procédure 🔨", type="primary"):
        if message and email_destinataire:
            with st.spinner("Consultation des codes juridiques..."):
                infos = analyser(message)
                lettre = generer_reclamation_offensive(message, infos)
                st.session_state['lettre_prete'] = lettre
                st.session_state['infos_pretes'] = infos
                st.session_state['etape'] = 2
        else:
            st.error("Dossier incomplet (Message ou Email manquant).")

# Zone de Résultat (s'affiche seulement après le clic)
if 'etape' in st.session_state and st.session_state['etape'] == 2:
    st.divider()
    st.header("📂 Dossier Juridique Prêt")
    
    # On met le résultat dans un joli cadre (expander)
    with st.expander("Voir l'analyse de l'IA", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Catégorie", st.session_state['infos_pretes'].get('category'))
        c2.metric("Niveau d'attaque", "MAXIMAL 🔴")

    st.subheader("3. Vérification du courrier")
    col_text, col_send = st.columns([3, 1])
    
    with col_text:
        texte_final = st.text_area("Lettre de mise en demeure :", value=st.session_state['lettre_prete'], height=400)
        sujet_final = st.text_input("Objet du mail :", value=f"URGENT : MISE EN DEMEURE - Dossier {st.session_state['infos_pretes'].get('category')}")
    
    with col_send:
        st.write("### Action")
        st.warning("⚠️ Attention, ce bouton envoie réellement le mail.")
        if st.button("🚀 ENVOYER MAINTENANT"):
            with st.spinner("Envoi recommandé électronique..."):
                succes, msg = envoyer_mail_reel(email_destinataire, sujet_final, texte_final)
                if succes:
                    st.balloons()
                    st.success(msg)
                else:
                    st.error(msg)
