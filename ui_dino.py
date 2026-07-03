import os
import sys
import time
import threading
import sqlite3
import json
import tkinter as tk
import customtkinter as ctk
import lancedb
import re
import subprocess
import ollama
from rank_bm25 import BM25Okapi
from datetime import datetime  # NOUVEAU : Pour la gestion de l'heure

from config import TABLE_NAME, MOTEUR_REFLEXION
from retrieval import recherche_hybride

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class NsymbiosUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ==========================================
        #  ⚙️ CONFIGURATION DE LA FENÊTRE
        # ==========================================
        self.title("N'symbios Core - OS Sémantique")
        self.geometry("800x700") 
        
        screen_width = self.winfo_screenwidth()
        spawn_x = int((screen_width / 2) - (800 / 2))
        self.geometry(f"800x700+{spawn_x}+100")

        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.config(background="#1a1a1a")
        self.attributes("-alpha", 0.96)

        # 🧠 INITIALISATION MÉMOIRE & SESSIONS
        self.chat_history = []
        self.sources_conversation = set() 
        self.current_conv_id = None 

        self.initialiser_db_conversations()
        self.initialiser_moteurs()

        # ==========================================
        #       🎨 CRÉATION DE L'INTERFACE UI
        # ==========================================
        
        # --- HEADER (Recherche & Historique) ---
        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.pack(fill="x", padx=20, pady=(20, 10))
        
        self.entry_recherche = ctk.CTkEntry(
            self.frame_header, 
            placeholder_text="Que veux-tu savoir, DredGuer ?...",
            height=50, font=("Arial", 16),
            corner_radius=10, fg_color="#2b2b2b", border_color="#3b3b3b"
        )
        self.entry_recherche.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_recherche.bind("<Return>", self.lancer_recherche_thread)

        self.combo_historique = ctk.CTkOptionMenu(
            self.frame_header, 
            values=["Nouvelle Session"], 
            command=self.charger_conversation,
            width=150, height=50, fg_color="#34495e", button_color="#2c3e50"
        )
        self.combo_historique.pack(side="right")
        self.rafraichir_historique()

        # --- BODY (Chat) ---
        self.zone_reponse = ctk.CTkTextbox(
            self, height=450, font=("Arial", 14),
            corner_radius=10, fg_color="#222222", border_color="#2d2d2d",
            border_width=1, wrap="word"
        )
        self.zone_reponse.pack(pady=5, padx=20, fill="both", expand=True)
        self.ecrire_ui_simple("🦖 N'symbios connecté. Prêt à naviguer dans tes projets.\nPresse 'Échap' pour fermer l'interface.\n" + "-"*50 + "\n")

        # --- BOTTOM (Sources) ---
        self.frame_sources = ctk.CTkScrollableFrame(self, height=60, fg_color="transparent", orientation="horizontal")
        self.frame_sources.pack(pady=5, padx=20, fill="x")

        # --- FOOTER (Statut & Boutons) ---
        self.frame_footer = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_footer.pack(fill="x", padx=30, pady=(5, 15))

        self.label_status = ctk.CTkLabel(self.frame_footer, text="Moteur V8.4 | Prêt", font=("Arial", 11), text_color="#666666")
        self.label_status.pack(side="left")

        self.btn_quitter = ctk.CTkButton(
            self.frame_footer, text="Fermer (Échap)", width=100, height=25,
            fg_color="#333333", hover_color="#c0392b", command=self.destroy, corner_radius=6
        )
        self.btn_quitter.pack(side="right")

        self.btn_nouvelle = ctk.CTkButton(
            self.frame_footer, text="Nouvelle Conv.", width=100, height=25,
            fg_color="#2980b9", hover_color="#3498db", command=self.nouvelle_conversation, corner_radius=6
        )
        self.btn_nouvelle.pack(side="right", padx=(0, 10))

        self.bind("<Escape>", lambda e: self.destroy())
        self.entry_recherche.focus_set()

    # ==========================================
    #      🗄️ GESTION SQLITE (CONVERSATIONS)
    # ==========================================
    def initialiser_db_conversations(self):
        conn = sqlite3.connect("symbios_meta.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      titre TEXT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      messages TEXT,
                      sources TEXT)''')
        conn.commit()
        conn.close()

    def rafraichir_historique(self):
        conn = sqlite3.connect("symbios_meta.db")
        c = conn.cursor()
        c.execute("SELECT id, titre FROM conversations ORDER BY timestamp DESC LIMIT 20")
        convs = c.fetchall()
        conn.close()
        
        values = ["Nouvelle Session"] + [f"{row[0]} - {row[1]}" for row in convs]
        self.combo_historique.configure(values=values)
        if self.current_conv_id is None:
            self.combo_historique.set("Nouvelle Session")

    def sauvegarder_conversation(self, premiere_question):
        titre = premiere_question[:25] + "..." if len(premiere_question) > 25 else premiere_question
        msgs_json = json.dumps(self.chat_history)
        srcs_json = json.dumps(list(self.sources_conversation))
        
        conn = sqlite3.connect("symbios_meta.db")
        c = conn.cursor()
        if self.current_conv_id is None:
            c.execute("INSERT INTO conversations (titre, messages, sources) VALUES (?, ?, ?)", (titre, msgs_json, srcs_json))
            self.current_conv_id = c.lastrowid
        else:
            c.execute("UPDATE conversations SET messages = ?, sources = ? WHERE id = ?", (msgs_json, srcs_json, self.current_conv_id))
        conn.commit()
        conn.close()
        self.rafraichir_historique()
        self.combo_historique.set(f"{self.current_conv_id} - {titre}")

    def charger_conversation(self, selection):
        if selection == "Nouvelle Session":
            self.nouvelle_conversation()
            return

        conv_id = int(selection.split(" - ")[0])
        conn = sqlite3.connect("symbios_meta.db")
        c = conn.cursor()
        c.execute("SELECT messages, sources FROM conversations WHERE id = ?", (conv_id,))
        row = c.fetchone()
        conn.close()

        if row:
            self.chat_history = json.loads(row[0])
            self.sources_conversation = set(json.loads(row[1]))
            self.current_conv_id = conv_id
            
            self.zone_reponse.configure(state="normal")
            self.zone_reponse.delete("0.0", tk.END)
            self.ecrire_ui_simple(f"🔄 Session rechargée : {selection}\n" + "-"*50 + "\n")
            
            # Réaffichage avec les dates/heures si elles existent
            for msg in self.chat_history:
                prefix = "👤 Toi" if msg['role'] == 'user' else "🦖 N'symbios"
                ts = msg.get('timestamp', '')
                ts_str = f" [{ts}]" if ts else ""
                
                if msg['role'] == 'user':
                    self.ecrire_ui_simple(f"{prefix}{ts_str} : {msg['content']}\n")
                else:
                    self.ecrire_ui_simple(f"{prefix}{ts_str} :")
                    self.ecrire_ui_avec_citations(msg['content'])
                
            self.afficher_sources_ui([])

    def nouvelle_conversation(self):
        self.chat_history.clear()
        self.sources_conversation.clear()
        self.current_conv_id = None
        
        self.zone_reponse.configure(state="normal")
        self.zone_reponse.delete("0.0", tk.END)
        self.ecrire_ui_simple("🦖 Nouvelle conversation démarrée.\n" + "-"*50 + "\n")
        
        for widget in self.frame_sources.winfo_children():
            widget.destroy()
            
        self.combo_historique.set("Nouvelle Session")
        self.label_status.configure(text="Mémoire réinitialisée")
        self.entry_recherche.focus_set()

    # ==========================================
    #      🧠 MOTEURS RAG ET AFFICHAGE UI
    # ==========================================
    def initialiser_moteurs(self):
        try:
            self.db = lancedb.connect("./base_memoire_locale")
            self.table = self.db.open_table(TABLE_NAME)
            
            df_all = self.table.search().limit(100000).to_pandas()
            self.corpus_textes = df_all['texte'].tolist()
            self.corpus_chemins = df_all['chemin_absolu'].tolist()
            self.corpus_ids = df_all['fragment_id'].tolist()
            
            tokenized_corpus = [re.findall(r'\w+', doc.lower()) for doc in self.corpus_textes]
            self.bm25 = BM25Okapi(tokenized_corpus)
        except Exception as e:
            print(f"⚠️ Erreur BDD : {e}")
            sys.exit(1)

    def charger_couche_0(self):
        try:
            conn = sqlite3.connect("symbios_meta.db")
            cursor = conn.cursor()
            cursor.execute("SELECT nom_projet, description FROM semantic_projects")
            projets = cursor.fetchall()
            conn.close()
            carte = "CARTE GLOBALE:\n"
            for nom, desc in projets: carte += f"- [{nom}] : {desc}\n"
            return carte
        except Exception: return "Carte globale non disponible."

    def ecrire_ui_simple(self, texte):
        self.zone_reponse.configure(state="normal")
        self.zone_reponse.insert(tk.END, texte + "\n")
        self.zone_reponse.yview(tk.END) 
        self.zone_reponse.configure(state="disabled")
        self.update_idletasks()

    def ecrire_ui_avec_citations(self, texte):
        self.zone_reponse.configure(state="normal")
        map_chemins = {os.path.basename(c): c for c in self.sources_conversation}
        parts = re.split(r'(\[.*?\])', texte)
        
        for part in parts:
            if part.startswith('[') and part.endswith(']'):
                nom_fichier = part[1:-1]
                
                # --- NOUVEAU : Nettoyage du nom des fichiers JSON ---
                nom_affichage = nom_fichier
                if nom_fichier.endswith('.json') and nom_fichier.startswith('chat-'):
                    nom_affichage = "Archive de Conversation"
                # ----------------------------------------------------

                if nom_fichier in map_chemins:
                    chemin_abs = map_chemins[nom_fichier]
                    # Le tag doit rester unique, on utilise un hash du nom d'origine
                    tag_name = f"link_{abs(hash(nom_fichier))}" 
                    
                    # On insère le nom propre au lieu du nom barbare
                    self.zone_reponse.insert(tk.END, f"[{nom_affichage}]", tag_name)
                    
                    self.zone_reponse.tag_config(tag_name, foreground="#3498db", underline=True)
                    self.zone_reponse._textbox.tag_bind(tag_name, "<Button-1>", lambda e, c=chemin_abs: subprocess.run(['open', c]))
                    self.zone_reponse._textbox.tag_bind(tag_name, "<Enter>", lambda e: self.zone_reponse._textbox.configure(cursor="hand2"))
                    self.zone_reponse._textbox.tag_bind(tag_name, "<Leave>", lambda e: self.zone_reponse._textbox.configure(cursor="arrow"))
                else:
                    self.zone_reponse.insert(tk.END, part)
            else:
                self.zone_reponse.insert(tk.END, part)
                
        self.zone_reponse.insert(tk.END, "\n" + "-"*50 + "\n")
        self.zone_reponse.yview(tk.END)
        self.zone_reponse.configure(state="disabled")
        self.update_idletasks()

    def afficher_sources_ui(self, nouveaux_chemins):
        self.sources_conversation.update(nouveaux_chemins)
        for widget in self.frame_sources.winfo_children(): widget.destroy()
            
        for chemin in self.sources_conversation:
            nom_fichier = os.path.basename(chemin)
            
            # --- NOUVEAU : Nettoyage pour les boutons ---
            texte_bouton = nom_fichier
            if nom_fichier.endswith('.json') and nom_fichier.startswith('chat-'):
                texte_bouton = "Archive de Conv."
            # ---------------------------------------------

            btn = ctk.CTkButton(
                self.frame_sources, text=f"📄 {texte_bouton}", 
                command=lambda c=chemin: subprocess.run(['open', c]),
                fg_color="#1f2937", hover_color="#374151", corner_radius=15, height=28
            )
            btn.pack(side="left", padx=5)

    def lancer_recherche_thread(self, event=None):
        question = self.entry_recherche.get()
        if not question.strip(): return
        
        self.entry_recherche.delete(0, tk.END)
        
        # NOUVEAU : On récupère l'heure de la question
        timestamp_user = datetime.now().strftime("%d/%m/%y %H:%M:%S")
        self.ecrire_ui_simple(f"\n👤 Toi [{timestamp_user}] : {question}")
        self.label_status.configure(text="🔍 RAG et réflexion en cours...")
        
        threading.Thread(target=self.processus_reflexion, args=(question, timestamp_user), daemon=True).start()

    def processus_reflexion(self, question, timestamp_user):
        start_time = time.time()
        
        # --- NOUVEAU : 1. REFORMULATION DE LA RECHERCHE (Query Expansion) ---
        requete_recherche = question
        
        # S'il y a déjà une conversation, on crée une requête enrichie pour le RAG
        if len(self.chat_history) > 0:
            # On prend la dernière réponse de l'IA pour le contexte
            dernier_sujet = self.chat_history[-1]['content'][:400] 
            
            # --- NOUVEAU PROMPT DE REFORMULATION ULTRA-STRICT ---
            prompt_reformulation = f"""
            Agis comme un expert en moteurs de recherche.
            Contexte de la conversation en cours : "{dernier_sujet}"
            Question imprécise de l'utilisateur : "{question}"
            
            TÂCHE : Reformule la question de l'utilisateur pour qu'elle soit parfaite pour un moteur de recherche documentaire.
            RÈGLES VITALES :
            1. Remplace OBLIGATOIREMENT les termes vagues ("les deux", "il", "ça", "ce projet") par les VRAIS noms des projets évoqués dans le contexte (ex: PulMind, NVNC, Jarvis).
            2. Ne retourne STRICTEMENT QUE la phrase reformulée, sans aucune introduction.
            """
            
            try:
                if MOTEUR_REFLEXION == "API":
                    from openai import OpenAI
                    from config import CLE_API_OPENAI, GENERATION_MODEL_API
                    client = OpenAI(api_key=CLE_API_OPENAI)
                    res = client.chat.completions.create(
                        model=GENERATION_MODEL_API, 
                        messages=[{"role": "user", "content": prompt_reformulation}],
                        max_tokens=60
                    )
                    requete_recherche = res.choices[0].message.content.strip()
                else:
                    from config import GENERATION_MODEL_OLLAMA
                    res = ollama.generate(model=GENERATION_MODEL_OLLAMA, prompt=prompt_reformulation)
                    requete_recherche = res['response'].strip()
            except:
                pass 
                
        # 💡 ASTUCE DEBUG : Regarde ton terminal quand tu poses une question !
        print(f"\n🔍 [DEBUG RAG] Question d'origine : {question}")
        print(f"🔍 [DEBUG RAG] Requête envoyée au moteur : {requete_recherche}\n")
        # ----------------------------------------------------------------------

        # 2. Le RAG utilise la requête reformulée, pas le petit "continue"
        resultats = recherche_hybride(requete_recherche, self.table, self.bm25, self.corpus_textes, self.corpus_chemins, self.corpus_ids)
        contexte_fragments = "\n".join([f"- {r['texte']}" for r in resultats])
        carte_globale = self.charger_couche_0()

        # 3. On ajuste le prompt pour lui permettre de dire "Je ne sais pas"
        messages_api = [{
            "role": "system", 
            "content": f"""Tu es N'symbios. Utilise la CARTE GLOBALE et les FRAGMENTS. 
            RÈGLES ABSOLUES :
            1. Dès que tu affirmes un fait issu d'un fragment, tu DOIS citer le fichier entre crochets, ex: [nom_fichier.md].
            2. Si les fragments ne parlent pas du tout du sujet demandé, NE FAIS PAS de suppositions forcées. Dis-le simplement.
            \n\n{carte_globale}"""
        }]
        
        for msg in self.chat_history:
            messages_api.append({"role": msg["role"], "content": msg["content"]})
            
        messages_api.append({"role": "user", "content": f"FRAGMENTS DE DONNÉES :\n{contexte_fragments}\n\nQUESTION :\n{question}"})

        # ... (Le reste de la méthode processus_reflexion reste strictement identique) ...
        try:
            if MOTEUR_REFLEXION == "API":
                from openai import OpenAI
                from config import CLE_API_OPENAI, GENERATION_MODEL_API
                client = OpenAI(api_key=CLE_API_OPENAI)
                res_api = client.chat.completions.create(model=GENERATION_MODEL_API, messages=messages_api)
                reponse_ia = res_api.choices[0].message.content
            else:
                from config import GENERATION_MODEL_OLLAMA
                res_ollama = ollama.chat(model=GENERATION_MODEL_OLLAMA, messages=messages_api)
                reponse_ia = re.sub(r'<\|channel>thought.*?<channel\|>', '', res_ollama['message']['content'], flags=re.DOTALL).strip()
        except Exception as e:
            reponse_ia = f"❌ Erreur : {e}"

        # NOUVEAU : On récupère l'heure de la réponse
        timestamp_ia = datetime.now().strftime("%d/%m/%y %H:%M:%S")

        # SAUVEGARDE EN MÉMOIRE LOCALE AVEC L'HEURE (La base de données s'en fiche de la structure)
        self.chat_history.append({"role": "user", "content": question, "timestamp": timestamp_user})
        self.chat_history.append({"role": "assistant", "content": reponse_ia, "timestamp": timestamp_ia})

        chemins = set(r['chemin_absolu'] for r in resultats if "INDEX" not in r['chemin_absolu'])
        self.sources_conversation.update(chemins)
        self.sauvegarder_conversation(question if len(self.chat_history) <= 2 else self.chat_history[0]['content'])

        temps_total = (time.time() - start_time) * 1000
        
        self.after(0, self.ecrire_ui_simple, f"\n🦖 N'symbios [{timestamp_ia}] :")
        self.after(0, self.ecrire_ui_avec_citations, reponse_ia)
        self.after(0, self.afficher_sources_ui, [])
        self.after(0, lambda: self.label_status.configure(text=f"V8.4 | Répondu en {temps_total:.0f} ms | Session {self.current_conv_id}"))

if __name__ == "__main__":
    app = NsymbiosUI()
    app.mainloop()