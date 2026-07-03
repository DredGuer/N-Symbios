import os
import sqlite3
import json
import ollama
from config import DOSSIER_CIBLE, GENERATION_MODEL_OLLAMA

DB_PATH = "symbios_meta.db"

def init_db():
    """Crée la base SQLite de la Couche 0 si elle n'existe pas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semantic_projects (
            nom_projet TEXT PRIMARY KEY,
            chemin_relatif TEXT,
            description TEXT,
            tags TEXT
        )
    """)
    conn.commit()
    return conn

def analyser_projet_ia(nom_projet, liste_fichiers):
    """Demande à l'IA de déduire ce qu'est le projet en lisant ses fichiers."""
    # On limite à 30 fichiers pour ne pas surcharger le prompt
    fichiers_echantillon = "\n".join(liste_fichiers[:30])
    
    prompt = f"""
    Tu es l'architecte système N'symbios. Voici un dossier nommé '{nom_projet}'.
    Il contient les fichiers suivants :
    {fichiers_echantillon}
    
    Déduis l'objectif de ce projet et renvoie-moi UNIQUEMENT un objet JSON valide avec ce format exact :
    {{
        "description": "Une phrase claire résumant l'objectif du projet.",
        "tags": ["Tag1", "Tag2", "Tag3"]
    }}
    Ne dis rien d'autre, je dois parser ce JSON.
    """
    
    try:
        response = ollama.generate(model=GENERATION_MODEL_OLLAMA, prompt=prompt)
        # Nettoyage rudimentaire pour extraire le JSON au cas où l'IA bavarde
        texte_brut = response['response']
        json_str = texte_brut[texte_brut.find("{"):texte_brut.rfind("}")+1]
        data = json.loads(json_str)
        return data.get("description", "Description indisponible"), ", ".join(data.get("tags", []))
    except Exception as e:
        return "Analyse échouée.", "erreur, inconnu"

def main():
    print("🧠 Initialisation de la Couche 0 (Cartographie des Projets)...")
    conn = init_db()
    cursor = conn.cursor()
    
    # 1. Lister les projets (Dossiers de premier niveau)
    dossiers_racine = [d for d in os.listdir(DOSSIER_CIBLE) if os.path.isdir(os.path.join(DOSSIER_CIBLE, d)) and not d.startswith('.')]
    
    print(f"📂 {len(dossiers_racine)} projets détectés à la racine.")
    
    # 2. Analyser chaque projet
    for projet in dossiers_racine:
        chemin_complet = os.path.join(DOSSIER_CIBLE, projet)
        
        # Vérifier si le projet est déjà dans la base
        cursor.execute("SELECT nom_projet FROM semantic_projects WHERE nom_projet = ?", (projet,))
        if cursor.fetchone():
            print(f"   ✅ [{projet}] déjà cartographié. Ignoré.")
            continue
            
        print(f"   🔍 Analyse de [{projet}] en cours...")
        
        # Récupérer tous les fichiers pour l'IA
        tous_les_fichiers = []
        for racine, _, fichiers in os.walk(chemin_complet):
            for f in fichiers:
                if not f.startswith('.'):
                    tous_les_fichiers.append(f)
                    
        # Demander l'analyse à Gemma
        description, tags = analyser_projet_ia(projet, tous_les_fichiers)
        
        # Sauvegarder dans SQLite
        cursor.execute("""
            INSERT INTO semantic_projects (nom_projet, chemin_relatif, description, tags)
            VALUES (?, ?, ?, ?)
        """, (projet, projet, description, tags))
        conn.commit()
        
        print(f"      📝 Desc : {description}")
        print(f"      🏷️ Tags : {tags}")

    conn.close()
    print("\n✅ Couche 0 générée avec succès ! (symbios_meta.db est prêt)")

if __name__ == "__main__":
    main()