import re
from embeddings import get_vector_optimized

def recherche_hybride(question, table, bm25, corpus_textes, corpus_chemins, corpus_ids, top_n=10):
    """Logique mathématique de fusion (Déterministe et testable)"""
    vecteur = get_vector_optimized(question, is_query=True)
    res_vector = table.search(vecteur).limit(50).to_list() if vecteur else []
    
    tokenized_query = re.findall(r'\w+', question.lower())
    bm25_scores = bm25.get_scores(tokenized_query)
    top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:50]
    
    rrf_scores = {}
    docs_metadata = {}
    k = 60 
    
    for rank, res in enumerate(res_vector):
        doc_id = res['fragment_id']
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        docs_metadata[doc_id] = res
        
    for rank, idx in enumerate(top_bm25_indices):
        doc_id = corpus_ids[idx]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        
        if doc_id not in docs_metadata:
            docs_metadata[doc_id] = {
                "fragment_id": doc_id,
                "texte": corpus_textes[idx],
                "chemin_absolu": corpus_chemins[idx],
                "_distance": None # Identifiant sentinelle explicite
            }
            
    top_docs_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_n]
    
    resultats_finaux = []
    for doc_id in top_docs_ids:
        doc = docs_metadata[doc_id]
        doc['rrf_score'] = rrf_scores[doc_id]
        resultats_finaux.append(doc)
        
    return resultats_finaux