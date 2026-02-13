import streamlit as st
import google.generativeai as genai
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Justibots",
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

# --- 3. RÉCUPÉRATION DES SECRETS ---
try:
    api_key = st.secrets["GEMINI_KEY"]
    user_email = st.secrets["EMAIL_ADDRESS"]
    user_password = st.secrets["EMAIL_PASSWORD"]
except FileNotFoundError:
    st.error("⚠️ Les secrets (clés) ne sont pas configurés sur Streamlit Cloud.")
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
        server = smtplib.SMTP('smtp.hostinger.com', 587)
        server.starttls()
        server.login(user_email, user_password)
        server.send_message(msg)
        server.quit()
        return True, "✅ Courrier envoyé avec succès !"
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
    model = genai.GenerativeModel(trouver_modele_disponible())
    try:
        prompt = f"Analyse ce litige et renvoie un JSON {{'category': '...', 'summary': '...'}}. Contexte : {text}"
        response = model.generate_content(prompt)
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
    st.info("Remplissez vos infos et cliquez sur 'Sauvegarder' pour créer votre lien personnel.")

    # -- LOGIQUE DE RÉCUPÉRATION DES INFOS DANS L'URL --
    # On regarde si l'URL contient déjà des infos
    def get_val(key):
        return st.query_params.get(key, "")

    # On pré-remplit les champs avec ce qu'il y a dans l'URL (si ça existe)
    nom_client = st.text_input("Nom & Prénom", value=get_val("nom"))
    adresse_client = st.text_input("Adresse", value=get_val("adresse"))
    ville_client = st.text_input("Code Postal & Ville", value=get_val("ville"))
    email_client_visuel = st.text_input("Votre Email (signature)", value=get_val("email"))

    # Bouton pour sauvegarder
    if st.button("💾 Sauvegarder mon profil"):
        # On écrit les infos dans l'URL
        st.query_params["nom"] = nom_client
        st.query_params["adresse"] = adresse_client
        st.query_params["ville"] = ville_client
        st.query_params["email"] = email_client_visuel
        st.success("✅ Profil sauvegardé ! Ajoutez maintenant cette page à vos favoris ⭐ pour revenir sans rien retaper.")

    # --- SECTION DONS (STRIPE) ---
    st.write("") 
    st.write("") 
    st.divider()
    
    st.subheader("☕ Soutenir le projet")
    st.caption("L'application est 100% gratuite. Si Justibots vous aide à récupérer votre argent, un petit soutien fait toujours plaisir !")
    
    # Ton lien Stripe
    st.link_button(
        "❤️ Faire un don (CB / Apple Pay)", 
        "https://buy.stripe.com/test_cNi28rdpobCU6Pe6q5bbG00", 
        type="primary"
    )

st.title("⚖️ Justibots : Assistant Juridique")

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
                st.balloons()
                st.success(msg)
                
                # --- AJOUT DU BLOC DE DON APRÈS SUCCÈS ---
                st.markdown("---")
                st.markdown("### 👏 Mission accomplie !")
                st.info("Votre mise en demeure a été envoyée ! Si ce service vous a été utile, pensez à soutenir le développeur.")
                
                col_vide, col_btn, col_vide2 = st.columns([1, 2, 1])
                with col_btn:
                    st.link_button(
                        "🏆 Offrir un café de la victoire", 
                        "https://buy.stripe.com/test_cNi28rdpobCU6Pe6q5bbG00", 
                        type="primary",
                        use_container_width=True
                    )
                # -----------------------------------------
            else:
                st.error(msg)
c'est le code poser sur github c'est bien celui que l'on connecte ?
