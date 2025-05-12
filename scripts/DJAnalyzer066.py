    def reset_ui_after_analysis(self):
        print("THREADING: UI resettata (pulsanti e flag).")
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Pausa")
        self.stop_button.config(state=tk.DISABLED)
        self.select_input_button.config(state=tk.NORMAL)
        self.select_output_button.config(state=tk.NORMAL)
        
        self.is_paused = False
        # NON resettare self.stop_requested qui, viene gestito da start_analysis
        
        # Pulisci la coda per evitare che messaggi vecchi vengano processati se si riavvia subito
        # Questo potrebbe essere il punto critico se la ripetizione è causata da messaggi residui
        # o da una chiamata non intenzionale a process_queue
        print("THREADING: Tentativo di svuotare la coda durante il reset finale.")
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
                print("THREADING: Messaggio rimosso dalla coda durante il reset.")
            except queue.Empty:
                print("THREADING: Coda già vuota durante il reset finale.")
                break
        
        self.analysis_thread = None # Resetta il riferimento al thread