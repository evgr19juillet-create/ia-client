import streamlit as st
import google.generativeai as genai
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Justi-Bot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE CSS (Le maquillage) ---
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
        server = smtplib.SMTP('smtp.titan.email', 587) # Modifié pour Hostinger/Titan
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

def generer_reclamation_offensive(text, analysis):
    model = genai.GenerativeModel(trouver_modele_disponible())
    
    # ICI : On change la personnalité pour rester légal mais ferme
    prompt = f"""
    Tu es un expert en médiation et en défense des consommateurs (NON AVOCAT).
    SITUATION : "{text}" (Catégorie: {analysis.get('category')})
    
    MISSION : Rédige une lettre de réclamation FORMELLE et FERME.
    OBJECTIF : Exiger un remboursement ou une indemnisation immédiate.
    TON : Sérieux, factuel, juridique (cite le Code de la Consommation si pertinent), mais courtois.
    
    IMPORTANT :
    1. Ne t'invente PAS un titre d'avocat ou de Maître.
    2. Signe simplement "Le Client" ou laisse l'espace pour le nom.
    3. Pas de crochets [ ]. Texte prêt à l'emploi.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur de rédaction."

# --- 5. INTERFACE (Façade) ---

# Sidebar (Barre latérale avec Pourboire)
with st.sidebar:
    st.title("🛡️ Justi-Bot")
    st.markdown("---")
    st.info("Votre assistant personnel pour faire valoir vos droits de consommateur sans frais d'avocat.")
    
    st.write("### Mode d'emploi :")
    st.caption("1. Décrivez le litige.\n2. L'IA rédige la mise en demeure.\n3. Vous envoyez.")
    
    # --- AJOUT SECTION POURBOIRE ---
    st.divider() # Ligne de séparation
    
    st.markdown("### ☕ Soutenir le projet")
    st.write("JustiBot est gratuit. Si cet outil vous a aidé à récupérer votre argent, vous pouvez m'offrir un café !")
    
    # IMPORTANT : Changez le lien ci-dessous par VOTRE lien Buy Me a Coffee
    link = "https://www.buymeacoffee.com/VOTRE_PSEUDO"
    
    st.markdown(f"""
    <div style="text-align: center; margin-top: 15px;">
        <a href="{link}" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important;" >
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.caption("© 2026 JustiBot")

# Page principale
st.title("⚖️ Assistant de Réclamation Automatisé")
st.markdown("#### *Obtenez réparation pour vos produits défectueux ou retards.*")
st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1. Le Problème")
    message = st.text_area("Détails du litige :", height=180, placeholder="Ex: TV livrée cassée, refus de remboursement du vendeur...")

with col2:
    st.subheader("2. Le Destinataire")
    email_destinataire = st.text_input("Email du SAV :", placeholder="contact@vendeur.com")
    st.write("") # Espace vide
    st.write("") 
    if st.button("Rédiger la lettre ✍️", type="primary"):
        if message and email_destinataire:
            with st.spinner("Analyse juridique en cours..."):
                infos = analyser(message)
                lettre = generer_reclamation_offensive(message, infos)
                st.session_state['lettre_prete'] = lettre
                st.session_state['infos_pretes'] = infos
                st.session_state['etape'] = 2
        else:
            st.error("Merci de remplir tous les champs.")

# Affichage du résultat
if 'etape' in st.session_state and st.session_state['etape'] == 2:
    st.divider()
    
    with st.expander("📊 Analyse du dossier (cliquer pour voir)", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Motif", st.session_state['infos_pretes'].get('category'))
        c2.metric("Stratégie", "Mise en demeure amiable")

    st.subheader("3. Validation et Envoi")
    
    col_text, col_send = st.columns([3, 1])
    
    with col_text:
        texte_final = st.text_area("Votre courrier prêt à partir :", value=st.session_state['lettre_prete'], height=450)
        sujet_final = st.text_input("Objet :", value=f"RÉCLAMATION - Commande / Dossier {st.session_state['infos_pretes'].get('category')}")
    
    with col_send:
        st.info("Si le texte vous convient, cliquez ci-dessous pour l'expédier.")
        if st.button("🚀 ENVOYER LE MAIL"):
            with st.spinner("Transmission en cours..."):
                succes, msg = envoyer_mail_reel(email_destinataire, sujet_final, texte_final)
                if succes:
                    st.balloons()
                    st.success(msg)
                else:
                    st.error(msg)
