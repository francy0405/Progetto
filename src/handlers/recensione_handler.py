"""Logica di business e query SQL per la risorsa recensioni."""

from typing import Any, Dict, Optional

from src.app import ottieni_connessione_db

_MAX_NOME = 120
_MAX_COMMENTO = 500


def _normalizza_commento(dati: Dict[str, Any]) -> Optional[str]:
    """Normalizza il campo facoltativo `commento`.

    Un commento assente, `null` o composto di soli spazi diventa None (SQL NULL),
    evitando di salvare la stringa letterale "None"; ogni altro valore viene
    convertito in stringa e ripulito degli spazi ai bordi.

    Args:
        dati: corpo JSON decodificato della richiesta.

    Returns:
        Optional[str]: il commento ripulito, oppure None se vuoto/assente.
    """
    return str(dati.get("commento", "") or "").strip() or None


def aggiungi_recensione(dati: Dict[str, Any]) -> Dict[str, Any]:
    """Inserisce una nuova recensione dopo aver validato i dati e l'esistenza del corriere.

    Args:
        dati: corpo JSON con le chiavi `id_corriere`, `nome_cliente`, `voto` e il
            facoltativo `commento`.

    Returns:
        Dict[str, Any]: la recensione appena creata.

    Raises:
        ValueError: se un campo non e' valido (voto fuori 1-5, tipi errati...).
        LookupError: se il corriere indicato non esiste.
        psycopg2.Error: in caso di errore del database.
    """
    id_corriere = dati["id_corriere"]
    if isinstance(id_corriere, bool) or not isinstance(id_corriere, int):
        raise ValueError("'id_corriere' deve essere un numero intero.")

    voto = dati["voto"]
    if isinstance(voto, bool) or not isinstance(voto, int):
        raise ValueError("'voto' deve essere un numero intero da 1 a 5.")
    if not 1 <= voto <= 5:
        raise ValueError("'voto' deve essere compreso tra 1 e 5.")

    nome_cliente = str(dati["nome_cliente"]).strip()
    if not nome_cliente:
        raise ValueError("'nome_cliente' non puo' essere vuoto.")
    if len(nome_cliente) > _MAX_NOME:
        raise ValueError(f"'nome_cliente' puo' avere al massimo {_MAX_NOME} caratteri.")

    commento = _normalizza_commento(dati)
    if commento is not None and len(commento) > _MAX_COMMENTO:
        raise ValueError(f"'commento' puo' avere al massimo {_MAX_COMMENTO} caratteri.")

    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()
        cursore.execute("SELECT id FROM corrieri WHERE id = %s;", (id_corriere,))
        if cursore.fetchone() is None:
            raise LookupError(f"Corriere con id={id_corriere} non trovato.")
        cursore.execute(
            "INSERT INTO recensioni (id_corriere, nome_cliente, voto, commento) "
            "VALUES (%s, %s, %s, %s) RETURNING *;",
            (id_corriere, nome_cliente, voto, commento),
        )
        recensione = cursore.fetchone()
        connessione.commit()
        return recensione
    finally:
        connessione.close()


def aggiorna_commento(id_recensione: int, dati: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiorna soltanto il commento di una recensione esistente.

    Inviare `{"commento": null}` o una stringa vuota azzera il commento (salva
    SQL NULL) invece del testo letterale "None".

    Args:
        id_recensione: identificativo della recensione da aggiornare.
        dati: corpo JSON che deve contenere la chiave `commento`.

    Returns:
        Dict[str, Any]: la recensione aggiornata.

    Raises:
        ValueError: se il commento supera la lunghezza massima.
        LookupError: se la recensione non esiste.
        psycopg2.Error: in caso di errore del database.
    """
    commento = _normalizza_commento(dati)
    if commento is not None and len(commento) > _MAX_COMMENTO:
        raise ValueError(f"'commento' puo' avere al massimo {_MAX_COMMENTO} caratteri.")

    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()
        cursore.execute("SELECT id FROM recensioni WHERE id = %s;", (id_recensione,))
        if cursore.fetchone() is None:
            raise LookupError(f"Recensione con id={id_recensione} non trovata.")
        cursore.execute(
            "UPDATE recensioni SET commento = %s WHERE id = %s RETURNING *;",
            (commento, id_recensione),
        )
        recensione = cursore.fetchone()
        connessione.commit()
        return recensione
    finally:
        connessione.close()
