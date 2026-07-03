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

DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 

# 1. MOTEUR DE MÉMOIRE (Toujours en local, c'est rapide et gratuit)
EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest" 
OCR_MODEL = "deepseek-ocr:3b" # Ton modèle visuel pour lire les images

# 2. MOTEUR DE RÉFLEXION (L'Interrupteur Local / Cloud)
MOTEUR_REFLEXION = "OLLAMA" # Remplace par "API" pour utiliser ChatGPT

# Si MOTEUR_REFLEXION = "OLLAMA"
GENERATION_MODEL_OLLAMA = "gemma4:12b"

# Si MOTEUR_REFLEXION = "API"
CLE_API_OPENAI = "sk-ta-cle-api-ici" # Mets ta vraie clé si tu utilises l'API
GENERATION_MODEL_API = "gpt-4o-mini" # Très rapide et peu coûteux

# ==========================================
#       🏭 L'USINE DE PRÉTRAITEMENT 
# ==========================================

print(f"📂 1. Analyse, extraction et Indexation du dossier : {os.path.abspath(DOSSIER_CIBLE)}")

def clean_texte(text):
    text = re.sub(r'[#*`_\[\]>]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def decouper_texte(texte, taille_max=50):
    mots = texte.split()
    morceaux = []
    for i in range(0, len(mots), taille_max):
        morceau = " ".join(mots[i:i + taille_max])
        if len(morceau.strip()) > 10: 
            morceaux.append(morceau)
    return morceaux

# --- LE ROUTEUR (Nouveau !) ---
def extraire_contenu_fichier(chemin_absolu):
    extension = chemin_absolu.lower().split('.')[-1]
    
    # 1. TEXTE & CODE
    if extension in ['txt', 'md', 'csv', 'json', 'py', 'js', 'html']:
        try:
            with open(chemin_absolu, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except: return ""
        
    # 2. PDF (Avec PyMuPDF)
    elif extension == 'pdf':
        import fitz # PyMuPDF
        texte_pdf = ""
        try:
            doc = fitz.open(chemin_absolu)
            for page in doc:
                texte_pdf += page.get_text() + "\n"
            return texte_pdf
        except Exception as e:
            print(f"\n⚠️ Erreur PDF {chemin_absolu}: {e}")
            return ""
            
    # 3. IMAGES (La tâche "Deep Sleep" testée ici en live)
    elif extension in ['jpg', 'jpeg', 'png']:
        try:
            print(" 👁️ (Lecture d'image en cours via OCR... patience)", end="", flush=True)
            res = ollama.generate(
                model=OCR_MODEL,
                prompt="Extrais le texte de cette image de manière précise. S'il n'y a pas de texte clair, décris ce que tu vois.",
                images=[chemin_absolu]
            )
            return res['response']
        except Exception as e:
            print(f"\n⚠️ Erreur OCR {chemin_absolu}: {e}")
            return ""
            
    return "" # Format non pris en charge

# ==========================================
#           🧠 INDEXATION
# ==========================================

documents_decoupes = [] 

for racine, sous_dossiers, fichiers in os.walk(DOSSIER_CIBLE):
    for nom_fichier in fichiers:
        # On ignore les fichiers cachés du Mac
        if nom_fichier.startswith('.'): continue
            
        chemin_absolu = os.path.abspath(os.path.join(racine, nom_fichier))
        contenu_brut = extraire_contenu_fichier(chemin_absolu)
        
        if contenu_brut: # Si on a réussi à extraire du texte
            contenu_propre = clean_texte(contenu_brut)
            morceaux = decouper_texte(contenu_propre)
            
            for index, morceau in enumerate(morceaux):
                documents_decoupes.append({
                    "chemin_absolu": chemin_absolu,
                    "texte": morceau
                })

db = lancedb.connect("./base_memoire_locale")

def get_vector(text):
    try: return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)["embedding"]
    except: return None

data = []
print(f"\n🧠 2. Vectorisation en cours (Conversion des {len(documents_decoupes)} fragments)...")
for doc in documents_decoupes:
    print(".", end="", flush=True) 
    vecteur = get_vector(doc['texte'])
    if vecteur:
        data.append({"vector": vecteur, "texte": doc['texte'], "chemin_absolu": doc['chemin_absolu']})

if not data:
    print("\n❌ Aucun fichier n'a pu être lu ou indexé.")
    exit()

try: db.drop_table("fichiers_v4")
except: pass
table = db.create_table("fichiers_v4", data=data)
print(f"\n✅ Base de données prête ! ({len(data)} fragments indexés)")

# ==========================================
#           🤖 L'INTERACTION
# ==========================================

print("\n🎯 3. À TOI DE JOUER !")
question = input("Que veux-tu savoir ou faire ?\n> ")

vecteur_question = get_vector(question)
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
Sois précis. Si la réponse n'est pas dans les fragments, réponds "Je n'ai pas l'information."

Fragments trouvés :
{contexte_global}

Question :
{question}
"""

reponse_finale = ""

# --- L'INTERRUPTEUR DE CERVEAU ---
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
        reponse_finale = f"❌ Erreur avec l'API OpenAI : {e}\nVérifie ta clé API !"
else:
    # On utilise Ollama par défaut
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
        print(f"  [{i+1}] {os.path.basename(chemin)}") # Affiche juste le nom du fichier pour faire plus propre
    
    action = input("\n👉 Veux-tu que j'ouvre ces fichiers ? (numéro, 'tous', ou 'n') : ")
    
    if action.lower() == 'tous':
        for chemin in liste_chemins:
            subprocess.run(['open', chemin])
    elif action.isdigit() and 1 <= int(action) <= len(liste_chemins):
        subprocess.run(['open', liste_chemins[int(action)-1]])
    else:
        print("Opération terminée.")