# --- Dans la fonction analyse_ia ---
def analyse_ia(text):
    # ON CHANGE ICI : gemini-pro -> gemini-1.5-flash
    model = genai.GenerativeModel('gemini-1.5-flash') 
    try:
        prompt = f"Analyse ce problème juridique et classe-le (ex: Remboursement, Non-livraison, Vice caché). Réponds juste par la catégorie. Contexte: {text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Litige commercial"

# --- Dans la fonction generer_courrier ---
def generer_courrier(probleme, categorie, user_infos):
    # ON CHANGE ICI AUSSI
    model = genai.GenerativeModel('gemini-1.5-flash')
    date_jour = datetime.now().strftime("%d/%m/%Y")
    
    # ... le reste du code ne change pas ...
