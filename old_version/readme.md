# 🦖 N'symbios (v1.0-Alpha)
> Le Compagnon de Bureau Symbiotique, Souverain et 100% Local.

N'symbios est un assistant système d'exploitation de nouvelle génération. Contrairement aux outils cloud intrusifs, N'symbios fonctionne de manière totalement autonome et hors-ligne sur votre machine. Il apprend à connaître l'arborescence et le contenu sémantique de vos fichiers pour devenir le bibliothécaire et l'agent d'action ultime de votre vie numérique.

## 🚀 Vision du Projet & Horizons

1. **Horizon 1 (MVP) :** Moteur de recherche sémantique hybride en cascade (Conscience spatiale des dossiers).
2. **Horizon 2 (Assistant) :** Synthèse active, automatisation des livrables courants (Markdown, PDF, PowerPoint).
3. **Horizon 3 (Symbiose OS) :** Gestion dynamique des ressources système (RAM/CPU) selon l'état de concentration de l'utilisateur.
4. **Horizon 4 (Agent Autonome) :** Création active complète (génération de maquettes web, scripts complexes) en langage naturel.

## 🛠️ Architecture Technique (Prototype vs Final)

| Composant | Prototype Actuel (Python) | Version Cible (Production Rust) |
| :--- | :--- | :--- |
| **Interface** | CustomTkinter (Widget Flottant) | Tauri + HTML/CSS/JS |
| **Base Vectorielle** | LanceDB (Embedded) | LanceDB / C++ Core Engine |
| **Modèle Embedding**| Nomic-Embed-Text-v2 (Ollama) | Nomic v2 (Format ONNX Local) |
| **Modèle Réflexion** | Gemma 4 (2B / 12B via Ollama) | Petit LLM Local Optimisé (GGUF/ONNX) |
| **Vision / OCR** | Deepseek-OCR (3B) | Modèle VL de poche intégré |

## 📦 Statut de l'Indexation Sémantique Contextuelle
Le système utilise un algorithme d'indexation **en cascade (Hierarchical RAG)** avec injection du contexte spatial. Chaque fragment de texte extrait du disque dur est scellé avec son étiquette d'origine : `[Projet: X | Fichier: Y] Texte`.

À ajouter : Préciser que le système s'appuie sur une vérification de l'empreinte temporelle (mtime) et sémantique de chaque fichier.
Pourquoi ? C'est ce qui justifie techniquement que le second scan prend 0 seconde. Il faut que ce soit écrit noir sur blanc dans la vision technique.