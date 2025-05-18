# -*- coding: utf-8 -*-
# Import necessarie
import math

def calculate_harmonics(frequency):
    harmonics = [frequency * i for i in range(1, 6)]
    return harmonics


def display_harmonics(harmonics):
    for harmonic in harmonics:
        print(f"Harmonic: {harmonic}")

# Esempio di utilizzo
if __name__ == "__main__":
    frequency = 440  # Frequenza di esempio
    harmonics = calculate_harmonics(frequency)
    display_harmonics(harmonics)
