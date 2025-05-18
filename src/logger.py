# -*- coding: utf-8 -*-
import logging

logging.basicConfig(level=logging.INFO)

def log_message(message):
    logging.info(message)

# Esempio di utilizzo
if __name__ == "__main__":
    log_message("Questo è un messaggio di log di esempio.")
