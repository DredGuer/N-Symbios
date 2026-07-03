import os
import ollama
import lancedb
import warnings
import re
import subprocess
import time

warnings.filterwarnings("ignore")

# Essayer d'importer psutil pour la télémétrie de la RAM, sinon fallback gracieux
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ==========================================
#         ⚙️ CONFIGURATION N'SYMBIOS V6
# ==========================================

DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 
TABLE_NAME = "fichiers_v6"
BATCH_SIZE = 500 # Écriture par paquets de 500 pour stabiliser la RAM

# Moteurs locaux
EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest" 
DIMENSION_MATRYOSHKA = 256 
OCR_MODEL = "deepseek-ocr:3b"

# Moteur de réflexion
MOTEUR_REFLEXION = "OLLAMA" # Ou "API"
GENERATION_MODEL_OLLAMA = "gemma4:12b"
CLE_API_OPENAI = "sk-ta-cle-api" 
GENERATION_MODEL_API = "gpt-4o-mini" 

# ==========================================
#         📊 OUTILS DE TÉLÉMÉTRIE
# ==========================================

def obtenir_ram_usage():
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024) # En Mo
    return 0.0

def afficher_metriques(fragments_traites, total_fragments, temps_debut, ram_initiale):
    temps_ecoule = time.time() - temps_debut
    ram_actuelle = obtenir_ram_usage()
    delta_ram = ram_actuelle - ram_initiale
    
    vitesse = fragments_traites / temps_ecoule if temps_ecoule > 0 else 0
    fragments_restants = total_fragments - fragments_traites
    temps_restant_estime = fragments_restants / vitesse if vitesse > 0 else 0
    
    print(f"\r   ⏳ [{fragments_traites}/{total_fragments}] "
          f"| Vitesse: {vitesse:.1f} frag/s "
          f"| RAM: {ram_actuelle:.1f} Mo ({'+' if delta_ram >= 0 else ''}{delta_ram:.1f} Mo) "
          f"| Est. restant: {temps_restant_estime:.0f}s", end="", flush=True)

# ==========================================
#       🏭 OUTILS DE TEXTE & PARSAGE
# ==========================================

def clean_texte(text):
    text = re.sub(r'[#*`_\[\]>]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

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
            import fitz
            texte_pdf = ""
            doc = fitz.open(chemin_absolu)
            for page in doc:
                texte_pdf += page.get_text() + "\n"
            return texte_pdf
        except: return ""
    elif extension in ['jpg', 'jpeg', 'png']:
        try:
            res = ollama.generate(model=OCR_MODEL, prompt="Extrais le texte.", images=[chemin_absolu])
            return res['response']
        except: return ""
    return ""

def get_vector_optimized(text, is_query=False):
    prefix = "search_query: " if is_query else "search_document: "
    try:
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=prefix + text)
        return response["embedding"][:DIMENSION_MATRYOSHKA] 
    except:
        return None

# ==========================================
#    🔄 ANALYSE ET COMPARAISON INCRÉMENTALE
# ==========================================

print(f"📂 1. Connexion à la base locale et analyse de l'existant...")
db = lancedb.connect("./base_memoire_locale")

# Chargement de la cartographie des fichiers déjà indexés
fichiers_indexes = {}
if TABLE_NAME in db.table_names():
    table = db.open_table(TABLE_NAME)
    # On extrait uniquement les métadonnées pour économiser la RAM
    df_existant = table.search().select(["chemin_absolu", "date_modification"]).to_pandas()
    # On crée un dictionnaire {chemin: date_modif} unique
    fichiers_indexes = dict(zip(df_existant['chemin_absolu'], df_existant['date_modification']))
    print(f"   ℹ️ {len(fichiers_indexes)} fichiers uniques détectés dans l'index existant.")
else:
    print("   ℹ️ Aucune base de données existante détectée. Création d'un nouvel index général.")

print(f"\n🔍 2. Parcours du disque et détection des changements...")
fichiers_a_traiter = []
fichiers_sur_disque = set()

for racine, _, fichiers in os.walk(DOSSIER_CIBLE):
    for nom_fichier in fichiers:
        if nom_fichier.startswith('.'): continue
        chemin_absolu = os.path.abspath(os.path.join(racine, nom_fichier))
        fichiers_sur_disque.add(chemin_absolu)
        
        try:
            mtime = os.path.getmtime(chemin_absolu)
        except:
            continue
            
        # RÈGLE INCRÉMENTALE : On ne traite que si nouveau ou modifié
        if chemin_absolu not in fichiers_indexes or fichiers_indexes[chemin_absolu] != mtime:
            fichiers_a_traiter.append((chemin_absolu, mtime))

# Nettoyage des fichiers supprimés du disque
if TABLE_NAME in db.table_names():
    fichiers_orphelins = set(fichiers_indexes.keys()) - fichiers_sur_disque
    if fichiers_orphelins:
        print(f"   🗑️ Suppression de {len(fichiers_orphelins)} fichiers supprimés du disque dans l'index...")
        for chemin_orphelinf in fichiers_orphelins:
            table.delete(f'chemin_absolu = "{chemin_orphelinf}"')

total_nouveaux_fichiers = len(fichiers_a_traiter)
if total_nouveaux_fichiers == 0:
    print("   ✅ Tout est à jour ! Aucun nouveau fichier ou modification détectée.")
else:
    print(f"   🚀 {total_nouveaux_fichiers} fichiers modifiés ou nouveaux à indexer.")

# ==========================================
#    🧠 PARSAGE ET VECTORISATION PAR FLUX
# ==========================================

if total_nouveaux_fichiers > 0:
    print("\n🏭 3. Extraction du texte des nouveaux fichiers...")
    fragments_a_vectoriser = []
    
    for chemin, mtime in fichiers_a_traiter:
        contenu_brut = extraire_contenu_fichier(chemin)
        if contenu_brut:
            contenu_propre = clean_texte(contenu_brut)
            morceaux = decouper_texte(contenu_propre)
            for morceau in morceaux:
                fragments_a_vectoriser.append({
                    "chemin_absolu": chemin,
                    "date_modification": mtime,
                    "texte": morceau
                })
                
    total_fragments = len(fragments_a_vectoriser)
    print(f"   🧠 {total_fragments} nouveaux fragments générés à vectoriser.")
    
    # ÉCRITURE EN STREAMING PAR BATCHS (ZÉRO EXPLOSION DE RAM)
    print("\n⚡ 4. Vectorisation Matryoshka & Streaming Database...")
    batch_data = []
    fragments_traites = 0
    temps_debut = time.time()
    ram_initiale = obtenir_ram_usage()
    
    # Si la table existe déjà, on l'ouvre, sinon on la créera au premier batch
    table = db.open_table(TABLE_NAME) if TABLE_NAME in db.table_names() else None
    
    # Dictionnaire pour suivre les fichiers nettoyés pendant cette session
    fichiers_nettoyes_session = set()
    
    for doc in fragments_a_vectoriser:
        # Télémétrie avant traitement
        afficher_metriques(fragments_traites, total_fragments, temps_debut, ram_initiale)
        
        # Sécurité : Si le fichier existait sous une ancienne version, on supprime ses vieux fragments
        # une seule fois au moment où on injecte la nouvelle version
        if table and doc['chemin_absolu'] in fichiers_indexes and doc['chemin_absolu'] not in fichiers_nettoyes_session:
            table.delete(f'chemin_absolu = "{doc["chemin_absolu"]}"')
            fichiers_nettoyes_session.add(doc['chemin_absolu'])
            
        vecteur = get_vector_optimized(doc['texte'], is_query=False)
        if vecteur:
            batch_data.append({
                "vector": vecteur,
                "texte": doc['texte'],
                "chemin_absolu": doc['chemin_absolu'],
                "date_modification": doc['date_modification']
            })
            
        fragments_traites += 1
        
        # Dès que le caddie est plein (BATCH_SIZE), on vide dans LanceDB et on purge la RAM
        if len(batch_data) >= BATCH_SIZE:
            if table is None:
                table = db.create_table(TABLE_NAME, data=batch_data)
            else:
                table.add(batch_data)
            batch_data.clear() # Libération immédiate de la mémoire vive !
            
    # Traitement du dernier paquet restant
    if batch_data:
        if table is None:
            table = db.create_table(TABLE_NAME, data=batch_data)
        else:
            table.add(batch_data)
        batch_data.clear()
        
    afficher_metriques(total_fragments, total_fragments, temps_debut, ram_initiale)
    print(f"\n\n✅ Base de données incrémentale mise à jour avec succès !")

# ==========================================
#           🤖 INTERACTION UTILISATEUR
# ==========================================

table = db.open_table(TABLE_NAME)
print(f"\n🎯 5. À TOI DE JOUER ! (Total indexé : {len(table.to_pandas())} fragments)")
question = input("Que veux-tu savoir ou faire ?\n> ")

temps_rech_debut = time.time()
vecteur_question = get_vector_optimized(question, is_query=True)
resultats = table.search(vecteur_question).limit(5).to_list() 
temps_rech_fin = time.time() - temps_rech_debut

print(f"🔍 Recherche foudroyante effectuée en {temps_rech_fin*1000:.2f} ms")

contexte_global = ""
chemins_trouves = set() 

for res in resultats:
    contexte_global += f"- {res['texte']}\n"
    chemins_trouves.add(res['chemin_absolu']) 

print(f"✍️ Réflexion en cours ({MOTEUR_REFLEXION})...")
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
