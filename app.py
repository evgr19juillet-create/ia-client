import streamlit as st
import google.generativeai as genai
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_KEY"]
    user_email = st.secrets["EMAIL_ADDRESS"]
    user_password = st.secrets["EMAIL_PASSWORD"]
except:
    # Mode secours
    api_key = os.getenv("GEMINI_KEY")
    user_email = os.getenv("EMAIL_ADDRESS")
    user_password = os.getenv("EMAIL_PASSWORD")

if not api_key:
    st.error("⚠️ Clé Gemini manquante.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. FONCTIONS MAIL ---
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
        return True, "✅ Réclamation envoyée ! Surveillez votre compte bancaire."
    except Exception as e:
        return False, f"Erreur d'envoi : {str(e)}"

# --- 3. CERVEAU IA (Mode Négociateur) ---
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
        return {"category": "Litige Produit", "summary": "Problème commande"}

def generer_reclamation_offensive(text, analysis):
    model = genai.GenerativeModel(trouver_modele_disponible())
    
    # C'est ici que tout se joue : on force la demande de dédommagement
    prompt = f"""
    Tu es un expert en droit de la consommation spécialisé dans l'obtention de dédommagements.
    
    SITUATION DU CLIENT : "{text}"
    CATÉGORIE : {analysis.get('category')}
    
    MISSION IMPÉRATIVE :
    Rédige un email de réclamation pour exiger un REMBOURSEMENT ou une INDEMNITÉ pour CHAQUE produit défectueux ou en retard cité.
    
    RÈGLES D'OR :
    1. Ne demande pas "si c'est possible". EXIGE une réparation financière immédiate.
    2. Cite le Code de la Consommation ou l'obligation de résultat du vendeur pour mettre la pression.
    3. Ton : Froid, factuel, juridique et déterminé.
    4. Pas de [crochets]. Le texte doit être prêt à partir.
    5. Menace poliment de signaler le cas aux associations de consommateurs si rien n'est fait sous 48h.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur de rédaction."

# --- 4. INTERFACE ---
st.set_page_config(page_title="Chasseur de Remboursement", page_icon="💰")
st.title("💰 Chasseur de Remboursement")
st.caption("Cette IA analyse chaque produit acheté et exige un dédommagement pour le moindre défaut.")

col_gauche, col_droite = st.columns(2)
with col_gauche:
    message = st.text_area("Listez les problèmes (ex: TV cassée + Livraison retard 3 jours) :", height=150)
with col_droite:
    email_destinataire = st.text_input("Email du SAV :", placeholder="sav@vendeur.com")

if st.button("1. Générer la demande de remboursement 💸"):
    if message and email_destinataire:
        with st.spinner("Analyse des failles juridiques..."):
            infos = analyser(message)
            lettre = generer_reclamation_offensive(message, infos)
            
            st.session_state['lettre_prete'] = lettre
            st.session_state['infos_pretes'] = infos
            st.success("Stratégie de dédommagement prête !")
    else:
        st.error("Remplissez la description et l'email !")

# Zone de validation
if 'lettre_prete' in st.session_state:
    st.divider()
    st.subheader("📝 Vérifiez l'attaque avant envoi")
    
    texte_final = st.text_area("Courrier généré :", value=st.session_state['lettre_prete'], height=400)
    sujet_final = st.text_input("Objet :", value=f"MISE EN DEMEURE - Remboursement commande ({st.session_state['infos_pretes'].get('category')})")
    
    if st.button("2. Envoyer la réclamation maintenant 🚀", type="primary"):
        with st.spinner("Envoi en cours..."):
            succes, msg = envoyer_mail_reel(email_destinataire, sujet_final, texte_final)
            if succes:
                st.balloons()
                st.success(msg)
            else:
                st.error(msg)
