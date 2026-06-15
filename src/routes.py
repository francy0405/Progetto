"""
=====================================================================
 src/routes.py  —  GLI INDIRIZZI WEB (LE "ROUTE") DELL'API
=====================================================================

Questo file e' come il centralino dell'applicazione: decide cosa
succede quando qualcuno bussa a un certo indirizzo.

Per esempio:
  - "GET /corrieri"            -> dammi la lista dei corrieri
  - "POST /recensioni"         -> aggiungi una recensione
  - "DELETE /corrieri/5"       -> cancella il corriere numero 5

COME E' ORGANIZZATO IL LAVORO (importante da spiegare):
qui dentro NON c'e' la logica vera e propria ne' le query al database.
Ogni route si limita a:
  1) ricevere la richiesta e controllare i dati di base;
  2) chiamare la funzione giusta (l'"handler") che fa il lavoro sporco;
  3) impacchettare la risposta in un formato sempre uguale.

Questa separazione (route da una parte, logica dall'altra) rende il
codice piu' ordinato e facile da modificare.

FORMATO DELLE RISPOSTE (sempre lo stesso, cosi' il client sa cosa aspettarsi):
  - se va tutto bene -> {"Message": "Success", "Data": ...}
  - se c'e' un errore -> {"Error": "spiegazione del problema"}

E poi ogni risposta porta con se' il suo "status code" HTTP:
  200 = ok | 201 = creato | 400 = richiesta sbagliata
  404 = non trovato       | 500 = errore del server/database
"""

from typing import Tuple

from flask import Blueprint, request, jsonify, Response
from psycopg2 import Error

# Importiamo le funzioni che fanno il lavoro vero (gli "handler").
from src.handlers.corriere_handler import leggi_corrieri, elimina_corriere, media_voti
from src.handlers.recensione_handler import aggiungi_recensione, aggiorna_commento

# Un "Blueprint" e' un gruppo di route che poi colleghiamo all'app in app.py.
# E' un modo per tenere le route in un file separato e ordinato.
bp_api = Blueprint("api", __name__)


@bp_api.route("/corrieri", methods=["GET"])
def elenco_corrieri() -> Tuple[Response, int]:
    """GET /corrieri — Restituisce la lista dei corrieri.

    Si puo' anche filtrare per tipo di veicolo aggiungendo "?veicolo=auto"
    all'indirizzo. Se non si mette nessun filtro, tornano tutti.
    """
    try:
        # Leggiamo l'eventuale filtro "veicolo" dall'indirizzo (la query string).
        veicolo = request.args.get("veicolo", default=None, type=str)
        dati = leggi_corrieri(veicolo)
        return jsonify({"Message": "Success", "Data": dati}), 200
    # Se il database da' problemi, rispondiamo con un 500 (errore del server).
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    # Rete di sicurezza per qualsiasi altro imprevisto.
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


@bp_api.route("/recensioni", methods=["POST"])
def crea_recensione() -> Tuple[Response, int]:
    """POST /recensioni — Aggiunge una nuova recensione a un corriere.

    Il client deve mandare nel corpo della richiesta un JSON con almeno:
    id_corriere, nome_cliente e voto (il commento e' facoltativo).
    """
    try:
        # Leggiamo il corpo JSON della richiesta.
        # "silent=True" evita che Flask vada in crash se il JSON e' malformato:
        # in quel caso ci ritorna semplicemente None e lo gestiamo noi.
        dati = request.get_json(silent=True)
        if not isinstance(dati, dict):
            return jsonify({"Error": "Il corpo della richiesta deve essere un oggetto JSON."}), 400

        # Controlliamo che ci siano tutti i campi obbligatori PRIMA di andare
        # avanti: cosi' diamo subito un messaggio chiaro se ne manca uno.
        for campo in ("id_corriere", "nome_cliente", "voto"):
            if campo not in dati:
                return jsonify({"Error": f"Parametro '{campo}' mancante."}), 400

        # Passiamo la palla all'handler, che validera' i valori e fara' l'INSERT.
        recensione = aggiungi_recensione(dati)
        # 201 = "creato con successo": e' lo status giusto quando si crea
        # una nuova risorsa.
        return jsonify({"Message": "Success", "Data": recensione}), 201

    # Da qui in poi "traduciamo" i vari tipi di errore in risposte HTTP:
    # dato non valido -> 400
    except ValueError as e:
        return jsonify({"Error": str(e)}), 400
    # corriere inesistente -> 404
    except LookupError as e:
        return jsonify({"Error": str(e)}), 404
    # problema col database -> 500
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    # qualsiasi altro imprevisto -> 500
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


@bp_api.route("/recensioni/<int:id_recensione>", methods=["PUT"])
def modifica_recensione(id_recensione: int) -> Tuple[Response, int]:
    """PUT /recensioni/<id> — Modifica il commento di una recensione gia' esistente.

    L'id della recensione si mette direttamente nell'indirizzo
    (es. /recensioni/7) e Flask ce lo passa gia' come numero intero.
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

    Ricorda: grazie al "ON DELETE CASCADE" definito nel database, cancellando
    il corriere spariscono in automatico anche tutte le recensioni collegate.
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
