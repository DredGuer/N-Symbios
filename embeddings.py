import os
import sys
import ollama
from config import EMBEDDING_MODEL, DIMENSION_MATRYOSHKA

# 🔥 ANCHOR ANTI-CRASH : Désactive le parallélisme pour éviter les deadlocks sur Mac
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from sentence_transformers import SentenceTransformer

print("⏳ Initialisation du moteur de vectorisation local (Nomic)...")
try:
    # Chargement unique en RAM au démarrage
    model = SentenceTransformer("nomic-ai/nomic-embed-text-v2-moe", trust_remote_code=True)
    print("✅ Moteur d'embedding local prêt.")
except Exception as e:
    print(f"❌ ERREUR CRITIQUE : Impossible de charger le modèle d'embedding : {e}")
    sys.exit(1)

def verifier_environnement():
    """Fail-fast : Vérifie qu'Ollama est actif pour la réflexion."""
    try:
        ollama.list()
    except Exception:
        print("❌ ERREUR CRITIQUE : Ollama n'est pas accessible.")
        print("👉 Lance la commande 'ollama serve' avant de continuer.")
        sys.exit(1)

def get_vector_optimized(text, is_query=False):
    """Génération instantanée (< 30ms) en local, bridée pour économiser le processeur."""
    prefix = "search_query: " if is_query else "search_document: "
    try:
        # La Guillotine Absolue à 800 caractères évite la surchauffe sur les gros blocs
        safe_text = (prefix + text)[:800]
        
        # Encodage linéaire sans barres de progression énergivores
        embedding = model.encode(
            safe_text, 
            convert_to_numpy=True, 
            show_progress_bar=False
        )
        return embedding[:DIMENSION_MATRYOSHKA].tolist()
    except Exception as e:
        print(f"\n   ⚠️ Embedding local échoué : {e}")
        return None