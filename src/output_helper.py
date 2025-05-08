def init_output(widget):
    """
    Imposta il widget in sola lettura.
    """
    widget.configure(state="disabled")


def append_output(widget, text):
    """
    Aggiunge `text` a `widget`, scroll automatico e aggiornamento GUI.
    """
    widget.configure(state="normal")
    widget.insert("end", text + "\n")
    widget.see("end")
    widget.configure(state="disabled")
    # forza aggiornamento GUI per scroll
    try:
        widget.update_idletasks()
        widget.update()
    except Exception:
        pass


def clear_output(widget):
    """
    Pulisce il contenuto di `widget`.
    """
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.configure(state="disabled")
