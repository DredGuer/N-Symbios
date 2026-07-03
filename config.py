import os
from dotenv import load_dotenv

# Chargement sécurisé des secrets
load_dotenv()
CLE_API_OPENAI = os.getenv("CLE_API_OPENAI", "")

# Constantes structurelles
DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 
TABLE_NAME = "fichiers_v8" 
FICHIER_LOGS = "query_log.jsonl" 
BATCH_SIZE = 500 

EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest" 
DIMENSION_MATRYOSHKA = 256 
OCR_MODEL = "glm-ocr"

# Dans config.py
MOTEUR_REFLEXION = "API"
GENERATION_MODEL_API = "gpt-5.4-nano"

#MOTEUR_REFLEXION = "OLLAMA" 
#GENERATION_MODEL_OLLAMA = "gemma4:12b"
#GENERATION_MODEL_API = "gpt-4o-mini"