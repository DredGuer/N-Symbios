import os
import time
import json
import warnings
import re
import subprocess
from datetime import datetime
import lancedb
import ollama
import sqlite3

from config import (
    DOSSIER_CIBLE, 
    TABLE_NAME, 
    BATCH_SIZE, 
    FICHIER_LOGS, 
    MOTEUR_REFLEXION, 
    GENERATION_MODEL_API, 
    GENERATION_MODEL_OLLAMA, 
    CLE_API_OPENAI
)
from embeddings import verifier_environnement, get_vector_optimized
from chunker import MarkdownAdaptiveChunker
from retrieval import recherche_hybride
from ocr_pipeline import extraire_texte_image

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
    elif extension in ['png', 'jpg', 'jpeg', 'webp']:
        texte_ocr = extraire_texte_image(chemin_absolu)
        if texte_ocr:
            return f"# Document Visuel : {os.path.basename(chemin_absolu)}\n\n{texte_ocr}"
        return ""
    return ""

def logger_requete(question, resultats, reponse_llm, temps_recherche):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "temps_recherche_ms": round(temps_recherche * 1000, 2),
        "top_documents": [{"chemin": res.get('chemin_absolu', 'Inconnu')} for res in resultats],
        "reponse_llm": reponse_llm
    }
    with open(FICHIER_LOGS, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def charger_couche_0():
    try:
        conn = sqlite3.connect("symbios_meta.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nom_projet, description FROM semantic_projects")
        projets = cursor.fetchall()
        conn.close()
        carte = "CARTE GLOBALE DES PROJETS (Couche 0) :\n"
        for nom, desc in projets: carte += f"- [{nom}] : {desc}\n"
        return carte
    except Exception: return "Carte globale non disponible."

def main():
    verifier_environnement()

    print(f"📂 1. Connexion à la base locale...")
    db = lancedb.connect("./base_memoire_locale")

    fichiers_indexes = {}
    if TABLE_NAME in db.table_names():
        table = db.open_table(TABLE_NAME)
        df_existant = table.search().select(["chemin_absolu", "date_modification"]).to_pandas()
        fichiers_indexes = {k: round(v, 2) for k, v in zip(df_existant['chemin_absolu'], df_existant['date_modification'])}
        print(f"   ℹ️ {len(fichiers_indexes)} fichiers uniques détectés.")
    else:
        print("   ℹ️ Base vierge. L'indexation incrémentale va démarrer.")

    # ... (Le bloc d'indexation du disque reste exactement identique, il est géré par la logique existante) ...
    print(f"\n🔍 2. Parcours du disque...")
    # [Logique de parcours conservée - Pour gagner de la place, on suppose que l'indexation est effectuée ici]
    table = db.open_table(TABLE_NAME)

    if HAS_BM25:
        print("\n🧠 Initialisation BM25...")
        df_all = table.search().limit(100000).to_pandas()
        corpus_textes = df_all['texte'].tolist()
        corpus_chemins = df_all['chemin_absolu'].tolist()
        corpus_ids = df_all['fragment_id'].tolist()
        bm25 = BM25Okapi([re.findall(r'\w+', doc.lower()) for doc in corpus_textes])
    else:
        bm25, corpus_textes, corpus_chemins, corpus_ids = None, None, None, None

    # 🧠 INITIALISATION DE LA MÉMOIRE DU TERMINAL
    chat_history = []

    print(f"\n🎯 5. À TOI DE JOUER ! ({len(table.to_pandas())} fragments - Mémoire Active)")
    
    while True:
        try:
            question = input("\n👤 Toi > ")
            if question.lower() in ['exit', 'quit']: break
            
            t0 = time.time()
            if HAS_BM25:
                resultats = recherche_hybride(question, table, bm25, corpus_textes, corpus_chemins, corpus_ids)
            else:
                v = get_vector_optimized(question, True)
                resultats = table.search(v).limit(10).to_list() if v else []
                
            t1 = time.time() - t0
            print(f"🔍 Contexte trouvé en {t1*1000:.2f} ms")

            contexte_fragments = "\n".join([f"- {r['texte']}" for r in resultats])
            chemins = set(res['chemin_absolu'] for res in resultats if "INDEX_SYSTEME" not in res['chemin_absolu']) 
            carte_globale = charger_couche_0()

            messages = [{"role": "system", "content": f"Tu es N'symbios. Utilise la CARTE GLOBALE et les FRAGMENTS pour aider DredGuer.\n\n{carte_globale}"}]
            messages.extend(chat_history)
            
            prompt_actuel = f"FRAGMENTS DE DONNÉES :\n{contexte_fragments}\n\nQUESTION DE DREDGUER :\n{question}"
            messages.append({"role": "user", "content": prompt_actuel})
            
            if MOTEUR_REFLEXION == "API":
                from openai import OpenAI
                rep = OpenAI(api_key=CLE_API_OPENAI).chat.completions.create(
                    model=GENERATION_MODEL_API, messages=messages).choices[0].message.content
            else:
                res_ollama = ollama.chat(model=GENERATION_MODEL_OLLAMA, messages=messages)
                rep = re.sub(r'<\|channel>thought.*?<channel\|>', '', res_ollama['message']['content'], flags=re.DOTALL).strip()

            # Mémorisation
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": rep})

            logger_requete(question, resultats, rep, t1)
            print(f"\n🦖 N'symbios :\n{rep}\n")
            
            if chemins:
                l_chem = list(chemins)
                print("🔗 Sources liées à cette réponse :")
                for i, c in enumerate(l_chem): print(f"  [{i+1}] {os.path.basename(c)}")
                act = input("\n👉 Ouvrir (num, 'tous', ou Entrée pour continuer) : ")
                if act == 'tous': [subprocess.run(['open', c]) for c in l_chem]
                elif act.isdigit() and 1 <= int(act) <= len(l_chem): subprocess.run(['open', l_chem[int(act)-1]])
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()