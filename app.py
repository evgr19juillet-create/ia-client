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

# --- 2. VERROUILLAGE VISUEL (STYLE) ---
st.markdown("""
<style>
    /* Cache le bouton 'Deploy' et le menu Hamburger */
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Style des boutons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
        background-color: #FF4B4B;
        color: white;
    }
    
    /* Style global */
    h1 { color: #0e1117; text-align: center; }
    .stTextArea textarea { font-size: 16px; }
    [data-testid="stMetricValue"] { font-size: 24px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. GESTION DES SECRETS (CLÉS) ---
try:
    # Essaie de récupérer depuis Streamlit Cloud
    api_key = st.secrets["GEMINI_KEY"]
    user_email = st.secrets["EMAIL_ADDRESS"]
    user_password = st.secrets["EMAIL_PASSWORD"]
except:
    # Sinon essaie depuis les variables d'environnement (local)
    api_key = os.getenv("GEMINI_KEY")
    user_email = os.getenv("EMAIL_ADDRESS")
    user_password = os.getenv("EMAIL_PASSWORD")

if not api_key:
    st.error("⚠️ Erreur de configuration : Clé API manquante.")
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
        # Configuration pour Hostinger
        server = smtplib.SMTP('smtp.hostinger.com', 587) 
        server.starttls()
        server.login(user_email, user_password)
        server.send_message(msg)
        server.quit()
        return True, "✅ Dossier transmis juridiquement !"
    except Exception as e:
        return False, f"Erreur d'envoi : {str(e)}"

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
    model_name = trouver_modele_disponible()
    model = genai.GenerativeModel(model_name)
    try:
        response = model.generate_content(f"Analyse ce problème en JSON strictement au format {{'category': '...', 'summary': '...'}}. Contexte : {text}")
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except:
        return {"category": "Litige commercial", "summary": "Réclamation client"}

def generer_reclamation_offensive(text, analysis, user_infos):
    model_name = trouver_modele_disponible()
    model = genai.GenerativeModel(model_name)
    date_jour = datetime.now().strftime("%d/%m/%Y")
    
    profil_client = f"""
    Nom : {user_infos['nom']}
    Adresse : {user_infos['adresse']}
    Code Postal / Ville : {user_infos['ville']}
    Téléphone : {user_infos['tel']}
    Email : {user_infos['email_user']}
    """
    
    prompt = f"""
    Tu es un expert en médiation (NON AVOCAT).
    INFORMATIONS CLIENT : {profil_client}
    DATE : {date_jour}
    SITUATION : "{text}" (Catégorie: {analysis.get('category')})
    
    MISSION : Rédige une lettre de réclamation FORMELLE.
    
    RÈGLES :
    1. En-tête gauche : Coordonnées complètes du client.
    2. En-tête droite : "Fait à {user_infos['ville']}, le {date_jour}".
    3. Objet : Clair et menaçant (juridiquement).
    4. Corps : Cite les articles de loi (Code de la consommation/Code Civil) adaptés à la situation.
    5. Exige une réponse sous 8 jours.
    6. Signature : Uniquement le Nom du client.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur de génération du courrier."

# --- 5. INTERFACE UTILISATEUR ---

# SIDEBAR (PROFIL)
with st.sidebar:
    st.title("👤 Mon Dossier")
    st.info("Vos données servent uniquement à rédiger le courrier.")
    
    nom_client = st.text_input("Nom & Prénom", placeholder="Jean Dupont")
    adresse_client = st.text_input("Adresse", placeholder="10 rue de la Liberté")
    ville_client = st.text_input("Code Postal & Ville", value="75000 Paris")
    tel_client = st.text_input("Téléphone", placeholder="06 00 00 00 00")
    email_client_visuel = st.text_input("Votre Email (pour la signature)", placeholder="jean@email.com")
    
    st.markdown("---")
    st.caption("🔒 Données sécurisées & non conservées.")
    st.caption("© 2026 JustiBot France")

# MAIN PAGE
st.title("⚖️ Justi-Bot : Votre Assistant Juridique")
st.markdown("#### *Faites valoir vos droits. L'IA rédige et envoie votre mise en demeure.*")
st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1. Le Litige")
    message = st.text_area("Expliquez la situation :", height=200, placeholder="Exemple : J'ai acheté un téléphone le 10 janvier, il ne marche plus et le vendeur refuse la garantie...")

with col2:
    st.subheader("2. La Cible")
    email_destinataire = st.text_input("Email du SAV adverse :", placeholder="sav@entreprise.com")
    st.write("")
    
    # BOUTON PRINCIPAL
    if st.button("Générer la Procédure ⚡", type="primary"):
        if message and email_destinataire and nom_client and ville_client:
            user_infos = {
                "nom": nom_client,
                "adresse": adresse_client,
                "ville": ville_client,
                "tel": tel_client,
                "email_user": email_client_visuel
            }
            with st.spinner("Analyse juridique en cours..."):
                infos = analyser(message)
                lettre = generer_reclamation_offensive(message, infos, user_infos)
                st.session_state['lettre_prete'] = lettre
                st.session_state['infos_pretes'] = infos
                st.session_state['etape'] = 2
        else:
            st.error("⚠️ Veuillez remplir votre Profil (à gauche) et le Problème.")

# ÉTAPE DE VALIDATION
if 'etape' in st.session_state and st.session_state['etape'] == 2:
    st.divider()
    st.success("✅ Analyse terminée. Votre courrier est prêt.")
    
    with st.expander("Voir l'analyse juridique (Détails)", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Qualification", st.session_state['infos_pretes'].get('category', 'Non classé'))
        c2.metric("Procédure", "Mise en demeure (Art. 1344 C.Civil)")

    st.subheader("3. Vérification et Envoi")
    
    col_text, col_send = st.columns([3, 1])
    
    with col_text:
        texte_final = st.text_area("Courrier officiel :", value=st.session_state['lettre_prete'], height=550)
        category = st.session_state['infos_pretes'].get('category', 'Litige')
        sujet_final = st.text_input("Objet du mail :", value=f"MISE EN DEMEURE - Dossier {category}")
    
    with col_send:
        st.warning("⚠️ Action irréversible.")
        if st.button("🚀 ENVOYER LA MISE EN DEMEURE"):
            with st.spinner("Transmission au serveur mail sécurisé..."):
                succes, msg = envoyer_mail_reel(email_destinataire, sujet_final, texte_final)
                if succes:
                    st.balloons()
                    st.success(msg)
                else:
                    st.error(msg)
