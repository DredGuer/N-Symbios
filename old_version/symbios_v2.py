import os
import ollama
import lancedb
import warnings
import re

warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
# We will use the nomic model, but feed it very carefully
EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest" 
GENERATION_MODEL = "gemma4:12b"
DOSSIER_TEST = "./mes_documents_test" 

if not os.path.exists(DOSSIER_TEST):
    print(f"⚠️ Le dossier '{DOSSIER_TEST}' n'existe pas.")
    exit()

print(f"📂 1. Analyse du dossier contrôlé : {DOSSIER_TEST}...")
documents_decoupes = [] 

# --- NEW: TEXT CLEANING ---
def clean_markdown(text):
    # Remove excessive markdown symbols that eat up tokens
    text = re.sub(r'[#*`_\[\]>]', ' ', text)
    # Collapse multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# --- NEW: ULTRA-SAFE CHUNKING ---
# 50 words is practically guaranteed to fit within any local model's context limit
def decouper_texte(texte, taille_max=50):
    mots = texte.split()
    morceaux = []
    for i in range(0, len(mots), taille_max):
        morceau = " ".join(mots[i:i + taille_max])
        # Only add chunks that actually have some content
        if len(morceau.strip()) > 10: 
            morceaux.append(morceau)
    return morceaux

tous_les_fichiers = os.listdir(DOSSIER_TEST)

for nom_fichier in tous_les_fichiers:
    if nom_fichier.lower().endswith((".txt", ".md")):
        chemin_complet = os.path.join(DOSSIER_TEST, nom_fichier)
        print(f"   ✅ Lecture de : {nom_fichier}")
        
        with open(chemin_complet, 'r', encoding='utf-8') as fichier:
            contenu_brut = fichier.read()
            contenu_propre = clean_markdown(contenu_brut)
            morceaux = decouper_texte(contenu_propre)
            
            for index, morceau in enumerate(morceaux):
                documents_decoupes.append({
                    "fichier": nom_fichier, 
                    "texte": morceau,
                    "partie": index + 1 
                })

if not documents_decoupes:
    print(f"⚠️ Aucun fichier valide trouvé. On arrête là.")
    exit()

# 2. MÉMOIRE VECTORIELLE
print("\n🧠 2. Création de la mémoire vectorielle locale...")
db = lancedb.connect("./base_memoire_locale")

def get_vector(text):
    try:
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
        return response["embedding"]
    except Exception as e:
        # We fail silently here to keep the console clean, but we handle the 'None' below
        return None

data = []
erreurs_count = 0

for doc in documents_decoupes:
    # Print a status indicator instead of a long line for every tiny chunk
    print(".", end="", flush=True) 
    vecteur = get_vector(doc['texte'])
    if vecteur:
        data.append({"vector": vecteur, "texte": doc['texte'], "fichier": doc['fichier']})
    else:
        erreurs_count += 1

print() # New line after the dots
if erreurs_count > 0:
    print(f"⚠️ {erreurs_count} chunks ont échoué, mais on continue avec le reste.")

# --- NEW: DATABASE SAFETY CHECK ---
if len(data) == 0:
    print("❌ FATAL: Aucun texte n'a pu être vectorisé. Le modèle d'embedding refuse toutes les requêtes.")
    print("Vérifiez que le modèle est bien lancé dans Ollama ou essayez de changer EMBEDDING_MODEL pour 'tazarov/all-minilm-l6-v2-f32:latest'.")
    exit()

try:
    db.drop_table("mes_vrais_fichiers")
except:
    pass
table = db.create_table("mes_vrais_fichiers", data=data)
print(f"✅ Base de données prête ! ({len(data)} fragments indexés)")


# 3. L'INTERACTION UTILISATEUR
print("\n🎯 3. À TOI DE JOUER !")
question = input("Que veux-tu savoir sur tes fichiers ?\n> ")

print("\nRecherche sémantique en cours...")
vecteur_question = get_vector(question)

if not vecteur_question:
    print("Erreur: Impossible de vectoriser la question.")
    exit()

# We pull the top 3 results to give the LLM more context, since our chunks are now very small
resultats = table.search(vecteur_question).limit(3).to_list()

contexte_global = ""
sources_trouvees = set()

for res in resultats:
    contexte_global += f"- {res['texte']}\n"
    sources_trouvees.add(res['fichier'])

print(f"🔍 J'ai assemblé l'information à partir de : {', '.join(sources_trouvees)}")

# 4. GÉNÉRATION DE LA RÉPONSE
print(f"✍️ 4. RÉFLEXION DE {GENERATION_MODEL} EN COURS...")
prompt_ia = f"""
Tu es l'agent système N'symbios.
Réponds à la question de l'utilisateur de manière naturelle, en te basant UNIQUEMENT sur les fragments de contexte ci-dessous.
Fais une synthèse claire. Si la réponse n'est pas du tout dans le contexte, dis que tu n'as pas l'information.

Fragments trouvés sur le disque :
{contexte_global}

Question de l'utilisateur :
{question}
"""

reponse = ollama.generate(model=GENERATION_MODEL, prompt=prompt_ia)

print("\n==================================================")
print("             🚀 N'SYMBIOS RÉPOND")
print("==================================================")
print(reponse['response'])
print("==================================================")