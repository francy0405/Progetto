"""
=====================================================================
 src/handlers/corriere_handler.py  —  LA LOGICA DEI CORRIERI
=====================================================================

Qui c'e' il "lavoro vero" sui corrieri: leggere la lista, cancellarne
uno, calcolare la media dei voti. Sono queste le funzioni che parlano
davvero col database scrivendo le query SQL.

Le route (in routes.py) si limitano a chiamare queste funzioni: e' una
divisione dei compiti che tiene il codice ordinato.

UN DETTAGLIO DI SICUREZZA IMPORTANTE (da sottolineare in presentazione):
in tutte le query NON incolliamo mai i valori dentro la stringa SQL "a mano".
Usiamo invece i segnaposto "%s" e passiamo i valori a parte. Cosi' psycopg2
li inserisce in modo sicuro. Questo ci protegge dalla "SQL injection",
cioe' da chi prova a infilare comandi malevoli al posto dei dati.
"""

from typing import Any, Dict, List, Optional

# Chiediamo al cuore dell'app (app.py) di aprirci la connessione al database.
from src.app import ottieni_connessione_db


def leggi_corrieri(veicolo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Restituisce l'elenco dei corrieri, eventualmente filtrato per veicolo.

    Se passiamo un tipo di veicolo, mostriamo solo i corrieri che usano quel
    mezzo; il confronto e' "case-insensitive", cioe' "Auto" e "auto" sono
    trattati allo stesso modo. Se non passiamo nulla, tornano tutti.
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()
        if veicolo:
            # LOWER(...) mette tutto in minuscolo da entrambi i lati del
            # confronto, cosi' la maiuscola/minuscola non conta.
            # Il valore viaggia come parametro (%s), mai incollato nel testo.
            cursore.execute(
                "SELECT * FROM corrieri WHERE LOWER(veicolo) = LOWER(%s);",
                (veicolo,),
            )
        else:
            # Nessun filtro: prendiamo tutti i corrieri.
            cursore.execute("SELECT * FROM corrieri;")
        # fetchall() = "dammi tutte le righe trovate".
        return cursore.fetchall()
    finally:
        # Chiudiamo sempre la connessione, anche se qualcosa va storto.
        connessione.close()


def elimina_corriere(id_corriere: int) -> str:
    """Cancella un corriere (e, a cascata, tutte le sue recensioni).

    Prima di cancellare, controlliamo che il corriere esista davvero: se non
    c'e', solleviamo un errore "LookupError" che la route trasformera' in un
    bel 404 (non trovato), invece di far finta di aver cancellato qualcosa.
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()

        # Passo 1: esiste questo corriere? Lo cerchiamo per id.
        cursore.execute("SELECT id FROM corrieri WHERE id = %s;", (id_corriere,))
        if cursore.fetchone() is None:
            # Non esiste: avvisiamo con un errore chiaro.
            raise LookupError(f"Corriere con id={id_corriere} non trovato.")

        # Passo 2: esiste -> lo cancelliamo. Le recensioni collegate spariscono
        # da sole grazie al "ON DELETE CASCADE" definito nello schema del database.
        cursore.execute("DELETE FROM corrieri WHERE id = %s;", (id_corriere,))
        connessione.commit()  # confermiamo la cancellazione
        return f"Corriere {id_corriere} eliminato, incluse le recensioni collegate."
    finally:
        connessione.close()


def media_voti(id_corriere: int) -> Dict[str, Any]:
    """Calcola la media dei voti ricevuti da un singolo corriere.

    Restituisce un riepilogo: id e nome del corriere, la media dei voti e
    quante recensioni ha in totale. Se il corriere non ha ancora ricevuto
    recensioni, la media sara' "None" (cioe' "nessun dato"), non zero:
    e' piu' onesto dire "non ci sono voti" che dire "ha media 0".
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()

        # Prima controlliamo che il corriere esista (e ci prendiamo il suo nome).
        cursore.execute("SELECT id, nome FROM corrieri WHERE id = %s;", (id_corriere,))
        corriere = cursore.fetchone()
        if corriere is None:
            raise LookupError(f"Corriere con id={id_corriere} non trovato.")

        # Poi chiediamo al database di fare i conti per noi:
        #   AVG(voto)  = la media dei voti
        #   COUNT(*)   = quante recensioni ci sono
        # Far calcolare la media direttamente al database e' piu' efficiente
        # che scaricare tutte le righe e sommarle in Python.
        cursore.execute(
            "SELECT AVG(voto) AS media, COUNT(*) AS totale "
            "FROM recensioni WHERE id_corriere = %s;",
            (id_corriere,),
        )
        riga = cursore.fetchone()

        # Se c'e' una media, la arrotondiamo a 2 decimali (es. 4.33).
        # Se invece e' None (nessuna recensione), la lasciamo None.
        media = round(float(riga["media"]), 2) if riga["media"] is not None else None

        # Impacchettiamo il risultato in un dizionario chiaro e leggibile.
        return {
            "id_corriere": id_corriere,
            "nome_corriere": corriere["nome"],
            "media_voti": media,
            "totale_recensioni": riga["totale"],
        }
    finally:
        connessione.close()
