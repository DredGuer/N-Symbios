# 🦖 N'symbios v8.3 - Système d'Exploitation Sémantique Hybride

N'symbios est un assistant de bureau et un moteur de recherche RAG hybride ultra-rapide conçu pour cartographier, indexer et interroger l'intégralité de tes projets, codes et documentations. En associant une base vectorielle 100 % locale et la vélocité d'une API de réflexion, il garantit des réponses sous la barre des 2 secondes.

---

## 📌 Sommaire

1. [Journal des Mises à Jour](CHANGELOG.md)
2. [Nouveautés v8.3](#nouveautés-v83)
3. [Fonctionnalités Principales](#fonctionnalités-principales)
4. [Screenshots](#screenshots)
5. [Index du Projet](#index-du-projet)
6. [Démarrage Rapide](#démarrage-rapide)
7. [Mise en Production (Phase 2)](#mise-en-production)
8. [Architecture Complète](#architecture-complète)
9. [Stack Technique](#stack-technique)
10. [API Endpoints](#api-endpoints)
11. [Base de Données](#base-de-données)
12. [Configuration](#configuration)
13. [Troubleshooting](#troubleshooting)
14. [Licence et Droits](#licence-et-droits)

---

## 2. Nouveautés v8.3

La version **v8.3 (Stabilisée)** marque le passage d'un script monolithique expérimental à une architecture découplée de grade industriel :
* **Réflexion Hybride (API / Local) :** Bascule instantanée sur `gpt-4o-mini` pour réduire la latence de réflexion de 4 minutes à moins de 2 secondes, tout en gardant l'indexation 100 % locale.
* **Couche 0 Intégrée (SQLite) :** Cartographie macro-sémantique autonome des 23 projets de la machine pour guider l'IA sans requêtes "aspirateurs".
* **Moteur Hybride Déterministe :** Fusion RRF (Reciprocal Rank Fusion) basée sur des `fragment_id` immuables (`chemin::index`) éliminant 100 % des collisions de hash natifs Python.
* **Pipeline OCR Multimodal :** Extraction visuelle via `glm-ocr` convertissant automatiquement les images (`.png`, `.jpg`) en fragments Markdown indexables, avec sécurité anti-boucle.
* **Interface Flottante Multithreadée :** UI sous `CustomTkinter` asynchrone pour éviter le gel de la fenêtre pendant les phases d'interrogation réseau.

---

## 3. Fonctionnalités Principales

* **Section-Aware Chunking :** Découpage adaptatif respectant la hiérarchie Markdown (`#`, `##`), isolant atomiquement les blocs de code (` ``` `) et les listes pour préserver la structure logique.
* **La Guillotine Absolue (Bouclier Anti-Crash 500) :** Analyse par caractères limitée à 800 symboles utiles pour immuniser le tokenizer Nomic contre la densité du code ou du JSON brut.
* **Indexation Incrémentale :** Comparaison des empreintes temporelles (`mtime`) du disque pour ne ré-indexer que les fichiers modifiés.
* **Mode Éclatement Flottant (Style Spotlight) :** Fenêtre *borderless*, transparente et *Always-on-Top* invocable instantanément, se fermant d'une simple pression sur `Échap`.

---

## 4. Screenshots

> *Interface CustomTkinter Borderless en mode Sombre*
```text
+-----------------------------------------------------------------+
|  Que veux-tu savoir ou faire, DredGuer ?...                    |
+-----------------------------------------------------------------+
| 🦖 N'symbios :                                                 |
| D'après ta carte globale des projets (couche 0)...              |
| 1. Écosystème IA (Export IA, PulMind, PulOs...)                 |
| 2. Infrastructures réseau/accès (NVNC, Naulthene, Neo)          |
+-----------------------------------------------------------------+

---

## 5. Index du Projet

Plaintext
nsymbios/
│
├── .env                  # Clés API et secrets (Ignoré par Git)
├── .gitignore            # Protections des dossiers locaux et BDD
├── LICENSE               # Licence CC BY 4.0
├── requirements.txt      # Dépendances Python figées
├── config.py             # Variables d'environnement et constantes globales
├── chunker.py            # Moteur de découpage adaptatif & Guillotine 800
├── embeddings.py         # Appels réseau Ollama & Fail-Fast Healthcheck
├── ocr_pipeline.py       # Extracteur de vision via glm-ocr
├── retrieval.py          # Logique pure de l'algorithme hybride BM25 + RRF
├── main.py               # Chef d'orchestre en mode Terminal interactif
├── structure.py          # Générateur de la Couche 0 (SQLite)
└── ui_dino.py            # Interface graphique flottante CustomTkinter connectée

--- 

 ## 6. Démarrage Rapide

*Prérequis Système (macOS Homebrew)
Pour éviter le crash d'initialisation du moteur graphique sur Mac, installe Tcl/Tk en amont :
Bash
brew install tcl-tk python-tk@3.14
Installation et initialisation
Active ton environnement virtuel et installe les dépendances :
Bash
source .venv/bin/activate
pip install -r requirements.txt
Crée ton fichier de secrets .env pour la réflexion API :
Bash
echo "CLE_API_OPENAI=sk-ta-cle-api" > .env
Télécharge les modèles locaux requis via Ollama :
Bash
ollama pull nomic-embed-text-v2-moe:latest
ollama pull glm-ocr
Génère la cartographie de tes projets (Couche 0) :
Bash
python structure.py
Lance l'indexation de la Couche 1 :
Bash
python main.py
Invoque l'interface graphique du Dinosaure :
Bash
python ui_dino.py

---

 ## 7. Mise en Production

N'symbios v8.3 est la version finale de validation algorithmique (Phase 1).
Les jalons pour la Phase 2 (Industrialisation / Optimisation Latence) sont :
Remplacement de l'Embedding Local : Contourner l'appel Ollama (nomic-embed) lors de la requête de l'utilisateur pour détruire les 20 secondes de latence au profit d'une inférence Python pure ou API.
Persistance de l'index Lexical : Sérialisation de l'arbre BM25 via pickle ou stockage SQLite pour éviter le rebuild en mémoire vive au-delà de 50 000 fragments.
Migration native vers la v9 (Core Rust) : Réécriture complète en Rust via les crates lancedb, candle (HuggingFace) et Tauri pour une UI native.

---

 ## 8. Architecture Complète

Plaintext
   [ Interface Utilisateur ] <---> [ ui_dino.py (Threading) ]
                                          |
   [ Moteur IA ] <------------------------+-- (OpenAI API / Ollama)
                                          |
   [ COUCHE 0 : Global ] --------> [ symbios_meta.db (SQLite) ]
                                          |
   [ COUCHE 1 : Profond ] -------> [ lancedb (Vectoriel) ]  <--+-- Fusion RRF 
                                   [ rank-bm25 (Lexical) ] <--+  (retrieval.py)

---

## 9. Stack Technique
Langage : Python 3.14+ (Environnement virtuel isolé)
Base de données Sémantique : LanceDB (Format d'intégration vectoriel persistant en local)
Base de données Structurelle : SQLite3 (Couche 0 native)
Moteur Lexical : BM25Okapi (rank-bm25)
Framework Graphique : CustomTkinter (Tcl/Tk 8.6)
Moteurs IA :
Embedding (Local) : nomic-embed-text-v2-moe:latest (Matryoshka 256 dim)
Réflexion (API) : gpt-4o-mini (OpenAI)
Vision/OCR (Local) : glm-ocr (Ollama)

---

 ## 10. API Endpoints

N'symbios gère un flux hybride, communiquant sur le réseau local et externe :
Génération d'embeddings & OCR : POST http://localhost:11434/api/generate (Ollama)
Inférence LLM Principale : POST https://api.openai.com/v1/chat/completions (OpenAI)

---

 ## 11. Base de Données

Schéma de la table LanceDB (fichiers_v8)
Colonne	Type	Description
fragment_id	TEXT (Primary)	Clé déterministe unique au format chemin_absolu::index
vector	VECTOR(256)	Embedding tronqué Matryoshka de Nomic
texte	TEXT	Contenu textuel brut du fragment avec son étiquette contextuelle
chemin_absolu	TEXT	Emplacement du fichier source sur le Finder
date_modification	FLOAT	Timestamp de modification (mtime) arrondi à 2 décimales

---

 ## 12. Configuration

Toute la configuration structurelle se gère dynamiquement dans config.py :
Python
DOSSIER_CIBLE = "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/10. Paramettrage IA" 
TABLE_NAME = "fichiers_v8"
EMBEDDING_MODEL = "nomic-embed-text-v2-moe:latest"
DIMENSION_MATRYOSHKA = 256
OCR_MODEL = "glm-ocr"
MOTEUR_REFLEXION = "API"
GENERATION_MODEL_API = "gpt-4o-mini"
GENERATION_MODEL_OLLAMA = "gemma4:12b"

---

 ## 13. Troubleshooting

1. ModuleNotFoundError: No module named '_tkinter'
Cause : L'installation Python via Homebrew n'a pas embarqué l'interface graphique.
Résolution : Lance brew install tcl-tk python-tk@3.14 puis redémarre ton terminal.
2. the input length exceeds the context length (Status Code: 500)
Cause : Un fragment brut ou minifié a contourné le chunker de prose.
Résolution : La sécurité active de la Guillotine à 800 caractères dans chunker.py intercepte désormais ce cas. Si l'erreur réapparaît, vide la base locale avec rm -rf ./base_memoire_locale et réduis MAX_CHARS à 600 dans chunker.py.

---

 ## 14. Licence et Droits
 
Ce projet est protégé sous la licence Creative Commons Attribution 4.0 International (CC BY 4.0).
Toute modification, dérivation ou redistribution de ce code est autorisée, à condition de fournir une attribution claire et visible au créateur original de l'architecture logicielle : Adrien Nault (DredGuer).