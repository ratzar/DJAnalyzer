# Dentro la classe DJAnalyzerApp
    def setup_ui(self):
        top_frame = ttk.Frame(self); top_frame.pack(fill=tk.X, padx=10, pady=5)
        input_frame = ttk.LabelFrame(top_frame, text="Cartelle"); input_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Label(input_frame, text="Input:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_folder, width=35)
        self.input_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        self.browse_input_button = ttk.Button(input_frame, text="Sfoglia", command=self.browse_input)
        self.browse_input_button.grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(input_frame, text="Output:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.output_entry = ttk.Entry(input_frame, textvariable=self.output_folder, width=35)
        self.output_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        self.browse_output_button = ttk.Button(input_frame, text="Sfoglia", command=self.browse_output)
        self.browse_output_button.grid(row=1, column=2, padx=5, pady=2)
        input_frame.columnconfigure(1, weight=1)

        action_buttons_frame = ttk.LabelFrame(top_frame, text="Azioni")
        action_buttons_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        self.start_button = ttk.Button(action_buttons_frame, text="Avvia Analisi", command=self.start_analysis_thread)
        self.start_button.pack(pady=2, padx=5, fill=tk.X)
        self.pause_button = ttk.Button(action_buttons_frame, text="Pausa Analisi", command=self.toggle_pause_analysis, state=tk.DISABLED)
        self.pause_button.pack(pady=2, padx=5, fill=tk.X)
        self.stop_button = ttk.Button(action_buttons_frame, text="Ferma Analisi", command=self.stop_analysis, state=tk.DISABLED)
        self.stop_button.pack(pady=2, padx=5, fill=tk.X)
        
        ttk.Label(self, textvariable=self.current_file_label, font=("Segoe UI", 9)).pack(pady=(0,5), fill=tk.X, padx=10, anchor=tk.W)

        tree_frame = ttk.Frame(self); tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree_sb_y = ttk.Scrollbar(tree_frame, orient="vertical"); tree_sb_y.pack(side="right", fill="y")
        tree_sb_x = ttk.Scrollbar(tree_frame, orient="horizontal"); tree_sb_x.pack(side="bottom", fill="x")
        
        self.tree_columns = ("File", "BPM", "Key", "Camelot", "Colore Camelot", "Compatibili", "Energia RMS", "Colore RMS")
        self.tree = ttk.Treeview(tree_frame, columns=self.tree_columns, show="headings", 
                                 yscrollcommand=tree_sb_y.set, xscrollcommand=tree_sb_x.set)
        cols_conf = {"File":230,"BPM":40,"Key":50,"Camelot":50,"Colore Camelot":90,"Compatibili":120,"Energia RMS":80,"Colore RMS":90}
        for col, wd in cols_conf.items():
            anc = tk.W if col in ["File", "Compatibili", "Colore Camelot"] else tk.CENTER
            self.tree.heading(col, text=col, anchor=anc); self.tree.column(col, width=wd, minwidth=max(30,wd//2), anchor=anc)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        tree_sb_y.config(command=self.tree.yview); tree_sb_x.config(command=self.tree.xview)

        # Pre-configura i tag colore per Camelot
        for camelot_key_code_map_key, color_name_val in CAMELOT_COLOR_MAP.items(): # Iteriamo sulla mappa Camelot -> Colore
            tag_name = color_name_val.lower().replace(" ", "_").replace("-", "_") + "_tag" 
            try:
                self.tree.tag_configure(tag_name, background=color_name_val)
            except tk.TclError: # Se il colore non è valido per Tkinter
                print(f"Attenzione: colore Tkinter non valido '{color_name_val}' per tag '{tag_name}'. Uso grigio.")
                self.tree.tag_configure(tag_name, background="grey70")
        
        # Configura il tag di default per N/A o errori se non già coperto
        default_color_name = CAMELOT_COLOR_MAP.get("N/A", "grey70")
        default_tag_name = default_color_name.lower().replace(" ", "_").replace("-","_") + "_tag"
        
        # Correzione: self.tree.tag_configure() senza argomenti restituisce una tupla dei nomi dei tag.
        # Quindi controlliamo se default_tag_name è in questa tupla.
        if default_tag_name not in self.tree.tag_configure(): # <<<<<<<<<<< CORREZIONE QUI
             try:
                self.tree.tag_configure(default_tag_name, background=default_color_name)
             except tk.TclError:
                self.tree.tag_configure(default_tag_name, background="grey70") # Fallback finale
        
        self.spectrum_display_frame = ttk.LabelFrame(self, text="Spettro Audio (Disattivato)")
        self.spectrum_display_frame.pack(fill=tk.X, expand=False, padx=10, pady=(0,5), ipady=5)
        ttk.Label(self.spectrum_display_frame, text="Visualizzazione spettrogramma temporaneamente disattivata per test performance GUI.").pack(padx=5, pady=10)