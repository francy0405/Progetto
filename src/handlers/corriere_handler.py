"""Logica di business e query SQL per la risorsa corrieri."""

from typing import Any, Dict, List, Optional

from src.app import ottieni_connessione_db


def leggi_corrieri(veicolo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Restituisce l'elenco dei corrieri, opzionalmente filtrato per veicolo.

    Args:
        veicolo: tipo di veicolo su cui filtrare (case-insensitive); se None o
            stringa vuota vengono restituiti tutti i corrieri.

    Returns:
        List[Dict[str, Any]]: lista di corrieri rappresentati come dizionari.

    Raises:
        psycopg2.Error: in caso di errore del database.
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()
        if veicolo:
            cursore.execute(
                "SELECT * FROM corrieri WHERE LOWER(veicolo) = LOWER(%s);",
                (veicolo,),
            )
        else:
            cursore.execute("SELECT * FROM corrieri;")
        return cursore.fetchall()
    finally:
        connessione.close()


def elimina_corriere(id_corriere: int) -> str:
    """Elimina un corriere e, tramite ON DELETE CASCADE, tutte le sue recensioni.

    Args:
        id_corriere: identificativo del corriere da eliminare.

    Returns:
        str: messaggio di conferma dell'eliminazione.

    Raises:
        LookupError: se il corriere non esiste.
        psycopg2.Error: in caso di errore del database.
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()
        cursore.execute("SELECT id FROM corrieri WHERE id = %s;", (id_corriere,))
        if cursore.fetchone() is None:
            raise LookupError(f"Corriere con id={id_corriere} non trovato.")
        cursore.execute("DELETE FROM corrieri WHERE id = %s;", (id_corriere,))
        connessione.commit()
        return f"Corriere {id_corriere} eliminato, incluse le recensioni collegate."
    finally:
        connessione.close()


def media_voti(id_corriere: int) -> Dict[str, Any]:
    """Calcola la media dei voti delle recensioni di un singolo corriere.

    Args:
        id_corriere: identificativo del corriere.

    Returns:
        Dict[str, Any]: dizionario con id, nome, media voti (None se il corriere
        non ha recensioni) e numero totale di recensioni.

    Raises:
        LookupError: se il corriere non esiste.
        psycopg2.Error: in caso di errore del database.
    """
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()
        cursore.execute("SELECT id, nome FROM corrieri WHERE id = %s;", (id_corriere,))
        corriere = cursore.fetchone()
        if corriere is None:
            raise LookupError(f"Corriere con id={id_corriere} non trovato.")
        cursore.execute(
            "SELECT AVG(voto) AS media, COUNT(*) AS totale "
            "FROM recensioni WHERE id_corriere = %s;",
            (id_corriere,),
        )
        riga = cursore.fetchone()
        media = round(float(riga["media"]), 2) if riga["media"] is not None else None
        return {
            "id_corriere": id_corriere,
            "nome_corriere": corriere["nome"],
            "media_voti": media,
            "totale_recensioni": riga["totale"],
        }
    finally:
        connessione.close()
