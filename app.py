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
    [data-testid="stMetricValue"] { font-size: 24px !important; }
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

# --- NOUVELLE FONCTION INTELLIGENTE ---
def generer_reclamation_offensive(text, analysis, user_infos):
    model = genai.GenerativeModel(trouver_modele_disponible())
    
    date_jour = datetime.now().strftime("%d/%m/%Y")
    
    # On prépare le profil complet pour l'IA
    profil_client = f"""
    Nom : {user_infos['nom']}
    Adresse : {user_infos['adresse']}
    Code Postal / Ville : {user_infos['ville']}
    Téléphone : {user_infos['tel']}
    Email : {user_infos['email_user']}
    """
    
    prompt = f"""
    Tu es un expert en médiation (NON AVOCAT).
    
    INFORMATIONS DU CLIENT (Expéditeur) :
    {profil_client}
    
    DATE ET LIEU : Fait à {user_infos['ville']}, le {date_jour}
    
    SITUATION DU LITIGE : "{text}" (Catégorie: {analysis.get('category')})
    
    MISSION : Rédige une lettre de réclamation FORMELLE.
    
    CONSIGNES STRICTES DE MISE EN PAGE :
    1. En haut à gauche : Mets les coordonnées COMPLÈTES du client (Nom, adresse, tel, mail).
    2. En haut à droite : "Fait à {user_infos['ville']}, le {date_jour}".
    3. Objet : Clair et précis.
    4. Corps de la lettre : Juridique, ferme, exigeant un remboursement/action.
    5. Signature : Signe avec le NOM du client (pas "Le Client", mais le vrai nom fourni).
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur de rédaction."

# --- 5. INTERFACE ---

# --- BARRE LATÉRALE (PROFIL UTILISATEUR) ---
with st.sidebar:
    st.title("👤 Mon Dossier")
    st.info("Remplissez vos infos une fois, la lettre se remplira toute seule !")
    
    # Champs pour le profil
    nom_client = st.text_input("Nom & Prénom", placeholder="Jean Dupont")
    adresse_client = st.text_input("Adresse", placeholder="10 rue de la Paix")
    ville_client = st.text_input("Code Postal & Ville", value="75000 Paris")
    tel_client = st.text_input("Téléphone", placeholder="06 00 00 00 00")
    # On demande l'email du client pour la signature (pas pour l'envoi technique)
    email_client_visuel = st.text_input("Votre Email", placeholder="jean@gmail.com")
    
    st.markdown("---")
    st.caption("© 2026 JustiBot")

# PAGE PRINCIPALE
st.title("⚖️ Assistant de Réclamation Automatisé")
st.markdown("#### *Obtenez réparation sans effort.*")
st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1. Le Problème")
    message = st.text_area("Racontez votre litige :", height=180, placeholder="Ex: Colis jamais reçu, vendeur refuse le remboursement...")

with col2:
    st.subheader("2. Le Destinataire")
    email_destinataire = st.text_input("Email du SAV (Adversaire) :", placeholder="sav@vendeur.com")
    
    st.write("") 
    st.write("") 
    
    # Vérification que le profil est rempli
    if st.button("Rédiger la lettre ✍️", type="primary"):
        if message and email_destinataire and nom_client and ville_client:
            
            # On stocke les infos dans un dictionnaire
            user_infos = {
                "nom": nom_client,
                "adresse": adresse_client,
                "ville": ville_client,
                "tel": tel_client,
                "email_user": email_client_visuel
            }
            
            with st.spinner("L'IA génère votre lettre personnalisée..."):
                infos = analyser(message)
                lettre = generer_reclamation_offensive(message, infos, user_infos)
                st.session_state['lettre_prete'] = lettre
                st.session_state['infos_pretes'] = infos
                st.session_state['etape'] = 2
        else:
            st.error("⚠️ Merci de remplir votre PROFIL (à gauche) et le PROBLÈME.")

# RESULTAT
if 'etape' in st.session_state and st.session_state['etape'] == 2:
    st.divider()
    
    with st.expander("📊 Analyse (cliquer pour voir)", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Motif", st.session_state['infos_pretes'].get('category'))
        c2.metric("Stratégie", "Mise en demeure")

    st.subheader("3. Validation et Envoi")
    
    col_text, col_send = st.columns([3, 1])
    
    with col_text:
        texte_final = st.text_area("Votre courrier (Modifiable) :", value=st.session_state['lettre_prete'], height=500)
        sujet_final = st.text_input("Objet du mail :", value=f"RÉCLAMATION - {st.session_state['infos_pretes'].get('category')}")
    
    with col_send:
        st.info("Tout est parfait ?")
        if st.button("🚀 ENVOYER MAINTENANT"):
            with st.spinner("Envoi en cours..."):
                succes, msg = envoyer_mail_reel(email_destinataire, sujet_final, texte_final)
                if succes:
                    st.balloons()
                    st.success(msg)
                else:
                    st.error(msg)
