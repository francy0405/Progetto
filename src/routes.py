"""
=====================================================================
 src/routes.py  —  GLI INDIRIZZI WEB (LE "ROUTE") DELL'API
=====================================================================

Questo file e' un po' il centralino dell'applicazione: il suo compito e'
decidere cosa deve succedere quando qualcuno bussa a un certo indirizzo.
Per fare qualche esempio, a "GET /corrieri" rispondiamo con la lista dei
corrieri, a "POST /recensioni" aggiungiamo una recensione e a
"DELETE /corrieri/5" cancelliamo il corriere numero 5.

C'e' una scelta di organizzazione che vale la pena spiegare: qui dentro
NON mettiamo la logica vera e propria, ne' le query al database. Ogni route
si limita a tre gesti - riceve la richiesta e controlla i dati di base,
chiama la funzione giusta (l'"handler") che fa il lavoro sporco, e infine
impacchetta la risposta in un formato sempre uguale. Tenere le route da una
parte e la logica dall'altra rende il codice piu' ordinato e piu' facile da
modificare.

Anche il formato delle risposte e' sempre lo stesso, cosi' il client sa
sempre cosa aspettarsi: quando va tutto bene rispondiamo con
{"Message": "Success", "Data": ...}, mentre quando c'e' un problema
rispondiamo con {"Error": "spiegazione"}. Ogni risposta porta poi con se' il
suo "status code" HTTP: 200 vuol dire ok, 201 creato, 400 richiesta
sbagliata, 404 non trovato e 500 errore del server o del database.
"""

from typing import Tuple

from flask import Blueprint, request, jsonify, Response
from psycopg2 import Error

# Importiamo le funzioni che fanno il lavoro vero (gli "handler").
from src.handlers.corriere_handler import leggi_corrieri, elimina_corriere, media_voti
from src.handlers.recensione_handler import aggiungi_recensione, aggiorna_commento

# Un "Blueprint" e' un gruppo di route che poi colleghiamo all'app in app.py:
# e' il modo con cui teniamo le route in un file separato e ordinato.
bp_api = Blueprint("api", __name__)


@bp_api.route("/corrieri", methods=["GET"])
def elenco_corrieri() -> Tuple[Response, int]:
    """GET /corrieri — Restituisce la lista dei corrieri.

    Volendo si puo' anche filtrare per tipo di veicolo, aggiungendo
    "?veicolo=auto" all'indirizzo; se non mettiamo nessun filtro, invece,
    tornano tutti.
    """
    try:
        # Leggiamo l'eventuale filtro "veicolo" dall'indirizzo (la query string).
        veicolo = request.args.get("veicolo", default=None, type=str)
        dati = leggi_corrieri(veicolo)
        return jsonify({"Message": "Success", "Data": dati}), 200
    # Se il database da' problemi rispondiamo con un 500 (errore del server)...
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    # ...e teniamo comunque una rete di sicurezza per qualsiasi altro imprevisto.
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


@bp_api.route("/recensioni", methods=["POST"])
def crea_recensione() -> Tuple[Response, int]:
    """POST /recensioni — Aggiunge una nuova recensione a un corriere.

    Nel corpo della richiesta il client deve mandarci un JSON con almeno tre
    campi - id_corriere, nome_cliente e voto - mentre il commento e'
    facoltativo.
    """
    try:
        # Leggiamo il corpo JSON della richiesta. Usiamo "silent=True" per
        # evitare che Flask vada in crash se il JSON e' malformato: in quel
        # caso ci restituisce semplicemente None, e a gestirlo ci pensiamo noi.
        dati = request.get_json(silent=True)
        if not isinstance(dati, dict):
            return jsonify({"Error": "Il corpo della richiesta deve essere un oggetto JSON."}), 400

        # Prima di andare avanti controlliamo che ci siano tutti i campi
        # obbligatori, cosi' da dare subito un messaggio chiaro se ne manca uno.
        for campo in ("id_corriere", "nome_cliente", "voto"):
            if campo not in dati:
                return jsonify({"Error": f"Parametro '{campo}' mancante."}), 400

        # A questo punto passiamo la palla all'handler, che validera' i valori
        # e fara' l'INSERT vero e proprio.
        recensione = aggiungi_recensione(dati)
        # Rispondiamo con 201, lo status giusto quando si crea una nuova risorsa.
        return jsonify({"Message": "Success", "Data": recensione}), 201

    # Da qui in poi "traduciamo" i vari tipi di errore in risposte HTTP: un
    # dato non valido diventa un 400...
    except ValueError as e:
        return jsonify({"Error": str(e)}), 400
    # ...un corriere inesistente diventa un 404...
    except LookupError as e:
        return jsonify({"Error": str(e)}), 404
    # ...un problema col database un 500...
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    # ...e qualsiasi altro imprevisto, di nuovo, un 500.
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


@bp_api.route("/recensioni/<int:id_recensione>", methods=["PUT"])
def modifica_recensione(id_recensione: int) -> Tuple[Response, int]:
    """PUT /recensioni/<id> — Modifica il commento di una recensione esistente.

    L'id della recensione va messo direttamente nell'indirizzo (per esempio
    /recensioni/7) e Flask ce lo consegna gia' pronto come numero intero.
    """
    try:
        dati = request.get_json(silent=True)
        if not isinstance(dati, dict):
            return jsonify({"Error": "Il corpo della richiesta deve essere un oggetto JSON."}), 400
        # Qui l'unica cosa che possiamo cambiare e' il commento.
        if "commento" not in dati:
            return jsonify({"Error": "Parametro 'commento' mancante."}), 400
        recensione = aggiorna_commento(id_recensione, dati)
        return jsonify({"Message": "Success", "Data": recensione}), 200
    except ValueError as e:
        return jsonify({"Error": str(e)}), 400
    except LookupError as e:
        return jsonify({"Error": str(e)}), 404
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


@bp_api.route("/corrieri/<int:id_corriere>", methods=["DELETE"])
def rimuovi_corriere(id_corriere: int) -> Tuple[Response, int]:
    """DELETE /corrieri/<id> — Cancella un corriere e, a cascata, le sue recensioni.

    Vale la pena ricordarlo: grazie al "ON DELETE CASCADE" definito nel
    database, cancellando il corriere spariscono in automatico anche tutte le
    recensioni collegate a lui.
    """
    try:
        messaggio = elimina_corriere(id_corriere)
        return jsonify({"Message": messaggio}), 200
    except LookupError as e:
        return jsonify({"Error": str(e)}), 404
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


@bp_api.route("/corrieri/<int:id_corriere>/media", methods=["GET"])
def media_corriere(id_corriere: int) -> Tuple[Response, int]:
    """GET /corrieri/<id>/media — Calcola la media dei voti di un singolo corriere."""
    try:
        dati = media_voti(id_corriere)
        return jsonify({"Message": "Success", "Data": dati}), 200
    except LookupError as e:
        return jsonify({"Error": str(e)}), 404
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
