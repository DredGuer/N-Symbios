# =====================================================================
# N'SYMBIOS SKILL MANIFEST
# =====================================================================
# Ce dictionnaire est lu automatiquement par le système au démarrage.
# Il décrit à l'IA quand et comment déclencher ce skill en langage naturel.
# =====================================================================

MANIFEST = {
    "name": "creer_note_markdown",
    "description": "Permet de générer un résumé, une synthèse ou une note propre au format Markdown (.md) et de l'enregistrer sur la machine.",
    "parameters": {
        "type": "object",
        "properties": {
            "nom_projet": {
                "type": "string",
                "description": "Le nom du projet ou du dossier concerné par la synthèse (ex: PulMind, Cap de vie)."
            },
            "type_note": {
                "type": "string",
                "enum": ["synthese", "todo_list", "compte_rendu"],
                "description": "Le format de document demandé par l'utilisateur."
            }
        },
        "required": ["nom_projet"]
    }
}

# =====================================================================
# CORE EXECUTION
# =====================================================================
# Cette fonction est appelée par le système si l'IA a déclenché le skill.
# Les arguments sont injectés automatiquement par l'analyse du langage naturel.
# =====================================================================

def execute(arguments, contexte_lancedb=None):
    """
    Le point d'entrée unique du Skill.
    :param arguments: dict contenant les paramètres extraits par l'IA.
    :param contexte_lancedb: Accès direct à la base sémantique si le skill doit lire des données.
    :return: dict contenant le statut et le message à afficher à l'utilisateur.
    """
    try:
        # 1. Récupération sécurisée des variables sémantiques
        projet = arguments.get("nom_projet")
        style = arguments.get("type_note", "synthese")
        
        # 2. Logique métier du skill (Exemple ici : création du fichier)
        chemin_bureau = os.path.expanduser("~/Desktop")
        nom_fichier = f"{style}_{projet}_{int(time.time())}.md"
        chemin_final = os.path.join(chemin_bureau, nom_fichier)
        
        # [Ici se placera le code de génération de ta note brute...]
        with open(chemin_final, "w", encoding="utf-8") as f:
            f.write(f"# {style.upper()} - {projet}\n\nDocument généré automatiquement par N'symbios.")
            
        # 3. Réponse normalisée pour le système
        return {
            "status": "success",
            "message": f"J'ai créé ton document avec succès ! Tu peux le retrouver ici : {nom_fichier}",
            "action_native": f"open '{chemin_final}'" # Commande système optionnelle à exécuter
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Je n'ai pas réussi à exécuter l'action. Erreur : {str(e)}"
        }