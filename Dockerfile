# =====================================================================
#  Dockerfile  —  LA "RICETTA" PER COSTRUIRE L'IMMAGINE DELL'APP
# =====================================================================
#
# Questo file racconta a Docker, passo per passo, come impacchettare la
# nostra applicazione Flask dentro un "contenitore": un ambiente isolato che
# si porta dietro tutto il necessario - Python, le librerie e il codice. E'
# proprio grazie a questo che l'app gira allo stesso identico modo sul nostro
# PC come su qualsiasi altra macchina.

# Partiamo da un'immagine di base che ha gia' Python 3.13 installato. La
# versione "slim" e' alleggerita: pesa meno e contiene solo l'essenziale.
FROM python:3.13-slim

# Diciamo a Python di non tenere i messaggi in un buffer ma di stamparli
# subito, cosi' i log di Flask li vediamo comparire in tempo reale nel
# terminale.
ENV PYTHONUNBUFFERED=1

# Da qui in poi tutte le operazioni avvengono dentro la cartella /app del
# contenitore: e' la nostra "cartella di lavoro".
WORKDIR /app

# Un piccolo trucco per andare piu' veloci: copiamo prima soltanto la lista
# delle librerie e le installiamo. Docker tiene in cache questo passaggio, e
# finche' le dipendenze non cambiano lo riusa senza reinstallare tutto da
# capo. Se invece copiassimo subito il codice, ogni minima modifica ci
# costringerebbe a reinstallare tutte le librerie da zero.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Solo ora copiamo il codice vero e proprio dentro il contenitore.
COPY main.py .
COPY src/ ./src/

# Dichiariamo che l'app, dentro il contenitore, usa la porta 5000.
EXPOSE 5000

# E questo e' il comando che parte all'avvio del contenitore: lancia l'app.
CMD ["python", "main.py"]
