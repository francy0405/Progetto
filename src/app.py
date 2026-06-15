"""
=====================================================================
 src/app.py  —  IL CUORE DELL'APPLICAZIONE
=====================================================================

Questo e' il file piu' importante del progetto, perche' qui dentro
succedono tre cose fondamentali, una dietro l'altra: ci colleghiamo al
database PostgreSQL, creiamo le tabelle se non esistono ancora e infine
costruiamo e configuriamo l'app Flask vera e propria. Non a caso tutti gli
altri pezzi del programma, quando hanno bisogno di parlare col database,
passano sempre da qui.
"""

import os

# psycopg2 e' la libreria che ci permette di "parlare" con PostgreSQL
# direttamente da Python: e' lei che apre la connessione, manda le query e
# ci riporta indietro i dati.
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection as ConnessionePg
from flask import Flask


def ottieni_connessione_db() -> ConnessionePg:
    """Apre una nuova connessione al database e la restituisce.

    Possiamo immaginarla come una telefonata al database: ogni volta che
    dobbiamo leggere o scrivere qualcosa, per prima cosa apriamo questa
    linea. Ci sono due dettagli che vale la pena raccontare in presentazione.
    Il primo riguarda la sicurezza: le credenziali non sono scritte nel
    codice ma lette dalle variabili d'ambiente (che arrivano dal file .env),
    cosi' il sorgente resta pulito e non rischiamo di pubblicare le password
    su GitHub. Il secondo e' una comodita': grazie a "RealDictCursor" i
    risultati ci tornano gia' come dizionari Python (nome della colonna ->
    valore) invece che come semplici liste di valori, e questo li rende
    immediati da trasformare poi in JSON da mandare al client.
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

    La lanciamo all'avvio, cosi' la prima volta che parte il programma il
    database si prepara da solo, senza che nessuno debba creare le tabelle a
    mano. E' un punto importante da sottolineare: e' questa funzione, e
    nessun altro, a costruire lo schema del database. Parte da un database
    completamente vuoto e lo rende pronto all'uso; il fatto che usi
    "CREATE TABLE IF NOT EXISTS" significa anche che possiamo riavviare
    l'app quante volte vogliamo senza mai rischiare di duplicare o
    sovrascrivere le tabelle gia' presenti.

    Le tabelle sono due e sono collegate tra loro: "corrieri", cioe' chi fa
    le consegne, e "recensioni", cioe' i voti che i clienti lasciano ai
    corrieri. A tenerle insieme e' la riga "FOREIGN KEY ... ON DELETE
    CASCADE", che dice una cosa precisa: ogni recensione e' agganciata a un
    corriere, e se cancelliamo quel corriere PostgreSQL elimina in automatico
    anche tutte le sue recensioni, senza lasciarne in giro di "orfane".
    Meritano un cenno anche altri due dettagli: "SERIAL" e' un numero che si
    incrementa da solo (1, 2, 3...), quindi all'id non dobbiamo pensare noi
    ma ci pensa il database; e "CHECK (voto BETWEEN 1 AND 5)" fa si' che sia
    il database stesso a rifiutare i voti fuori scala, una rete di sicurezza
    in piu' che si aggiunge ai controlli che facciamo gia' in Python.
    """
    # Apriamo la connessione...
    connessione = ottieni_connessione_db()
    try:
        # ...e ci procuriamo un "cursore", cioe' lo strumento con cui mandiamo
        # i comandi SQL al database.
        cursore = connessione.cursor()

        # La tabella dei CORRIERI.
        cursore.execute("""
            CREATE TABLE IF NOT EXISTS corrieri (
                id               SERIAL       PRIMARY KEY,
                nome             VARCHAR(120) NOT NULL,
                veicolo          VARCHAR(60)  NOT NULL,
                consegne_totali  INT          NOT NULL DEFAULT 0
            );
        """)

        # La tabella delle RECENSIONI, collegata ai corrieri.
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

        # Con "commit" confermiamo e salviamo davvero le modifiche nel
        # database: senza questo passaggio i comandi resterebbero in sospeso e
        # non verrebbero mai scritti per davvero.
        connessione.commit()
    finally:
        # Qualunque cosa succeda, anche in caso di errore, chiudiamo sempre la
        # connessione: e' come riagganciare il telefono per non lasciare linee
        # aperte inutilmente.
        connessione.close()


def crea_app() -> Flask:
    """Costruisce e prepara l'applicazione Flask, pronta a ricevere richieste.

    E' la "fabbrica" che mette insieme tutti i pezzi: per prima cosa crea le
    tabelle chiamando inizializza_db, poi accende Flask e infine collega le
    route, cioe' gli indirizzi web come /corrieri o /recensioni. C'e' un
    dettaglio tecnico che a volte viene chiesto: l'import del blueprint lo
    facciamo qui dentro e non in cima al file. Il motivo e' evitare un
    "import circolare" - i file delle route hanno bisogno di questo file (per
    la connessione al database) e questo file ha bisogno di loro (per le
    route): importando al momento giusto, qui dentro, evitiamo che si
    rincorrano a vicenda generando un errore.
    """
    from src.routes import bp_api

    inizializza_db()                  # prepariamo il database
    app = Flask(__name__)             # accendiamo Flask
    app.register_blueprint(bp_api)    # colleghiamo tutte le route
    return app                        # restituiamo l'app pronta all'uso
