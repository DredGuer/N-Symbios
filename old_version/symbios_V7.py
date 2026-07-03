import os
import ollama
import lancedb
import warnings
import re
import subprocess
import time

warnings.filterwarnings("ignore")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ==========================================
#         ⚙️ CONFIGURATION N'SYMBIOS V7
# ==========================================

DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 
TABLE_NAME = "fichiers_v7" # Nouvelle table pour injecter la conscience de l'arborescence
BATCH_SIZE = 500 

EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest" 
DIMENSION_MATRYOSHKA = 256 
OCR_MODEL = "deepseek-ocr:3b"

MOTEUR_REFLEXION = "OLLAMA" 
GENERATION_MODEL_OLLAMA = "gemma4:12b"
CLE_API_OPENAI = "sk-ta-cle-api" 
GENERATION_MODEL_API = "gpt-4o-mini" 

# ==========================================
#         📊 OUTILS DE TÉLÉMÉTRIE
# ==========================================

def obtenir_ram_usage():
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
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

fichiers_indexes = {}
if TABLE_NAME in db.table_names():
    table = db.open_table(TABLE_NAME)
    df_existant = table.search().select(["chemin_absolu", "date_modification"]).to_pandas()
    fichiers_indexes = dict(zip(df_existant['chemin_absolu'], df_existant['date_modification']))
    print(f"   ℹ️ {len(fichiers_indexes)} fichiers uniques détectés dans l'index existant.")
else:
    print("   ℹ️ Base V7 vierge. Création du nouvel index sémantique (Conscience des dossiers).")

print(f"\n🔍 2. Parcours du disque et détection des changements...")
fichiers_a_traiter = []
fichiers_sur_disque = set()
liste_projets = set() # NOUVEAU: Pour la cartographie auto

for racine, sous_dossiers, fichiers in os.walk(DOSSIER_CIBLE):
    # NOUVEAU : On repère les dossiers de 1er niveau (les Projets)
    chemin_relatif_racine = os.path.relpath(racine, DOSSIER_CIBLE)
    if chemin_relatif_racine != ".":
        projet_parent = chemin_relatif_racine.split(os.sep)[0]
        liste_projets.add(projet_parent)
        
    for nom_fichier in fichiers:
        if nom_fichier.startswith('.'): continue
        chemin_absolu = os.path.abspath(os.path.join(racine, nom_fichier))
        fichiers_sur_disque.add(chemin_absolu)
        
        try: mtime = os.path.getmtime(chemin_absolu)
        except: continue
            
        if chemin_absolu not in fichiers_indexes or fichiers_indexes[chemin_absolu] != mtime:
            fichiers_a_traiter.append((chemin_absolu, mtime))

if TABLE_NAME in db.table_names():
    fichiers_orphelins = set(fichiers_indexes.keys()) - fichiers_sur_disque
    if fichiers_orphelins:
        for chemin_orphelinf in fichiers_orphelins:
            table.delete(f'chemin_absolu = "{chemin_orphelinf}"')

total_nouveaux_fichiers = len(fichiers_a_traiter)

# ==========================================
#    🧠 PARSAGE, INJECTION CONTEXTUELLE & FLUX
# ==========================================

if total_nouveaux_fichiers > 0 or len(fichiers_indexes) == 0:
    print(f"\n🏭 3. Extraction et INJECTION DU CONTEXTE ({total_nouveaux_fichiers} fichiers)...")
    fragments_a_vectoriser = []
    
    # NOUVEAU : Auto-Cartographie du disque
    if len(fichiers_indexes) == 0 and liste_projets:
        map_texte = "CARTE GLOBALE DES PROJETS DE LA MACHINE : Ce dossier contient les projets suivants : " + ", ".join(liste_projets)
        fragments_a_vectoriser.append({
            "chemin_absolu": os.path.join(DOSSIER_CIBLE, "INDEX_GLOBAL_SYSTEME"),
            "date_modification": time.time(),
            "texte": map_texte
        })
        print(f"   🗺️ Carte globale des {len(liste_projets)} projets injectée dans le cerveau.")
    
    for chemin, mtime in fichiers_a_traiter:
        contenu_brut = extraire_contenu_fichier(chemin)
        if contenu_brut:
            contenu_propre = clean_texte(contenu_brut)
            morceaux = decouper_texte(contenu_propre)
            
            # NOUVEAU : Identification du projet
            chemin_rel = os.path.relpath(chemin, DOSSIER_CIBLE)
            dossier_projet = chemin_rel.split(os.sep)[0] if os.sep in chemin_rel else "Racine"
            nom_fichier = os.path.basename(chemin)
            
            for morceau in morceaux:
                # NOUVEAU : Le secret d'un RAG intelligent. On injecte l'adresse DANS le vecteur.
                texte_enrichi = f"[Projet: {dossier_projet} | Fichier: {nom_fichier}] {morceau}"
                
                fragments_a_vectoriser.append({
                    "chemin_absolu": chemin,
                    "date_modification": mtime,
                    "texte": texte_enrichi # L'IA apprendra le nom du dossier en même temps que le texte !
                })
                
    total_fragments = len(fragments_a_vectoriser)
    print(f"   🧠 {total_fragments} fragments enrichis générés.")
    
    print("\n⚡ 4. Vectorisation Matryoshka & Streaming Database...")
    batch_data = []
    fragments_traites = 0
    temps_debut = time.time()
    ram_initiale = obtenir_ram_usage()
    table = db.open_table(TABLE_NAME) if TABLE_NAME in db.table_names() else None
    fichiers_nettoyes_session = set()
    
    for doc in fragments_a_vectoriser:
        if fragments_traites % 10 == 0 or fragments_traites == total_fragments - 1:
            afficher_metriques(fragments_traites, total_fragments, temps_debut, ram_initiale)
        
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
        if len(batch_data) >= BATCH_SIZE:
            if table is None: table = db.create_table(TABLE_NAME, data=batch_data)
            else: table.add(batch_data)
            batch_data.clear() 
            
    if batch_data:
        if table is None: table = db.create_table(TABLE_NAME, data=batch_data)
        else: table.add(batch_data)
        batch_data.clear()
        
    print(f"\n\n✅ Base de données V7 (Intelligente) mise à jour !")

# ==========================================
#           🤖 INTERACTION UTILISATEUR
# ==========================================

table = db.open_table(TABLE_NAME)
print(f"\n🎯 5. À TOI DE JOUER ! (Total indexé : {len(table.to_pandas())} fragments)")
question = input("Que veux-tu savoir ou faire ?\n> ")

temps_rech_debut = time.time()
vecteur_question = get_vector_optimized(question, is_query=True)

# NOUVEAU : On passe à 15 résultats pour avoir une vue panoramique sur les différents dossiers
resultats = table.search(vecteur_question).limit(15).to_list() 
temps_rech_fin = time.time() - temps_rech_debut

print(f"🔍 Recherche foudroyante effectuée en {temps_rech_fin*1000:.2f} ms")

contexte_global = ""
chemins_trouves = set() 

for res in resultats:
    contexte_global += f"- {res['texte']}\n"
    if res['chemin_absolu'] != os.path.join(DOSSIER_CIBLE, "INDEX_GLOBAL_SYSTEME"):
        chemins_trouves.add(res['chemin_absolu']) 

print(f"✍️ Réflexion en cours ({MOTEUR_REFLEXION})...")

# NOUVEAU : Prompt strict pour obliger l'IA à citer ses sources et les projets
prompt_ia = f"""
Tu es N'symbios, l'assistant système.
Voici des fragments de la machine de l'utilisateur. Chaque fragment indique le [Projet] et le [Fichier] d'où il provient.

RÈGLES ABSOLUES :
1. Fais une synthèse intelligente en regroupant les informations par nom de Projet.
2. Si la question est globale (ex: "Quels sont mes projets ?"), liste tous les projets que tu vois dans les fragments.
3. Ne réponds QUE sur la base de ces fragments.

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
    print("\n🔗 Fichiers sources trouvés (Parcours des projets) :")
    liste_chemins = list(chemins_trouves)
    for i, chemin in enumerate(liste_chemins):
        print(f"  [{i+1}] {os.path.basename(os.path.dirname(chemin))} / {os.path.basename(chemin)}")
    
    action = input("\n👉 Veux-tu ouvrir ces fichiers ? (numéro, 'tous', ou 'n') : ")
    if action.lower() == 'tous':
        for chemin in liste_chemins:
            subprocess.run(['open', chemin])
    elif action.isdigit() and 1 <= int(action) <= len(liste_chemins):
        subprocess.run(['open', liste_chemins[int(action)-1]])