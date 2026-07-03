import ollama
from config import OCR_MODEL

def extraire_texte_image(chemin_image):
    """
    Envoie l'image à glm-ocr et applique des verrous de sécurité
    pour empêcher les boucles infinies de répétition.
    """
    prompt_vision = "Ocr: " # Glm-ocr réagit très bien à ce prompt minimal pour extraire le texte pur
    
    try:
        reponse = ollama.generate(
            model="glm-ocr",
            prompt=prompt_vision,
            images=[chemin_image],
            options={
                "temperature": 0.0,      # Sécurité 1 : Reste factuel, pas d'improvisation
                "num_predict": 200,      # Sécurité 2 : Coupe le sifflet après 200 tokens max (anti-boucle)
                "repeat_penalty": 1.5    # Sécurité 3 : Pénalise fortement la répétition de mots
            }
        )
        
        texte_brut = reponse.get('response', '').strip()
        if not texte_brut:
            return ""
            
        # Secousse de nettoyage : Si le modèle a quand même tenté de tricher en se répétant,
        # on ne garde que les lignes uniques dans l'ordre d'apparition.
        lignes_uniques = []
        for ligne in texte_brut.split('\n'):
            ligne_clean = ligne.strip()
            if ligne_clean and ligne_clean not in lignes_uniques:
                lignes_uniques.append(ligne_clean)
                
        return "\n".join(lignes_uniques)
        
    except Exception as e:
        print(f"\n   ⚠️ Échec de l'OCR sur l'image [{chemin_image}] : {e}")
        return ""