"""
=====================================================================
 src/handlers/corriere_handler.py  —  LA LOGICA DEI CORRIERI
=====================================================================

Qui sta il "lavoro vero" sui corrieri: leggere la lista, cancellarne uno e
calcolare la media dei voti. Sono queste le funzioni che parlano davvero col
database, scrivendo le query SQL; le route, in routes.py, si limitano a
chiamarle, in quella divisione dei compiti che tiene il codice ordinato.

C'e' poi un dettaglio di sicurezza importante da sottolineare in
presentazione: in nessuna query incolliamo mai i valori dentro la stringa
SQL "a mano". Usiamo invece i segnaposto "%s" e passiamo i valori a parte,
lasciando che sia psycopg2 a inserirli in modo sicuro. E' proprio questo che
ci protegge dalla "SQL injection", cioe' da chi prova a infilare comandi
malevoli al posto dei dati.
"""

from typing import Any, Dict, List, Optional

# Chiediamo al cuore dell'app (app.py) di aprirci la connessione al database.
from src.app import ottieni_connessione_db


def leggi_corrieri(veicolo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Restituisce l'elenco dei corrieri, eventualmente filtrato per veicolo.

    Se passiamo un tipo di veicolo mostriamo solo i corrieri che usano quel
    mezzo, e il confronto e' "case-insensitive", cioe' "Auto" e "auto"
    vengono trattati allo stesso modo; se invece non passiamo nulla, tornano
    tutti.
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()
        if veicolo:
            # Con LOWER(...) mettiamo tutto in minuscolo da entrambi i lati del
            # confronto, cosi' la differenza tra maiuscole e minuscole non
            # conta. Il valore, come sempre, viaggia come parametro (%s) e non
            # viene mai incollato nel testo della query.
            cursore.execute(
                "SELECT * FROM corrieri WHERE LOWER(veicolo) = LOWER(%s);",
                (veicolo,),
            )
        else:
            # Nessun filtro: ci facciamo dare tutti i corrieri.
            cursore.execute("SELECT * FROM corrieri;")
        # fetchall() vuol dire "dammi tutte le righe trovate".
        return cursore.fetchall()
    finally:
        # Chiudiamo sempre la connessione, anche se qualcosa va storto.
        connessione.close()


def elimina_corriere(id_corriere: int) -> str:
    """Cancella un corriere (e, a cascata, tutte le sue recensioni).

    Prima di cancellare controlliamo che il corriere esista davvero: se non
    c'e', invece di far finta di aver cancellato qualcosa solleviamo un
    "LookupError" che la route trasformera' in un bel 404 (non trovato).
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()

        # Primo passo: questo corriere esiste? Lo cerchiamo per id.
        cursore.execute("SELECT id FROM corrieri WHERE id = %s;", (id_corriere,))
        if cursore.fetchone() is None:
            # Non esiste: lo segnaliamo con un errore chiaro.
            raise LookupError(f"Corriere con id={id_corriere} non trovato.")

        # Secondo passo: esiste, quindi lo cancelliamo. Le recensioni collegate
        # spariscono da sole grazie al "ON DELETE CASCADE" definito nello schema.
        cursore.execute("DELETE FROM corrieri WHERE id = %s;", (id_corriere,))
        connessione.commit()  # confermiamo la cancellazione
        return f"Corriere {id_corriere} eliminato, incluse le recensioni collegate."
    finally:
        connessione.close()


def media_voti(id_corriere: int) -> Dict[str, Any]:
    """Calcola la media dei voti ricevuti da un singolo corriere.

    Restituisce un piccolo riepilogo - id e nome del corriere, media dei voti
    e numero totale di recensioni. Se il corriere non ha ancora ricevuto
    recensioni la media sara' "None", cioe' "nessun dato", e non zero: e' piu'
    onesto dire "non ci sono voti" che far credere che abbia una media di 0.
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()

        # Prima di tutto controlliamo che il corriere esista, e gia' che ci
        # siamo ci prendiamo anche il suo nome.
        cursore.execute("SELECT id, nome FROM corrieri WHERE id = %s;", (id_corriere,))
        corriere = cursore.fetchone()
        if corriere is None:
            raise LookupError(f"Corriere con id={id_corriere} non trovato.")

        # Poi lasciamo che sia il database a fare i conti per noi: AVG(voto) ci
        # da' la media dei voti e COUNT(*) quante recensioni ci sono. Far
        # calcolare la media direttamente al database e' piu' efficiente che
        # scaricarsi tutte le righe e sommarle a mano in Python.
        cursore.execute(
            "SELECT AVG(voto) AS media, COUNT(*) AS totale "
            "FROM recensioni WHERE id_corriere = %s;",
            (id_corriere,),
        )
        riga = cursore.fetchone()

        # Se una media c'e', la arrotondiamo a due decimali (per esempio 4.33);
        # se invece e' None - nessuna recensione - la lasciamo None.
        media = round(float(riga["media"]), 2) if riga["media"] is not None else None

        # Infine impacchettiamo il risultato in un dizionario chiaro e leggibile.
        return {
            "id_corriere": id_corriere,
            "nome_corriere": corriere["nome"],
            "media_voti": media,
            "totale_recensioni": riga["totale"],
        }
    finally:
        connessione.close()
