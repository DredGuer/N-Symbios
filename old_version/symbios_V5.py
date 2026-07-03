import os
import ollama
import lancedb
import warnings
import re
import subprocess

warnings.filterwarnings("ignore")

# ==========================================
#         ⚙️ CONFIGURATION N'SYMBIOS
# ==========================================

# ⚠️ Modifie cette cible avec le dossier de ton choix
DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 

# 1. MOTEUR DE MÉMOIRE (Nomic optimisé)
EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest" 
DIMENSION_MATRYOSHKA = 256 # Réduction par 3 du poids de la base !
OCR_MODEL = "deepseek-ocr:3b"

# 2. MOTEUR DE RÉFLEXION
MOTEUR_REFLEXION = "OLLAMA" # Ou "API"
GENERATION_MODEL_OLLAMA = "gemma4:12b"
CLE_API_OPENAI = "sk-ta-cle-api" 
GENERATION_MODEL_API = "gpt-4o-mini" 

# ==========================================
#       🏭 L'USINE DE PRÉTRAITEMENT 
# ==========================================

print(f"📂 1. Analyse et extraction : {os.path.abspath(DOSSIER_CIBLE)}")

def clean_texte(text):
    text = re.sub(r'[#*`_\[\]>]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

# Découpage à 120 mots max pour respecter la limite des 512 tokens de Nomic
def decouper_texte(texte, taille_max=120):
    mots = texte.split()
    morceaux = []
    for i in range(0, len(mots), taille_max):
        morceau = " ".join(mots[i:i + taille_max])
        if len(morceau.strip()) > 10: 
            morceaux.append(morceau)
    return morceaux

def extraire_contenu_fichier(chemin_absolu):
    extension = chemin_absolu.lower().split('.')[-1]
    
    if extension in ['txt', 'md', 'csv', 'json', 'py', 'js', 'html']:
        try:
            with open(chemin_absolu, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except: return ""
        
    elif extension == 'pdf':
        try:
            import fitz # PyMuPDF
            texte_pdf = ""
            doc = fitz.open(chemin_absolu)
            for page in doc:
                texte_pdf += page.get_text() + "\n"
            return texte_pdf
        except Exception as e:
            return ""
            
    elif extension in ['jpg', 'jpeg', 'png']:
        try:
            res = ollama.generate(
                model=OCR_MODEL,
                prompt="Extrais le texte. S'il n'y a pas de texte clair, décris l'image.",
                images=[chemin_absolu]
            )
            return res['response']
        except Exception as e:
            return ""
            
    return ""

# ==========================================
#       🧠 INDEXATION & OPTIMISATION
# ==========================================

documents_decoupes = [] 

for racine, sous_dossiers, fichiers in os.walk(DOSSIER_CIBLE):
    for nom_fichier in fichiers:
        if nom_fichier.startswith('.'): continue
            
        chemin_absolu = os.path.abspath(os.path.join(racine, nom_fichier))
        contenu_brut = extraire_contenu_fichier(chemin_absolu)
        
        if contenu_brut:
            contenu_propre = clean_texte(contenu_brut)
            morceaux = decouper_texte(contenu_propre)
            
            for morceau in morceaux:
                documents_decoupes.append({
                    "chemin_absolu": chemin_absolu,
                    "texte": morceau
                })

db = lancedb.connect("./base_memoire_locale")

# La fonction optimisée avec Préfixes et Troncature Matryoshka
def get_vector_optimized(text, is_query=False):
    prefix = "search_query: " if is_query else "search_document: "
    try:
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=prefix + text)
        vecteur_complet = response["embedding"]
        # Optimisation foudroyante : on ne garde que les 256 premières dimensions
        return vecteur_complet[:DIMENSION_MATRYOSHKA] 
    except:
        return None

data = []
total_fragments = len(documents_decoupes)
print(f"\n🧠 2. Vectorisation Matryoshka ({total_fragments} fragments à traiter)...")

for i, doc in enumerate(documents_decoupes):
    # Compteur de progression dynamique (se met à jour sur la même ligne)
    if i % 50 == 0 or i == total_fragments - 1:
        print(f"\r   ⏳ Traitement : {i+1} / {total_fragments}", end="", flush=True)
        
    vecteur = get_vector_optimized(doc['texte'], is_query=False)
    if vecteur:
        data.append({"vector": vecteur, "texte": doc['texte'], "chemin_absolu": doc['chemin_absolu']})

if not data:
    print("\n❌ Aucun fichier n'a pu être lu ou indexé.")
    exit()

# Création (ou écrasement) propre de la table
table = db.create_table("fichiers_v5", data=data, mode="overwrite")
print(f"\n✅ Base de données prête ! ({len(data)} fragments indexés, poids réduit par 3)")

# ==========================================
#           🤖 L'INTERACTION
# ==========================================

print("\n🎯 3. À TOI DE JOUER !")
question = input("Que veux-tu savoir ou faire ?\n> ")

# On utilise le préfixe de recherche pour cibler l'information avec une précision absolue
vecteur_question = get_vector_optimized(question, is_query=True)
resultats = table.search(vecteur_question).limit(5).to_list() 

contexte_global = ""
chemins_trouves = set() 

for res in resultats:
    contexte_global += f"- {res['texte']}\n"
    chemins_trouves.add(res['chemin_absolu']) 

print(f"\n✍️ 4. RÉFLEXION EN COURS (Moteur : {MOTEUR_REFLEXION})...")
prompt_ia = f"""
Tu es N'symbios, l'assistant système du Mac.
Réponds à la question en te basant STRICTEMENT sur les fragments ci-dessous.
Si l'information n'est pas dans les fragments, dis "Je n'ai pas l'information."

Fragments trouvés :
{contexte_global}

Question :
{question}
"""

reponse_finale = ""

if MOTEUR_REFLEXION == "API":
    try:
        from openai import OpenAI
        client = OpenAI(api_key=CLE_API_OPENAI)
        res_api = client.chat.completions.create(
            model=GENERATION_MODEL_API,
            messages=[{"role": "system", "content": prompt_ia}]
        )
        reponse_finale = res_api.choices[0].message.content
    except Exception as e:
        reponse_finale = f"❌ Erreur avec l'API OpenAI : {e}"
else:
    res_ollama = ollama.generate(model=GENERATION_MODEL_OLLAMA, prompt=prompt_ia)
    reponse_finale = res_ollama['response']

print("\n==================================================")
print("             🚀 N'SYMBIOS RÉPOND")
print("==================================================")
print(reponse_finale)
print("==================================================")

# ==========================================
#           ⚙️ ACTION NATIVE MAC
# ==========================================
if chemins_trouves:
    print("\n🔗 Fichiers sources trouvés :")
    liste_chemins = list(chemins_trouves)
    for i, chemin in enumerate(liste_chemins):
        print(f"  [{i+1}] {os.path.basename(chemin)}")
    
    action = input("\n👉 Veux-tu ouvrir ces fichiers ? (numéro, 'tous', ou 'n') : ")
    
    if action.lower() == 'tous':
        for chemin in liste_chemins:
            subprocess.run(['open', chemin])
    elif action.isdigit() and 1 <= int(action) <= len(liste_chemins):
        subprocess.run(['open', liste_chemins[int(action)-1]])
    else:
        print("Opération terminée.")