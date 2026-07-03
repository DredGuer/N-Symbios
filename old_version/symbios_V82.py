import os
import ollama
import lancedb
import warnings
import re
import subprocess
import time
import json
from datetime import datetime

warnings.filterwarnings("ignore")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

# ==========================================
#         ⚙️ CONFIGURATION N'SYMBIOS V8.2
# ==========================================

DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 
TABLE_NAME = "fichiers_v8" 
FICHIER_LOGS = "query_log.jsonl" 
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

def logger_requete(question, resultats_vecteurs, reponse_llm, temps_recherche):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "temps_recherche_ms": round(temps_recherche * 1000, 2),
        "top_documents": [
            {
                "fragment_id": res.get('fragment_id', 'Inconnu'),
                "chemin": res.get('chemin_absolu', 'Inconnu'),
                "rrf_score": res.get('rrf_score', 0.0), 
                "vector_distance": res.get('_distance', None),
                "extrait": res.get('texte', '')[:100] + "..."
            } for res in resultats_vecteurs
        ],
        "reponse_llm": reponse_llm
    }
    with open(FICHIER_LOGS, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

# ==========================================
#    🔪 MOTEUR DE CHUNKING ADAPTATIF
# ==========================================

class MarkdownAdaptiveChunker:
    def __init__(self, max_prose=200, max_code=250, min_chunk=20):
        self.max_prose = max_prose
        self.max_code = max_code
        self.min_chunk = min_chunk

    def chunk_document(self, projet, nom_fichier, markdown_text):
        chunks_finaux = []
        sections = re.split(r'(?m)^(#+\s+.*)\n', markdown_text)
        
        if sections[0].strip():
            chunks_finaux.extend(self._process_section("Introduction", sections[0], projet, nom_fichier))
            
        for i in range(1, len(sections), 2):
            titre_brut = sections[i].strip()
            titre_propre = titre_brut.lstrip('#').strip()
            
            contenu = sections[i+1].strip() if i+1 < len(sections) else ""
            if not contenu:
                continue
                
            chunks_finaux.extend(self._process_section(titre_propre, contenu, projet, nom_fichier))
            
        return chunks_finaux

    def _process_section(self, titre, contenu, projet, nom_fichier):
        mots_totaux = len(contenu.split())
        prefixe_contexte = f"[Projet: {projet} | Fichier: {nom_fichier} | Section: {titre}]\n"
        
        if mots_totaux <= 250:
            if mots_totaux >= self.min_chunk:
                return [prefixe_contexte + contenu]
            return [] 
            
        chunks_subdivises = []
        
        blocs_code = re.findall(r'```.*?```', contenu, re.DOTALL)
        for i, code in enumerate(blocs_code):
            contenu = contenu.replace(code, f"__BLOC_CODE_{i}__")
            
        listes = re.findall(r'(?:^[*-]\s+.*\n?)+', contenu, re.MULTILINE)
        for i, liste in enumerate(listes):
            contenu = contenu.replace(liste, f"__BLOC_LISTE_{i}__")
            
        paragraphes = contenu.split('\n\n')
        chunk_courant = ""
        
        for para in paragraphes:
            if "__BLOC_CODE_" in para:
                idx_match = re.search(r'__BLOC_CODE_(\d+)__', para)
                if idx_match:
                    idx = int(idx_match.group(1)) 
                    chunks_subdivises.append(prefixe_contexte + blocs_code[idx])
                continue
                
            if "__BLOC_LISTE_" in para:
                idx_match = re.search(r'__BLOC_LISTE_(\d+)__', para)
                if idx_match:
                    idx = int(idx_match.group(1))
                    chunks_subdivises.append(prefixe_contexte + listes[idx])
                continue
                
            if len((chunk_courant + para).split()) > self.max_prose:
                chunks_subdivises.append(prefixe_contexte + chunk_courant.strip())
                
                phrases = re.split(r'(?<=[.!?])\s+', chunk_courant.strip())
                derniere_phrase = phrases[-1] if phrases else ""
                
                chunk_courant = derniere_phrase + "\n" + para
            else:
                chunk_courant += "\n" + para
                
        if chunk_courant.strip() and len(chunk_courant.split()) >= self.min_chunk:
            chunks_subdivises.append(prefixe_contexte + chunk_courant.strip())
            
        # ==========================================
        # 🛡️ LA GUILLOTINE ABSOLUE
        # ==========================================
        MAX_CHARS = 800
        chunks_securises = []
        
        for chunk in chunks_subdivises:
            if len(chunk) > MAX_CHARS:
                taille_utile = MAX_CHARS - len(prefixe_contexte) - 15 
                if taille_utile < 100: taille_utile = 100
                
                for j in range(0, len(chunk), taille_utile):
                    morceau = chunk[j:j+taille_utile]
                    if j > 0 and not morceau.startswith("[Projet:"):
                        morceau = prefixe_contexte + "[SUITE] " + morceau
                    chunks_securises.append(morceau)
            else:
                chunks_securises.append(chunk)
                
        return chunks_securises

# ==========================================
#       🏭 OUTILS DE PARSAGE & VECTEURS
# ==========================================

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
            for page in doc: texte_pdf += page.get_text() + "\n"
            return texte_pdf
        except: return ""
    return ""

def get_vector_optimized(text, is_query=False):
    prefix = "search_query: " if is_query else "search_document: "
    try:
        safe_text = (prefix + text)[:800]
        response = ollama.embeddings(
            model=EMBEDDING_MODEL, 
            prompt=safe_text
        )
        return response["embedding"][:DIMENSION_MATRYOSHKA] 
    except Exception as e:
        print(f"\n   ⚠️ Embedding échoué (Taille: {len(text)} chars) : {e}")
        return None

# ==========================================
#    🧠 LE MOTEUR HYBRIDE DÉTERMINISTE (V8.2)
# ==========================================

def recherche_hybride(question, table, bm25, corpus_textes, corpus_chemins, corpus_ids, top_n=10):
    # 1. Recherche Vectorielle (Sens)
    vecteur = get_vector_optimized(question, is_query=True)
    res_vector = table.search(vecteur).limit(50).to_list() if vecteur else []
    
    # 2. Recherche Lexicale (Mot-clé exact)
    tokenized_query = re.findall(r'\w+', question.lower())
    bm25_scores = bm25.get_scores(tokenized_query)
    top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:50]
    
    # 3. Fusion Mathématique RRF Déterministe
    rrf_scores = {}
    docs_metadata = {}
    k = 60 
    
    # Intégration des rangs sémantiques (LanceDB)
    for rank, res in enumerate(res_vector):
        # 🔴 CORRECTION : Extraction de l'ID stable au lieu du vieux hash(texte)
        doc_id = res.get('fragment_id', str(hash(res['texte'])))
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        docs_metadata[doc_id] = res
        
    # Intégration des rangs lexicaux (BM25)
    for rank, idx in enumerate(top_bm25_indices):
        # 🔴 CORRECTION : Alignement déterministe par l'index du corpus persistant
        doc_id = corpus_ids[idx]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        
        if doc_id not in docs_metadata:
            docs_metadata[doc_id] = {
                "fragment_id": doc_id,
                "texte": corpus_textes[idx],
                "chemin_absolu": corpus_chemins[idx],
                "_distance": None # 🟡 CORRECTION : Sentinelle None explicite au lieu de 0.0
            }
            
    top_docs_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_n]
    
    resultats_finaux = []
    for doc_id in top_docs_ids:
        doc = docs_metadata[doc_id]
        doc['rrf_score'] = rrf_scores[doc_id]
        resultats_finaux.append(doc)
        
    return resultats_finaux

# ==========================================
#    🔄 ANALYSE ET COMPARAISON INCRÉMENTALE
# ==========================================

print(f"📂 1. Connexion à la base locale et analyse de l'existant...")
db = lancedb.connect("./base_memoire_locale")

fichiers_indexes = {}
if TABLE_NAME in db.table_names():
    table = db.open_table(TABLE_NAME)
    df_existant = table.search().select(["chemin_absolu", "date_modification"]).to_pandas()
    fichiers_indexes = {k: round(v, 2) for k, v in zip(df_existant['chemin_absolu'], df_existant['date_modification'])}
    print(f"   ℹ️ {len(fichiers_indexes)} fichiers uniques détectés dans l'index existant.")
else:
    print("   ℹ️ Base V8.2 vierge. Création de l'index à ID unique stable.")

print(f"\n🔍 2. Parcours du disque et détection des changements...")
fichiers_a_traiter = []
fichiers_sur_disque = set()
liste_projets = set() 

for racine, sous_dossiers, fichiers in os.walk(DOSSIER_CIBLE):
    chemin_relatif_racine = os.path.relpath(racine, DOSSIER_CIBLE)
    if chemin_relatif_racine != ".":
        projet_parent = chemin_relatif_racine.split(os.sep)[0]
        liste_projets.add(projet_parent)
        
    for nom_fichier in fichiers:
        if nom_fichier.startswith('.'): continue
        chemin_absolu = os.path.abspath(os.path.join(racine, nom_fichier))
        fichiers_sur_disque.add(chemin_absolu)
        
        try: 
            mtime = round(os.path.getmtime(chemin_absolu), 2)
        except: continue
            
        if chemin_absolu not in fichiers_indexes or fichiers_indexes[chemin_absolu] != mtime:
            fichiers_a_traiter.append((chemin_absolu, mtime))

if TABLE_NAME in db.table_names():
    fichiers_orphelins = set(fichiers_indexes.keys()) - fichiers_sur_disque
    if fichiers_orphelins:
        for chemin_orphelin in fichiers_orphelins:
            table.delete(f'chemin_absolu = "{chemin_orphelin}"')

total_nouveaux_fichiers = len(fichiers_a_traiter)

# ==========================================
#    🧠 PARSAGE ADAPTATIF ET VECTORISATION
# ==========================================

chunker = MarkdownAdaptiveChunker(max_prose=200, max_code=250, min_chunk=20)
erreurs_vectorisation = 0 

if total_nouveaux_fichiers > 0 or len(fichiers_indexes) == 0:
    print(f"\n🏭 3. Extraction et DÉCOUPAGE INTELLIGENT ({total_nouveaux_fichiers} fichiers)...")
    fragments_a_vectoriser = []
    
    if len(fichiers_indexes) == 0 and liste_projets:
        map_texte = "CARTE GLOBALE DES PROJETS DE LA MACHINE : Ce dossier contient les projets suivants : " + ", ".join(liste_projets)
        fragments_a_vectoriser.append({
            "chemin_absolu": os.path.join(DOSSIER_CIBLE, "INDEX_GLOBAL_SYSTEME"),
            "date_modification": time.time(),
            "texte": map_texte
        })
    
    for chemin, mtime in fichiers_a_traiter:
        contenu_brut = extraire_contenu_fichier(chemin)
        if contenu_brut:
            chemin_rel = os.path.relpath(chemin, DOSSIER_CIBLE)
            dossier_projet = chemin_rel.split(os.sep)[0] if os.sep in chemin_rel else "Racine"
            nom_fichier = os.path.basename(chemin)
            
            morceaux = chunker.chunk_document(dossier_projet, nom_fichier, contenu_brut)
            
            for morceau in morceaux:
                fragments_a_vectoriser.append({
                    "chemin_absolu": chemin,
                    "date_modification": mtime,
                    "texte": morceau 
                })
                
    total_fragments = len(fragments_a_vectoriser)
    print(f"   🧠 {total_fragments} fragments hautement structurés générés.")
    
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
        
        # 🟡 NOTE DE CONCEPTION : Si mutation vers une architecture "Watch" en tâche de fond,
        # l'index BM25 devra impérativement être invalidé et rechargé juste après cette suppression.
        if table and doc['chemin_absolu'] in fichiers_indexes and doc['chemin_absolu'] not in fichiers_nettoyes_session:
            table.delete(f'chemin_absolu = "{doc["chemin_absolu"]}"')
            fichiers_nettoyes_session.add(doc['chemin_absolu'])
            
        vecteur = get_vector_optimized(doc['texte'], is_query=False)
        if vecteur:
            # 🔴 CORRECTION : Injection d'un ID de fragment déterministe et immuable dans LanceDB
            batch_data.append({
                "fragment_id": f"{doc['chemin_absolu']}::{fragments_traites}",
                "vector": vecteur,
                "texte": doc['texte'],
                "chemin_absolu": doc['chemin_absolu'],
                "date_modification": doc['date_modification']
            })
        else:
            erreurs_vectorisation += 1
            
        fragments_traites += 1
        if len(batch_data) >= BATCH_SIZE:
            if table is None: table = db.create_table(TABLE_NAME, data=batch_data)
            else: table.add(batch_data)
            batch_data.clear() 
            
    if batch_data:
        if table is None: table = db.create_table(TABLE_NAME, data=batch_data)
        else: table.add(batch_data)
        batch_data.clear()
        
    print(f"\n\n✅ Base de données V8.2 mise à jour ! (Erreurs de vectorisation : {erreurs_vectorisation})")

# ==========================================
#           🤖 INTERACTION UTILISATEUR
# ==========================================

table = db.open_table(TABLE_NAME)

if HAS_BM25:
    print("\n🧠 Initialisation du Cortex Lexical (BM25)...")
    # 🟠 NOTE DE CONCEPTION (PHASE 2) : Au-delà de 50k fragments, df_all et tokenized_corpus
    # devront être persistés via Pickle ou sérialisés de manière incrémentale.
    df_all = table.search().limit(100000).to_pandas()
    corpus_textes = df_all['texte'].tolist()
    corpus_chemins = df_all['chemin_absolu'].tolist()
    corpus_ids = df_all['fragment_id'].tolist() # 🔴 CORRECTION : Extraction des identifiants stables
    
    tokenized_corpus = [re.findall(r'\w+', doc.lower()) for doc in corpus_textes]
    bm25 = BM25Okapi(tokenized_corpus)
else:
    print("\n⚠️ Module 'rank_bm25' manquant. Moteur hybride désactivé.")
    bm25, corpus_textes, corpus_chemins, corpus_ids = None, None, None, None

print(f"\n🎯 5. À TOI DE JOUER ! (Total indexé : {len(table.to_pandas())} fragments purs)")
question = input("Que veux-tu savoir ou faire ?\n> ")

temps_rech_debut = time.time()

if HAS_BM25:
    resultats = recherche_hybride(question, table, bm25, corpus_textes, corpus_chemins, corpus_ids, top_n=10)
else:
    vecteur_question = get_vector_optimized(question, is_query=True)
    if vecteur_question:
        resultats = table.search(vecteur_question).limit(10).to_list()
    else:
        resultats = []

temps_rech_fin = time.time() - temps_rech_debut
print(f"🔍 Recherche foudroyante effectuée en {temps_rech_fin*1000:.2f} ms")

contexte_global = ""
chemins_trouves = set() 

for res in resultats:
    score_display = f"RRF: {res.get('rrf_score', 0):.4f}" if HAS_BM25 else f"Dist: {res.get('_distance', 0):.3f}"
    contexte_global += f"- (Score {score_display}) {res['texte']}\n"
    
    if res['chemin_absolu'] != os.path.join(DOSSIER_CIBLE, "INDEX_GLOBAL_SYSTEME"):
        chemins_trouves.add(res['chemin_absolu']) 

print(f"✍️ Réflexion en cours ({MOTEUR_REFLEXION})...")

prompt_ia = f"""
Tu es N'symbios, l'assistant système. Ton créateur s'appelle DredGuer.
Voici des fragments hautement structurés de la machine. Chaque fragment indique le [Projet], le [Fichier] et la [Section].

RÈGLES ABSOLUES :
1. Réponds de manière précise en citant le nom des projets.
2. Si la question concerne l'organisation globale, donne une vue d'ensemble.
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

logger_requete(question, resultats, reponse_finale, temps_rech_fin)

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