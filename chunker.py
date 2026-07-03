import re

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