# Dentro DJAnalyzerApp
# ... (analyze_key_internal come prima) ...

def analyze_bpm_internal(y, sr): # Aggiornato per il warning
    try:
        # Aggiornato per librosa >= 0.10.0
        if hasattr(librosa.feature, 'rhythm') and hasattr(librosa.feature.rhythm, 'tempo'):
            tempo_array = librosa.feature.rhythm.tempo(y=y, sr=sr, aggregate=None)
        else: # Fallback per versioni più vecchie di librosa
            tempo_array = librosa.beat.tempo(y=y, sr=sr, aggregate=None)
        
        bpm = int(round(np.median(tempo_array))) if tempo_array.size > 0 else 0
        return bpm
    except Exception as e: print(f"Errore (analyze_bpm_internal): {e}"); return 0

# ... (analyze_energy_rms_internal e altre funzioni come prima) ...

# Dentro DJAnalyzerApp
    def setup_ui(self):
        # ... (inizio di setup_ui come prima) ...
        self.tree = ttk.Treeview(tree_frame, columns=("File", "BPM", "Key", "Camelot", "Colore Camelot", "Compatibili", "Energia RMS", "Colore RMS"), show="headings", yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)
        # ... (configurazione colonne come prima) ...
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        tree_scrollbar_y.config(command=self.tree.yview)
        tree_scrollbar_x.config(command=self.tree.xview)

        # PRE-CONFIGURA TUTTI I TAG COLORE CAMELOT
        for camelot_code, color_name in CAMELOT_COLOR_MAP.items():
            tag_name = color_name.lower().replace(" ", "_").replace("-","_") + "_tag"
            try:
                self.tree.tag_configure(tag_name, background=color_name)
            except tk.TclError:
                print(f"Attenzione: colore non valido per pre-configurazione tag: {color_name} ({tag_name}), uso grigio.")
                self.tree.tag_configure(tag_name, background="grey70")
        # Configura anche il tag di default per N/A o errori se non già coperto
        default_tag = CAMELOT_COLOR_MAP.get("N/A", "grey70").lower().replace(" ", "_").replace("-","_") + "_tag"
        if default_tag not in self.tree.tag_configure():
             self.tree.tag_configure(default_tag, background=CAMELOT_COLOR_MAP.get("N/A", "grey70"))


        # RIMOSSA LA SEZIONE DELLO SPETTROGRAMMA PER TEST
        # ...
    
    # ... (browse_input, browse_output, toggle_pause_analysis, stop_analysis, start_analysis_thread come prima) ...

    # ... (run_full_analysis come prima, si assicura di generare tag_name correttamente) ...
    # in run_full_analysis, la generazione del tag per la coda:
    # camelot_color_for_tag = CAMELOT_COLOR_MAP.get(camelot_val, "grey70")
    # tag_name_for_queue = camelot_color_for_tag.lower().replace(" ", "_").replace("-","_") + "_tag"
    # queue.put({..., "camelot_color_tag": tag_name_for_queue})

    def process_analysis_queue(self):
        try:
            # Processa al massimo N messaggi per evitare di bloccare troppo la GUI
            # anche durante l'elaborazione della coda.
            for _ in range(20): # Processa fino a 20 messaggi per chiamata
                if self.analysis_queue.empty():
                    break 
                message = self.analysis_queue.get_nowait()
                self.handle_queue_message(message)
                self.analysis_queue.task_done()
        except QueueEmpty:
            pass
        except Exception as e:
            print(f"Errore in process_analysis_queue: {e}")
        finally:
            is_thread_alive_now = self.analysis_thread and self.analysis_thread.is_alive()
            
            if is_thread_alive_now or not self.analysis_queue.empty():
                self.after(100, self.process_analysis_queue)
            elif not is_thread_alive_now and self.analysis_queue.empty():
                # Chiamare reset_ui_after_analysis solo se il thread è DAVVERO finito
                # e non è mai stato chiamato prima per questa sessione di analisi
                if not getattr(self, '_analysis_completed_flag', False):
                    self.reset_ui_after_analysis()
                    self._analysis_completed_flag = True # Imposta un flag per evitare chiamate multiple
    
    def start_analysis_thread(self):
        # ...
        self._analysis_completed_flag = False # Resetta il flag all'inizio di una nuova analisi
        # ... (resto della funzione come prima)

    def handle_queue_message(self, message):
        msg_type = message.get("type")
        if msg_type == "status_update": 
            self.current_file_label.set(message.get("message", ""))
            self.last_analysis_status_message = message.get("message", "")
        elif msg_type == "new_row":
            row_data = message.get("data")
            camelot_color_tag_name = message.get("camelot_color_tag") # Questo è già il nome del tag, es. "light_sky_blue_tag"
            
            # Il tag dovrebbe essere già stato configurato in setup_ui
            # Se camelot_color_tag_name è None o vuoto, non applicare nessun tag specifico
            # (o applica un tag di default se vuoi)
            tags_to_apply = ()
            if camelot_color_tag_name:
                tags_to_apply = (camelot_color_tag_name,)
                # Verifica opzionale se il tag esiste, anche se dovrebbe
                # if camelot_color_tag_name not in self.tree.tag_configure():
                #     print(f"ATTENZIONE: Tag {camelot_color_tag_name} non pre-configurato!")
                #     # Potresti configurarlo qui come fallback, ma idealmente è in setup_ui
                #     actual_color_name_from_row = row_data[4] # Colore Camelot è alla quinta posizione (indice 4)
                #     self.tree.tag_configure(camelot_color_tag_name, background=actual_color_name_from_row)


            item_id = self.tree.insert("", "end", values=row_data, tags=tags_to_apply)
            self.tree.see(item_id)
        # ... (resto della gestione messaggi come prima) ...