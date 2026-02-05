import streamlit as st
import google.generativeai as genai
import json
import os
import smtplib
from datetime import datetime  # <--- AJOUT POUR LA DATE
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Justi-Bot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE CSS ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    h1 { color: #0e1117; text-align: center; }
    .stTextArea textarea { font-size: 16px; }
    
    /* Taille réduite pour les métriques */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
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

# --- 4. FONCTIONS ---
def envoyer_mail_reel(destinataire, sujet, corps):
    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(corps, 'plain'))

    try:
        # Serveur Hostinger
        server = smtplib.SMTP('smtp.hostinger.com', 587) 
        server.starttls()
        server.login(user_email, user_password)
        server.send_message(msg)
        server.quit()
        return True, "✅ Réclamation officielle envoyée avec succès !"
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

# --- MODIFICATION ICI : On ajoute ville et date ---
def generer_reclamation_offensive(text, analysis, ville_user):
    model = genai.GenerativeModel(trouver_modele_disponible())
    
    # Récupération automatique de la date
    date_jour = datetime.now().strftime("%d/%m/%Y")
    
    prompt = f"""
    Tu es un expert en médiation (NON AVOCAT).
    SITUATION : "{text}" (Catégorie: {analysis.get('category')})
    VILLE DU CLIENT : {ville_user}
    DATE : {date_jour}
    
    MISSION : Rédige une lettre de réclamation FORMELLE.
    
    CONSIGNES STRICTES :
    1. Commence IMPÉRATIVEMENT par : "Fait à {ville_user}, le {date_jour}" en haut à droite.
    2. Ensuite, mets l'objet.
    3. Ton : Sérieux, juridique mais courtois.
    4. Ne mets PAS de crochets pour la ville ou la date, utilise les vraies valeurs fournies.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur de rédaction."

# --- 5. INTERFACE ---

with st.sidebar:
    st.title("🛡️ Justi-Bot")
    st.markdown("---")
    st.info("L'IA rédige vos courriers juridiques.")
    st.link_button("☕ Soutenir le projet", "https://www.buymeacoffee.com/valentinremiot")
    st.caption("© 2026 JustiBot")

st.title("⚖️ Assistant de Réclamation Automatisé")
st.markdown("#### *Obtenez réparation pour vos produits défectueux ou retards.*")
st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1. Le Problème")
    message = st.text_area("Détails du litige :", height=180, placeholder="Racontez votre problème ici...")

with col2:
    st.subheader("2. Vos Infos")
    # --- AJOUT DU CHAMP VILLE ---
    ville = st.text_input("Votre Ville :", value="Paris")
    email_destinataire = st.text_input("Email du SAV :", placeholder="contact@vendeur.com")
    
    st.write("") 
    if st.button("Rédiger la lettre ✍️", type="primary"):
        if message and email_destinataire and ville:
            with st.spinner("Analyse et rédaction..."):
                infos = analyser(message)
                # On passe la ville à la fonction
                lettre = generer_reclamation_offensive(message, infos, ville)
                st.session_state['lettre_prete'] = lettre
                st.session_state['infos_pretes'] = infos
                st.session_state['etape'] = 2
        else:
            st.error("Merci de remplir tous les champs (Ville incluse).")

# Résultat
if 'etape' in st.session_state and st.session_state['etape'] == 2:
    st.divider()
    
    with st.expander("📊 Analyse (cliquer pour voir)", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Motif", st.session_state['infos_pretes'].get('category'))
        c2.metric("Stratégie", "Mise en demeure amiable")

    st.subheader("3. Validation et Envoi")
    
    col_text, col_send = st.columns([3, 1])
    
    with col_text:
        texte_final = st.text_area("Votre courrier :", value=st.session_state['lettre_prete'], height=450)
        sujet_final = st.text_input("Objet du mail :", value=f"RÉCLAMATION - {st.session_state['infos_pretes'].get('category')}")
    
    with col_send:
        st.info("Tout est bon ?")
        if st.button("🚀 ENVOYER"):
            with st.spinner("Envoi..."):
                succes, msg = envoyer_mail_reel(email_destinataire, sujet_final, texte_final)
                if succes:
                    st.balloons()
                    st.success(msg)
                else:
                    st.error(msg)
