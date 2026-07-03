import os
import ollama
import lancedb
import warnings
import re
import subprocess # Le module pour interagir avec le système d'exploitation macOS

warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest" 
GENERATION_MODEL = "gemma4:12b"
# 👇 TU PEUX METTRE UN DOSSIER PLUS GROS ICI (ex: "/Users/dredguer/Documents/Notes")
DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 

print(f"📂 1. Analyse et Indexation du dossier : {os.path.abspath(DOSSIER_CIBLE)}")

def clean_markdown(text):
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

documents_decoupes = [] 

# On utilise os.walk pour fouiller dans les SOUS-DOSSIERS aussi (Scale-up !)
for racine, sous_dossiers, fichiers in os.walk(DOSSIER_CIBLE):
    for nom_fichier in fichiers:
        if nom_fichier.lower().endswith((".txt", ".md")):
            chemin_absolu = os.path.abspath(os.path.join(racine, nom_fichier))
            
            with open(chemin_absolu, 'r', encoding='utf-8', errors='ignore') as fichier:
                contenu_propre = clean_markdown(fichier.read())
                morceaux = decouper_texte(contenu_propre)
                
                for index, morceau in enumerate(morceaux):
                    documents_decoupes.append({
                        "nom_fichier": nom_fichier,
                        "chemin_absolu": chemin_absolu, # 🔗 On garde le VRAI lien
                        "texte": morceau
                    })

# 2. MÉMOIRE VECTORIELLE
db = lancedb.connect("./base_memoire_locale")

def get_vector(text):
    try:
        return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)["embedding"]
    except:
        return None

data = []
print("🧠 2. Vectorisation en cours (cela peut prendre du temps sur de gros dossiers)...")
for doc in documents_decoupes:
    vecteur = get_vector(doc['texte'])
    if vecteur:
        data.append({"vector": vecteur, "texte": doc['texte'], "chemin_absolu": doc['chemin_absolu']})

if not data:
    print("❌ Aucun fichier indexé.")
    exit()

try:
    db.drop_table("fichiers_v3")
except:
    pass
table = db.create_table("fichiers_v3", data=data)
print(f"✅ Base de données prête ! ({len(data)} fragments indexés)")


# 3. L'INTERACTION UTILISATEUR
print("\n🎯 3. À TOI DE JOUER !")
question = input("Que veux-tu savoir ou faire ?\n> ")

vecteur_question = get_vector(question)
# On récupère les 5 meilleurs fragments pour réduire le taux d'erreur à 0
resultats = table.search(vecteur_question).limit(5).to_list() 

contexte_global = ""
chemins_trouves = set() # On utilise un Set pour éviter les doublons de chemins

for res in resultats:
    contexte_global += f"- {res['texte']}\n"
    chemins_trouves.add(res['chemin_absolu']) # On stocke les liens directs

# 4. GÉNÉRATION DE LA RÉPONSE (Zéro Hallucination)
print(f"\n✍️ 4. RÉFLEXION DE {GENERATION_MODEL} EN COURS...")
prompt_ia = f"""
Tu es N'symbios, l'assistant système local du Mac de l'utilisateur.
Réponds à la question en te basant STRICTEMENT ET UNIQUEMENT sur les fragments ci-dessous.
Si la réponse n'est pas dans les fragments, réponds EXACTEMENT : "Je n'ai pas trouvé l'information dans tes fichiers locaux." Ne brode pas.

Fragments trouvés :
{contexte_global}

Question :
{question}
"""

reponse = ollama.generate(model=GENERATION_MODEL, prompt=prompt_ia)

print("\n==================================================")
print("             🚀 N'SYMBIOS RÉPOND")
print("==================================================")
print(reponse['response'])
print("==================================================")

# --- 5. L'ACTION NATIVE OS (LA NOUVEAUTÉ) ---
if chemins_trouves:
    print("\n🔗 Liens directs des fichiers sources utilisés :")
    liste_chemins = list(chemins_trouves)
    for i, chemin in enumerate(liste_chemins):
        print(f"  [{i+1}] {chemin}")
    
    action = input("\n👉 Veux-tu que j'ouvre un ou plusieurs de ces fichiers ? (Tape le numéro, 'tous', ou 'n' pour non) : ")
    
    if action.lower() == 'tous':
        for chemin in liste_chemins:
            # Commande native macOS pour ouvrir un fichier avec son application par défaut
            subprocess.run(['open', chemin])
        print("✅ Fichiers ouverts sur ton Mac !")
    elif action.isdigit() and 1 <= int(action) <= len(liste_chemins):
        chemin_a_ouvrir = liste_chemins[int(action)-1]
        subprocess.run(['open', chemin_a_ouvrir])
        print(f"✅ Fichier ouvert : {chemin_a_ouvrir}")
    else:
        print("Opération terminée.")