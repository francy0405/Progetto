"""Application factory di Flask e gestione della connessione PostgreSQL."""

import os

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection as ConnessionePg
from flask import Flask


def ottieni_connessione_db() -> ConnessionePg:
    """Apre e restituisce una nuova connessione PostgreSQL.

    Le credenziali vengono lette esclusivamente dalle variabili d'ambiente
    (caricate da `.env` in `main.py`), cosi' da non esporle mai nel codice. La
    connessione usa `RealDictCursor`, quindi ogni cursore restituisce le righe
    come dizionari (nome colonna -> valore).

    Returns:
        psycopg2 connection: connessione aperta al database.

    Raises:
        psycopg2.Error: se la connessione non puo' essere stabilita.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_DATABASE"),
        port=os.getenv("DB_PORT"),
        cursor_factory=RealDictCursor,
    )


def inizializza_db() -> None:
    """Crea le tabelle `corrieri` e `recensioni` se non esistono.

    L'integrita' referenziale e' garantita a livello di schema:
    `recensioni.id_corriere` e' una FOREIGN KEY su `corrieri.id` con
    `ON DELETE CASCADE`, quindi eliminando un corriere vengono rimosse
    automaticamente le sue recensioni. Un vincolo CHECK limita `voto`
    all'intervallo 1-5; la chiave primaria usa `SERIAL` (auto-incremento di
    PostgreSQL).

    Returns:
        None.
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()
        cursore.execute("""
            CREATE TABLE IF NOT EXISTS corrieri (
                id               SERIAL       PRIMARY KEY,
                nome             VARCHAR(120) NOT NULL,
                veicolo          VARCHAR(60)  NOT NULL,
                consegne_totali  INT          NOT NULL DEFAULT 0
            );
        """)
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
        connessione.commit()
    finally:
        connessione.close()


def crea_app() -> Flask:
    """Istanzia e configura l'applicazione Flask.

    Crea le tabelle PostgreSQL (se non esistono) e registra il blueprint con le
    route. L'import del blueprint avviene qui dentro (non a livello di modulo) per
    evitare import circolari: i moduli handler importano `ottieni_connessione_db`
    da `src.app`.

    Returns:
        Flask: l'applicazione configurata e pronta all'uso.
    """
    from src.routes import bp_api

    inizializza_db()
    app = Flask(__name__)
    app.register_blueprint(bp_api)
    return app
