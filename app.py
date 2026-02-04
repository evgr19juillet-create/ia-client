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
    # Si les secrets ne sont pas trouvés, on arrête tout
    st.error("⚠️ Il manque les clés dans les Secrets (GEMINI_KEY, EMAIL_ADDRESS ou EMAIL_PASSWORD).")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. FONCTIONS MAIL ---
def envoyer_mail_reel(destinataire, sujet, corps):
    """Connecte l'IA au serveur Gmail pour envoyer le mail"""
    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(corps, 'plain'))

    try:
        # Connexion sécurisée à Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # On utilise le mot de passe d'application (celui de 16 lettres)
        server.login(user_email, user_password)
        server.send_message(msg)
        server.quit()
        return True, "Email envoyé avec succès ! 🚀 (Vérifiez vos 'Messages envoyés')"
    except Exception as e:
        return False, f"Erreur d'envoi : {str(e)}"

# --- 3. CERVEAU IA ---
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
        response = model.generate_content(f"Analyse ce litige en JSON (category, summary). Contexte : {text}")
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return {"category": "Réclamation", "summary": "Litige client"}

def generer_reclamation(text, analysis):
    model = genai.GenerativeModel(trouver_modele_disponible())
    prompt = f"""
    Agis comme un avocat expert.
    SITUATION : {text}
    CATÉGORIE : {analysis.get('category')}
    
    TÂCHE : Rédige un email de réclamation FORMEL et FERME.
    Ne mets PAS d'objets [Entre crochets]. Rédige le texte final prêt à partir.
    Signe simplement "Le Client".
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erreur de rédaction."

# --- 4. INTERFACE ---
st.set_page_config(page_title="IA Avocat Connecté", page_icon="⚖️")
st.title("⚖️ Avocat Automatique")

col_gauche, col_droite = st.columns(2)
with col_gauche:
    message = st.text_area("Expliquez le litige :", height=150, placeholder="Ex: Mon vol a été annulé sans préavis...")
with col_droite:
    # Pour tester, mettez VOTRE PROPRE ADRESSE ici au début
    email_destinataire = st.text_input("Email du destinataire :", placeholder="sav@entreprise.com")

if st.button("1. Analyser et Préparer le courrier 🕵️"):
    if message and email_destinataire:
        with st.spinner("Rédaction juridique en cours..."):
            infos = analyser(message)
            lettre = generer_reclamation(message, infos)
            
            st.session_state['lettre_prete'] = lettre
            st.session_state['infos_pretes'] = infos
            st.success("Courrier prêt ! Vérifiez ci-dessous.")
    else:
        st.error("Il faut un message et un email destinataire !")

# Zone de validation et d'envoi
if 'lettre_prete' in st.session_state:
    st.divider()
    st.subheader("📝 Vérification avant envoi")
    
    texte_final = st.text_area("Message à envoyer :", value=st.session_state['lettre_prete'], height=300)
    sujet_final = st.text_input("Objet du mail :", value=f"Réclamation officielle : {st.session_state['infos_pretes'].get('category')}")
    
    # BOUTON DÉCLENCHEUR
    if st.button("2. Envoyer le mail maintenant 🚀", type="primary"):
        with st.spinner("Connexion à votre Gmail..."):
            succes, msg = envoyer_mail_reel(email_destinataire, sujet_final, texte_final)
            if succes:
                st.balloons()
                st.success(msg)
            else:
                st.error(msg)
