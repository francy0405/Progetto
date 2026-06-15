"""
=====================================================================
 src/handlers/recensione_handler.py  —  LA LOGICA DELLE RECENSIONI
=====================================================================

Qui gestiamo le recensioni, e in pratica facciamo due cose: aggiungerne una
nuova e modificare il commento di una gia' esistente.

La parte piu' interessante da raccontare in presentazione e' la
VALIDAZIONE. Prima di scrivere qualunque cosa nel database, controlliamo con
attenzione che i dati abbiano senso: il voto e' davvero un numero da 1 a 5?
il nome non e' vuoto? il commento non e' troppo lungo? Il principio e'
semplice: meglio bloccare subito un dato sbagliato con un messaggio chiaro,
piuttosto che lasciarlo entrare e ritrovarcelo nel database.
"""

from typing import Any, Dict, Optional

from src.app import ottieni_connessione_db

# Le lunghezze massime consentite. Le teniamo come "costanti" qui in alto
# cosi' che il numero compaia in un posto solo: se un domani volessimo
# cambiarlo, lo cambiamo qui e basta. Devono combaciare con i limiti VARCHAR
# definiti nel database.
_MAX_NOME = 120
_MAX_COMMENTO = 500


def _normalizza_commento(dati: Dict[str, Any]) -> Optional[str]:
    """Mette in ordine il campo "commento", che e' facoltativo.

    Il problema che risolve e' questo: il commento puo' mancare del tutto,
    arrivare come null, oppure essere fatto solo di spazi vuoti. In tutti
    questi casi vogliamo salvare un vero "niente" (NULL nel database) e non,
    per sbaglio, la parola "None" scritta come testo; se invece il commento
    c'e' davvero, ci limitiamo a togliere gli spazi inutili ai bordi. Il nome
    che inizia con "_" e' una convenzione: segnala che e' una funzione di
    aiuto interna, pensata per essere usata solo qui dentro.
    """
    # Letta da sinistra a destra: prendi il commento (se manca, stringa vuota),
    # se e' "falso"/vuoto usa "", togli gli spazi ai bordi e, se a quel punto
    # non resta niente, trasformalo in None.
    return str(dati.get("commento", "") or "").strip() or None


def aggiungi_recensione(dati: Dict[str, Any]) -> Dict[str, Any]:
    """Crea una nuova recensione, ma solo dopo aver controllato tutto.

    L'ordine che seguiamo e' sempre lo stesso: prima validiamo ogni singolo
    campo, e se qualcosa non va lo diciamo subito; poi verifichiamo che il
    corriere esista; e solo alla fine, quando siamo sicuri, scriviamo davvero
    nel database.
    """
    # --- Controllo dell'id del corriere ---
    id_corriere = dati["id_corriere"]
    # Qui c'e' un piccolo trucco a cui fare attenzione: in Python True e False
    # vengono considerati numeri (1 e 0), quindi escludiamo esplicitamente i
    # booleani, altrimenti un "True" passerebbe per un id valido.
    if isinstance(id_corriere, bool) or not isinstance(id_corriere, int):
        raise ValueError("'id_corriere' deve essere un numero intero.")

    # --- Controllo del voto ---
    voto = dati["voto"]
    if isinstance(voto, bool) or not isinstance(voto, int):
        raise ValueError("'voto' deve essere un numero intero da 1 a 5.")
    # Il voto deve stare nell'intervallo 1-5. Lo stesso limite e' anche nel
    # database, garantito dal CHECK; qui pero' lo controlliamo prima, cosi' da
    # poter dare all'utente un messaggio piu' gentile.
    if not 1 <= voto <= 5:
        raise ValueError("'voto' deve essere compreso tra 1 e 5.")

    # --- Controllo del nome del cliente ---
    nome_cliente = str(dati["nome_cliente"]).strip()  # togliamo spazi ai bordi
    if not nome_cliente:
        raise ValueError("'nome_cliente' non puo' essere vuoto.")
    if len(nome_cliente) > _MAX_NOME:
        raise ValueError(f"'nome_cliente' puo' avere al massimo {_MAX_NOME} caratteri.")

    # --- Commento (facoltativo) ---
    commento = _normalizza_commento(dati)
    if commento is not None and len(commento) > _MAX_COMMENTO:
        raise ValueError(f"'commento' puo' avere al massimo {_MAX_COMMENTO} caratteri.")

    # --- Tutto valido: ora possiamo parlare col database ---
    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()

        # Verifichiamo che il corriere a cui vogliamo legare la recensione
        # esista davvero: se non c'e', ha senso fermarci con un 404 invece di
        # salvare una recensione "appesa al nulla".
        cursore.execute("SELECT id FROM corrieri WHERE id = %s;", (id_corriere,))
        if cursore.fetchone() is None:
            raise LookupError(f"Corriere con id={id_corriere} non trovato.")

        # Inseriamo la recensione. Il "RETURNING *" e' molto comodo: chiede al
        # database di restituirci subito la riga appena creata, id compreso,
        # cosi' possiamo rimandarla al client senza dover fare una seconda query.
        cursore.execute(
            "INSERT INTO recensioni (id_corriere, nome_cliente, voto, commento) "
            "VALUES (%s, %s, %s, %s) RETURNING *;",
            (id_corriere, nome_cliente, voto, commento),
        )
        recensione = cursore.fetchone()
        connessione.commit()  # confermiamo il salvataggio
        return recensione
    finally:
        connessione.close()


def aggiorna_commento(id_recensione: int, dati: Dict[str, Any]) -> Dict[str, Any]:
    """Modifica SOLO il commento di una recensione gia' esistente.

    Qui non tocchiamo ne' il voto ne' il cliente: cambiamo unicamente il
    testo del commento. E se ci arriva un commento vuoto o null, il commento
    viene azzerato (torna a NULL) grazie alla funzione di normalizzazione che
    abbiamo visto sopra.
    """
    # Facciamo lo stesso controllo di lunghezza dell'inserimento.
    commento = _normalizza_commento(dati)
    if commento is not None and len(commento) > _MAX_COMMENTO:
        raise ValueError(f"'commento' puo' avere al massimo {_MAX_COMMENTO} caratteri.")

    connessione = ottieni_connessione_db()
    try:
        cursore = connessione.cursor()

        # Prima di tutto controlliamo che la recensione esista davvero.
        cursore.execute("SELECT id FROM recensioni WHERE id = %s;", (id_recensione,))
        if cursore.fetchone() is None:
            raise LookupError(f"Recensione con id={id_recensione} non trovata.")

        # Aggiorniamo il commento e ci facciamo restituire la riga aggiornata.
        cursore.execute(
            "UPDATE recensioni SET commento = %s WHERE id = %s RETURNING *;",
            (commento, id_recensione),
        )
        recensione = cursore.fetchone()
        connessione.commit()
        return recensione
    finally:
        connessione.close()
