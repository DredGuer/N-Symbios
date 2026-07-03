# 📜 Charte de Normalisation des Skills pour N'symbios

Pour garantir la stabilité de l'OS et permettre à n'importe quel développeur d'étendre les capacités du petit dinosaure, chaque compétence doit se soumettre à cette charte de normalisation stricte.

---

## 📋 Les 4 Critères Obligatoires d'un Skill

### 1️⃣ **Le Numéro Unique Obligatoire (ID)**

Chaque skill possède un identifiant numérique unique (**NS-XXXX**). Les plages de numéros déterminent la catégorie du skill :

- **NS-1000 à NS-1999** : Gestion du système de fichiers (Lecture, écriture, Marie Poppins).
- **NS-2000 à NS-2999** : Contrôle de l'OS et des applications (Ouvrir, fermer, fenêtres).
- **NS-3000 à NS-3999** : Génération de livrables (Markdown, PDF, PPTX).
- **NS-4000 à NS-4999** : Multimédia et vision (OCR, reconnaissance faciale).

---

### 2️⃣ **Le Nom & la Description Sémantique**

Écrits en texte clair dans le manifeste. C'est ce qui permet à l'IA de savoir à quoi sert le skill en lisant la phrase en langage naturel de l'utilisateur.

---

### 3️⃣ **Le Niveau de Signature (Sécurité)**

Déclare si l'action nécessite une validation humaine ou s'exécute en silence.

---

### 4️⃣ **Le Contrat d'Interaction avec le Cœur**

L'interaction se fait exclusivement via la fonction universelle `execute(arguments, contexte)`. **Un skill ne peut jamais modifier le code racine de N'symbios.**

---

### 5️⃣ Un 5ème critère obligatoire : L'auto-vérification des dépendances. Chaque skill doit vérifier au démarrage si ses modules tiers sont présents, et sinon, renvoyer un statut propre à N'symbios sans faire planter l'application.

---

## 🗂️ Tableau des Signatures Visuelles des Skills de Base


| **ID Unique** | **Nom du Skill**      | **Signature de Sécurité** | **Interaction avec N'symbios**                                                                                               |
| ------------- | --------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| NS-1001       | marie_poppins         | 🟡 CONFIRM                | Scanne le Bureau/Téléchargements, compare les vecteurs avec l'index global de DredGuer et déplace les fichiers physiques.    |
| NS-2001       | gestion_app           | 🟡 CONFIRM                | Envoie une commande AppleScript native pour ouvrir/fermer des applications ou figer des processus.                           |
| NS-3001       | synthese_md           | 🟢 SILENT                 | Reçoit le contexte sémantique extrait de LanceDB par le cœur, formate le texte en Markdown et crée le fichier sur le Bureau. |
| NS-3002       | generateur_pdf        | 🟢 SILENT                 | Compile une note textuelle ou une structure sémantique en un fichier PDF mis en page via ReportLab.                          |
| NS-4001       | reconnaissance_visage | 🟢 SILENT                 | Reçoit le chemin d'une image, extrait l'empreinte faciale et la compare à l'index sémantique des contacts locaux.            |


---

**Synthèse** : Cette charte définit 4 critères stricts (ID unique, description sémantique, niveau de sécurité, contrat d'interaction) pour normaliser les skills de N'symbios, avec un tableau récapitulatif des skills de base et leurs signatures.