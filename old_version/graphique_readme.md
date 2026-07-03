# 🎨 Spécifications de l'Interface Graphique (GUI) - N'symbios

L'interface doit briser la froideur des gestionnaires de fichiers classiques en proposant **un compagnon vivant, discret et redoutablement accessible**.

```
       /\_/\      💬 [ Analyse sémantique... 76% ]
      ( o.o )
       > ^ <      <-- Le Dino Flottant (Toujours au premier plan)
 ______________________________________________________
|  Que veux-tu savoir ou faire ?                  ⚙️ 🎙️ |
| [ Parle-moi du projet Adrien Profil...             ] |
|______________________________________________________|
```

---

## 🦖 L'Identité Visuelle du "Dino"

### **Le Style**

- **Flat-design** ou **Low-Poly épuré**.
- Petit dinosaure minimaliste qui **flotte sur l'écran** (fenêtre transparente sans bordures, configurée en **Always-on-Top**).

### **Les États d'Âme Animés**

Le personnage ne bouge pas de façon frénétique, il **respire calmement** pour indiquer que le démon de fond tourne. Ses états changent selon l'activité :


| **État**                | **Animation**                                                                 |
| ----------------------- | ----------------------------------------------------------------------------- |
| **Indexation initiale** | Il porte des petites lunettes de lecture ou consulte un mini-livre.           |
| **Écoute Vocale**       | Des petites ondes discrètes apparaissent autour de lui.                       |
| **Réflexion**           | Une bulle de dialogue avec trois petits points clignotants (`...`) s'affiche. |


---

## 💬 La Communication & L'Affichage

### **La Bulle de Pensée**

- Affiche les **informations transitoires**.
- Exemple : Lors du premier scan, la bulle affiche dynamiquement :  
`📥 Indexation... 76%`.

### **Le Panel Déployable**

- **Au clic sur le Dinosaure**, un panneau épuré **glisse vers le bas**.
- Contenu :
  - Une **barre de recherche textuelle unique**.
  - Deux icônes discrètes :
    - **🎙️ Micro** : pour déclencher la dictée vocale native du Mac.
    - **⚙️ Roue crantée** : pour accéder aux réglages.

### **Les Réponses Sémantiques**

- N'symbios affiche sa **réponse textuelle de façon élégante**.
- En dessous, les **fichiers sources trouvés** apparaissent sous forme de :
  - **Petites pastilles cliquables** (badges).
  - **Un clic sur une pastille** ouvre instantanément le fichier ou le dossier dans le **Finder**.

---

À ajouter : La propriété « Repositionnable (Draggable) ». L'utilisateur doit pouvoir cliquer sur le dinosaure pour le glisser-déposer n'importe où sur son écran (ou ses multi-écrans).
Option bonus : Le raccourci clavier global (ex: Cmd + Shift + Espace) pour masquer/afficher instantanément le dinosaure s'il gêne la vue.

---

## 🎨 La Palette de Couleurs (Charte Graphique)

Pour s'intégrer harmonieusement à l'écosystème **macOS** ou **Windows** (Light/Dark mode), la palette utilise des tons **"Ambiants" et technologiques** :


| **Élément**                   | **Couleur**   | **Code Hexadécimal** | **Description**                                                                                    |
| ----------------------------- | ------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| **Fond du Panel (Sombre)**    | Gris ardoise  | `#1E1E24`            | Très profond, légèrement transparent avec un **effet de flou d'arrière-plan (Blur)**.              |
| **Le Dino**                   | Bleu pastel   | `#4A90E2`            | Doux, rassurant et professionnel (personnalisable via des **skins**).                              |
| **Couleur d'Action / Succès** | Vert émeraude | `#2ECC71`            | Vibrant pour les bulles de succès, l'état d'écoute ou la validation des actions **Marie Poppins**. |
| **Texte**                     | Blanc cassé   | `#F5F5F7`            | Iconique pour une **scannabilité maximale** sans agresser les yeux.                                |


---

**Synthèse** : Interface minimaliste et intuitive avec un dinosaure animé, des bulles dynamiques, un panneau déployable et une palette de couleurs adaptée aux modes Light/Dark de macOS/Windows.