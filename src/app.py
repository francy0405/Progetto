"""
=====================================================================
 src/app.py  —  IL CUORE DELL'APPLICAZIONE
=====================================================================

Qui dentro succedono tre cose fondamentali:

  1) ci colleghiamo al database PostgreSQL;
  2) creiamo le tabelle (se non esistono ancora);
  3) costruiamo e configuriamo l'app Flask vera e propria.

E' il file piu' importante: tutti gli altri pezzi del programma
chiedono a lui di aprire la connessione al database.
"""

import os

# psycopg2 e' la libreria che ci permette di "parlare" con PostgreSQL
# direttamente da Python: apre la connessione, manda le query, riceve i dati.
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection as ConnessionePg
from flask import Flask


def ottieni_connessione_db() -> ConnessionePg:
    """Apre una nuova connessione al database e la restituisce.

    In pratica e' come "chiamare al telefono" il database: ogni volta
    che dobbiamo leggere o scrivere dati, prima apriamo questa linea.

    Due dettagli importanti da raccontare alla presentazione:

    - Le password NON sono scritte nel codice: le leggiamo dalle variabili
      d'ambiente (che arrivano dal file .env). Cosi' il codice resta pulito
      e non rischiamo di pubblicare le credenziali su GitHub.

    - Usiamo "RealDictCursor": grazie a questo, i risultati del database
      ci tornano gia' come dizionari Python (nome_colonna -> valore),
      invece che come semplici liste di valori. E' molto piu' comodo da
      trasformare poi in JSON da mandare al client.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),          # indirizzo del database
        user=os.getenv("DB_USER"),          # nome utente
        password=os.getenv("DB_PASSWORD"),  # password (mai scritta nel codice!)
        dbname=os.getenv("DB_DATABASE"),    # nome del database da usare
        port=os.getenv("DB_PORT"),          # porta su cui risponde PostgreSQL
        cursor_factory=RealDictCursor,      # ci fa avere le righe come dizionari
    )


def inizializza_db() -> None:
    """Crea le due tabelle del progetto, ma solo se non esistono gia'.

    Lanciamo questa funzione all'avvio: cosi' la prima volta che parte il
    programma il database si "prepara" da solo, senza bisogno che qualcuno
    crei le tabelle a mano.

    Le tabelle sono due e sono COLLEGATE tra loro:

      - "corrieri"   -> chi fa le consegne;
      - "recensioni" -> i voti che i clienti danno ai corrieri.

    Il collegamento e' la riga "FOREIGN KEY ... ON DELETE CASCADE":
    significa che ogni recensione e' legata a un corriere, e se cancelliamo
    un corriere, PostgreSQL cancella in automatico anche tutte le sue
    recensioni. Non rimangono recensioni "orfane".

    Da notare anche:
      - SERIAL = numero che si incrementa da solo (1, 2, 3...). Non dobbiamo
        pensare noi all'id: lo gestisce il database.
      - CHECK (voto BETWEEN 1 AND 5) = il database stesso rifiuta voti fuori
        scala. E' una rete di sicurezza in piu', oltre ai controlli in Python.
    """
    # Apriamo la connessione...
    connessione = ottieni_connessione_db()
    try:
        # ...e creiamo un "cursore", cioe' lo strumento con cui mandiamo
        # i comandi SQL al database.
        cursore = connessione.cursor()

        # Tabella dei CORRIERI.
        cursore.execute("""
            CREATE TABLE IF NOT EXISTS corrieri (
                id               SERIAL       PRIMARY KEY,
                nome             VARCHAR(120) NOT NULL,
                veicolo          VARCHAR(60)  NOT NULL,
                consegne_totali  INT          NOT NULL DEFAULT 0
            );
        """)

        # Tabella delle RECENSIONI, collegata ai corrieri.
        cursore.execute("""
            CREATE TABLE IF NOT EXISTS recensioni (
                id            SERIAL       PRIMARY KEY,
                id_corriere   INT          NOT NULL,
                nome_cliente  VARCHAR(120) NOT NULL,
                voto          INT          NOT NULL,
                commento      VARCHAR(500),
                CONSTRAINT fk_recensioni_corriere
                    FOREIGN KEY (id_corriere) REFERENCES corrieri(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                CONSTRAINT chk_voto CHECK (voto BETWEEN 1 AND 5)
            );
        """)

        # "commit" = conferma e salva davvero le modifiche nel database.
        # Senza questo, i comandi resterebbero in sospeso e non verrebbero salvati.
        connessione.commit()
    finally:
        # Qualunque cosa succeda (anche in caso di errore), chiudiamo sempre
        # la connessione: e' come riagganciare il telefono per non lasciare
        # linee aperte inutilmente.
        connessione.close()


def crea_app() -> Flask:
    """Costruisce e prepara l'applicazione Flask, pronta a ricevere richieste.

    E' la "fabbrica" che mette insieme tutti i pezzi:
      1) crea le tabelle (chiamando inizializza_db);
      2) accende Flask;
      3) collega le route (gli indirizzi web tipo /corrieri, /recensioni...).

    Piccolo dettaglio tecnico da spiegare se chiedono: l'import del blueprint
    lo facciamo QUI DENTRO e non in cima al file. Il motivo e' evitare un
    "import circolare": i file delle route hanno bisogno di questo file
    (per la connessione al database), e questo file ha bisogno di loro (per
    le route). Importando qui dentro, al momento giusto, evitiamo che si
    inseguano a vicenda creando un errore.
    """
    from src.routes import bp_api

    inizializza_db()                  # prepariamo il database
    app = Flask(__name__)             # accendiamo Flask
    app.register_blueprint(bp_api)    # colleghiamo tutte le route
    return app                        # restituiamo l'app pronta all'uso
