# 🦖 N'symbios v8.3 - Système d'Exploitation Sémantique Local

N'symbios est un assistant de bureau et un moteur de recherche RAG hybride ultra-rapide (sous la barre des 300 ms en local) conçu pour cartographier, indexer et interroger l'intégralité de tes projets, codes et documentations sans aucune fuite de données vers le Cloud.

---

## 📌 Sommaire

1. [Journal des Mises a Jour](CHANGELOG.md)
2. [Nouveautes v8.3](#nouveautes-v83)
3. [Fonctionnalites Principales](#fonctionnalites-principales)
4. [Screenshots](#screenshots)
5. [Index du Projet](#index-du-projet)
6. [Demarrage Rapide](#demarrage-rapide)
7. [Mise en Production](#mise-en-production)
8. [Architecture Complete](#architecture-complete)
9. [Stack Technique](#stack-technique)
10. [API Endpoints](#api-endpoints)
11. [Base de Donnees](#base-de-donnees)
12. [Configuration](#configuration)
13. [Troubleshooting](#troubleshooting)

---

## 2. Nouveautes v8.3

La version **v8.3 (Stabilisée)** marque le passage d'un script monolithique expérimental à une architecture découplée de grade industriel :
* **Couche 0 Intégrée (SQLite) :** Cartographie macro-sémantique autonome des 23 projets de la machine pour guider l'IA sans requêtes "aspirateurs".
* **Moteur Hybride Déterministe :** Fusion RRF (Reciprocal Rank Fusion) basée sur des `fragment_id` immuables (`chemin::index`) éliminant 100 % des collisions de hash natifs Python.
* **Pipeline OCR Synchrone :** Extraction visuelle via `deepseek-ocr:3b` convertissant automatiquement les images (`.png`, `.jpg`) en fragments Markdown indexables.
* **Interface Flottante Multithreadée :** UI sous `CustomTkinter` asynchrone pour éviter le gel de la fenêtre pendant les phases de réflexion d'Ollama.

---

## 3. Fonctionnalites Principales

* **Section-Aware Chunking :** Découpage adaptatif respectant la hiérarchie Markdown (`#`, `##`), isolant atomiquement les blocs de code (` ``` `) et les listes pour préserver la structure logique.
* **La Guillotine Absolue (Bouclier Anti-Crash 500) :** Analyse par caractères limitée à 800 symboles utiles (marge d'étiquette contextuelle incluse) pour immuniser le tokenizer Nomic contre la densité du code ou du JSON brut.
* **Indexation Incrémentale :** Comparaison des empreintes temporelles (`mtime`) du disque pour ne ré-indexer que les fichiers modifiés. Un scan de 17 000 fragments prend moins de 1 seconde si rien n'a bougé.
* **Mode Éclatement Flottant (Style Spotlight) :** Fenêtre *borderless*, transparente et *Always-on-Top* invocable instantanément, se fermant d'une simple pression sur `Échap`.

---

## 4. Screenshots

> *Placeholders pour l'interface CustomTkinter Borderless en mode Sombre*
+-----------------------------------------------------------------+
|  Que veux-tu savoir ou faire, DredGuer ?...                    |
+-----------------------------------------------------------------+
| 🦖 N'symbios :                                                 |
| En consultant la CARTE GLOBALE DES PROJETS...                   |
| 1. Écosystème IA (Jarvis, PulOs, Export IA...)                  |
|                                                                 |
+-----------------------------------------------------------------+

---

## 5. Index du Projet

```text
nsymbios/
│
├── .env                  # Clés API et secrets (Ignoré par Git)
├── .gitignore            # Protections des dossiers locaux et BDD
├── requirements.txt      # Dépendances Python figées
├── config.py             # Variables d'environnement et constantes globales
├── chunker.py            # Moteur de découpage adaptatif & Guillotine 800
├── embeddings.py         # Appels réseau Ollama & Fail-Fast Healthcheck
├── retrieval.py          # Logique pure de l'algorithme hybride BM25 + RRF
├── main.py               # Chef d'orchestre en mode Terminal interactif
├── ui_dino.py            # Interface graphique flottante CustomTkinter
└── tests/
    └── test_chunker.py   # Suite de tests unitaires de non-régression (Pytest)
'''

---

 ## 6. Demarrage Rapide
Prérequis Système (macOS Homebrew)
Pour éviter le crash d'initialisation du moteur graphique sur Mac, installe Tcl/Tk en amont :
Bash
brew install tcl-tk python-tk@3.14
Installation et initialisation
Active ton environnement virtuel et installe les dépendances :
Bash
source .venv/bin/activate
pip install -r requirements.txt
Crée ton fichier de secrets .env :
Bash
echo "CLE_API_OPENAI=sk-ta-cle-api" > .env
Exécute la suite de tests pour valider le comportement du découpeur :
Bash
pytest tests/test_chunker.py
Génère la cartographie de tes projets (Couche 0) :
Bash
python structure.py
Lance l'interface graphique du Dinosaure :
Bash
python ui_dino.py

---

##7. Mise en Production
N'symbios v8.3 est la version finale de validation algorithmique (Phase 1). Les jalons pour la Phase 2 (Industrialisation) et Phase 3 (Rust) sont :
Persistance de l'index Lexical : Sérialisation de l'arbre BM25 via pickle ou stockage SQLite pour éviter le rebuild en mémoire vive au-delà de 50 000 fragments.
Migration native vers la v9 (Core Rust) : Réécriture complète en Rust via les crates lancedb, candle (HuggingFace) et Tauri pour intégrer directement le modèle Nomic en local (ONNX Runtime) sans passer par la surcouche réseau HTTP d'Ollama.

---

##8. Architecture Complete

   [ Interface Utilisateur ] <---> [ ui_dino.py (Threading) ]
                                          |
                                          v
   [ COUCHE 0 : Global ] --------> [ symbios_meta.db (SQLite) ]
                                          |
   [ COUCHE 1 : Profond ] -------> [ lancedb (Vectoriel) ]  <--+-- Fusion RRF 
                                   [ rank-bm25 (Lexical) ] <--+  (retrieval.py)

---

##9. Stack Technique
Langage : Python 3.14+ (Environnement virtuel isolé)
Base de données Sémantique : LanceDB (Format d'intégration vectoriel persistant en local)
Base de données Structurelle : SQLite3 (Couche 0 native)
Moteur Lexical : BM25Okapi (rank-bm25)
Framework Graphique : CustomTkinter (Tcl/Tk 8.6)
Moteurs IA (Ollama Local) :
Embedding : nomic-embed-text-v2-moe:latest (Matryoshka 256 dim)
Réflexion : gemma4:12b
Vision/OCR : deepseek-ocr:3b

---

##10. API Endpoints
N'symbios communique exclusivement sur le réseau local via l'instance Ollama :
Génération d'embeddings : POST http://localhost:11434/api/embeddings
Inférence LLM (Gemma) : POST http://localhost:11434/api/generate

---

##11. Base de Donnees

Schéma de la table LanceDB (fichiers_v8)
Colonne	Type	Description
fragment_id	TEXT (Primary)	Clé déterministe unique au format chemin_absolu::index
vector	VECTOR(256)	Embedding tronqué Matryoshka de Nomic
texte	TEXT	Contenu textuel brut du fragment avec son étiquette contextuelle
chemin_absolu	TEXT	Emplacement du fichier source sur le Finder
date_modification	FLOAT	Timestamp de modification (mtime) arrondi à 2 décimales

---

##12. Configuration

Toute la configuration structurelle se gère dans config.py :
Python
DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 
TABLE_NAME = "fichiers_v8"
EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest"
DIMENSION_MATRYOSHKA = 256
OCR_MODEL = "deepseek-ocr:3b"
GENERATION_MODEL_OLLAMA = "gemma4:12b"

---

##13. Troubleshooting

1. ModuleNotFoundError: No module named '_tkinter'
Cause : L'installation Python via Homebrew n'a pas embarqué l'interface graphique.
Résolution : Lance brew install tcl-tk python-tk@3.14 puis redémarre ton terminal.
2. the input length exceeds the context length (Status Code: 500)
Cause : Un fragment brut ou minifié a contourné le chunker de prose.
Résolution : La sécurité active de la Guillotine à 800 caractères dans chunker.py intercepte désormais ce cas. Si l'erreur réapparaît, vide la base locale avec rm -rf ./base_memoire_locale et réduis MAX_CHARS à 600 dans chunker.py.