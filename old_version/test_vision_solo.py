import os
import ollama

# Remplace par le chemin EXACT de ton image sur ton Mac
CHEMIN_IMAGE = "708e89b4-dcbf-4017-b99a-b9d48d86366f.jpg" 
MODELE_OCR = "glm-ocr"

print(f"👁️ Envoi de l'image [{os.path.basename(CHEMIN_IMAGE)}] à {MODELE_OCR}...")

prompt = """
Tu es un extracteur OCR. 
Extrais TOUT le texte visible dans cette image, mot pour mot. 
Ne fais aucun commentaire. Donne juste le texte.
"""

try:
    if not os.path.exists(CHEMIN_IMAGE):
        print(f"❌ Erreur : Le fichier image est introuvable au chemin : {os.path.abspath(CHEMIN_IMAGE)}")
        exit()
        
    response = ollama.generate(
        model=MODELE_OCR,
        prompt=prompt,
        images=[os.path.abspath(CHEMIN_IMAGE)]
    )
    
    print("\n=====================================")
    print("      📝 RÉSULTAT DE L'OCR")
    print("=====================================")
    print(response.get('response', 'Vide...'))
    print("=====================================")

except Exception as e:
    print(f"❌ Erreur lors de l'appel Ollama : {e}")