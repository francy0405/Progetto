# =====================================================================
#  Dockerfile  —  LA "RICETTA" PER COSTRUIRE L'IMMAGINE DELL'APP
# =====================================================================
#
# Questo file dice a Docker, passo per passo, come impacchettare la nostra
# applicazione Flask dentro un "contenitore": un ambiente isolato che porta
# con se' tutto il necessario (Python, le librerie, il codice). Cosi' l'app
# gira allo stesso identico modo sul nostro PC come su qualsiasi altro.

# Partiamo da un'immagine di base che ha gia' Python 3.13 installato.
# La versione "slim" e' alleggerita: pesa meno e contiene solo l'essenziale.
FROM python:3.13-slim

# Diciamo a Python di NON tenere i messaggi in un buffer ma di stamparli
# subito. Cosi' i log di Flask li vediamo in tempo reale nel terminale.
ENV PYTHONUNBUFFERED=1

# Tutte le operazioni successive avvengono dentro la cartella /app del
# contenitore: e' la nostra "cartella di lavoro".
WORKDIR /app

# TRUCCO PER ANDARE PIU' VELOCE: copiamo PRIMA solo la lista delle librerie
# e le installiamo. Docker tiene in cache questo passaggio: finche' non
# cambiano le dipendenze, alle build successive le ri-usa senza reinstallare
# tutto da capo. Se copiassimo il codice prima, ogni minima modifica al
# codice ci costringerebbe a reinstallare tutte le librerie.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ora copiamo il codice vero e proprio dentro il contenitore.
COPY main.py .
COPY src/ ./src/

# Dichiariamo che l'app dentro il contenitore usa la porta 5000.
EXPOSE 5000

# Il comando che viene eseguito quando il contenitore parte: avvia l'app.
CMD ["python", "main.py"]
