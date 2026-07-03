import ollama
import lancedb
import warnings

# On masque les avertissements inutiles pour garder une console propre
warnings.filterwarnings("ignore")

# --- CONFIGURATION DE TES MODÈLES OLLAMA ---
EMBEDDING_MODEL = "tazarov/all-minilm-l6-v2-f32:latest" # Ton modèle de 91 MB pour vectoriser
GENERATION_MODEL = "gemma4:12b" # Ton modèle de 7.6 GB pour réfléchir et rédiger

# 1. NOS FAUX DOCUMENTS LOCAUX (Le test)
documents = [
    {"fichier": "C:/Documents/budget_mourafiq.txt", "texte": "Le budget total alloué au projet MOURAFIQ pour 2026 est de 150 000 euros, financé par la région. 50 000 euros sont dédiés au développement logiciel."},
    {"fichier": "C:/Bureau/planning_equipe.txt", "texte": "Pour le projet MOURAFIQ, l'équipe de développement doit livrer la première version de l'application iOS avant le 15 novembre. Le backend Rust doit être prêt le 1er octobre."},
    {"fichier": "C:/Telechargements/recette_crepes.txt", "texte": "Pour faire des crêpes, il faut 250g de farine, 4 oeufs et un demi-litre de lait."}
]

print("🧠 1. Création de la mémoire vectorielle locale...")
db = lancedb.connect("./base_memoire_locale") # Création de la base de données invisible

# Fonction pour demander à Ollama de transformer du texte en vecteur
def get_vector(text):
    response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
    return response["embedding"]

# On prépare les données pour la base
data = []
for doc in documents:
    print(f"   -> Lecture et vectorisation de : {doc['fichier']}")
    vecteur = get_vector(doc["texte"])
    data.append({"vector": vecteur, "texte": doc["texte"], "fichier": doc["fichier"]})

# On crée la table (on l'écrase si on relance le script)
try:
    db.drop_table("mes_fichiers")
except:
    pass
table = db.create_table("mes_fichiers", data=data)

print("\n🎯 2. L'UTILISATEUR POSE SA QUESTION (Simulation du widget flottant)...")
question = "Fais moi une slide rapide sur le point financier du projet Mourafiq"
print(f"Demande : '{question}'")

# Le système vectorise la question pour trouver les documents mathématiquement proches
vecteur_question = get_vector(question)

# Recherche Sémantique Instantanée (On demande le document le plus pertinent)
resultats = table.search(vecteur_question).limit(1).to_list()
contexte_trouve = resultats[0]['texte']
fichier_source = resultats[0]['fichier']

print(f"\n🔍 Document trouvé par l'IA (sans utiliser le nom du fichier) : {fichier_source}")
print(f"   Extrait injecté : {contexte_trouve}")

print(f"\n✍️ 3. RÉFLEXION DU GROS MODÈLE ({GENERATION_MODEL}) EN COURS...")
# On passe l'extrait trouvé au modèle Gemma4 pour qu'il rédige la réponse finale
prompt_ia = f"""
Tu es l'agent système intelligent de la machine.
Rédige le contenu pour une diapositive PowerPoint (avec des tirets) en te basant STRICTEMENT sur le contexte fourni. 
Ne rajoute pas de fausses informations. Sois concis.

Contexte local trouvé sur la machine :
{contexte_trouve}

Demande de l'utilisateur :
{question}
"""

reponse = ollama.generate(model=GENERATION_MODEL, prompt=prompt_ia)

print("\n==================================================")
print("             🚀 RÉSULTAT FINAL (À AFFICHER)        ")
print("==================================================")
print(reponse['response'])
print("==================================================")