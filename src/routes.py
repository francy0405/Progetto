"""Definizione delle route: mappa gli endpoint HTTP sulle funzioni handler.

Gli handler sollevano eccezioni; ogni route le intercetta con try/except e le
traduce nel formato di risposta uniforme `{"Message"/"Data"}` (successo) oppure
`{"Error"}` (errore), con lo status code appropriato.
"""

from typing import Tuple

from flask import Blueprint, request, jsonify, Response
from psycopg2 import Error

from src.handlers.corriere_handler import leggi_corrieri, elimina_corriere, media_voti
from src.handlers.recensione_handler import aggiungi_recensione, aggiorna_commento

bp_api = Blueprint("api", __name__)


@bp_api.route("/corrieri", methods=["GET"])
def elenco_corrieri() -> Tuple[Response, int]:
    """GET /corrieri — Elenco dei corrieri, filtrabile con `?veicolo=<tipo>`."""
    try:
        veicolo = request.args.get("veicolo", default=None, type=str)
        dati = leggi_corrieri(veicolo)
        return jsonify({"Message": "Success", "Data": dati}), 200
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


@bp_api.route("/recensioni", methods=["POST"])
def crea_recensione() -> Tuple[Response, int]:
    """POST /recensioni — Inserisce una nuova recensione per un corriere esistente."""
    try:
        dati = request.get_json(silent=True)
        if not isinstance(dati, dict):
            return jsonify({"Error": "Il corpo della richiesta deve essere un oggetto JSON."}), 400
        for campo in ("id_corriere", "nome_cliente", "voto"):
            if campo not in dati:
                return jsonify({"Error": f"Parametro '{campo}' mancante."}), 400
        recensione = aggiungi_recensione(dati)
        return jsonify({"Message": "Success", "Data": recensione}), 201
    except ValueError as e:
        return jsonify({"Error": str(e)}), 400
    except LookupError as e:
        return jsonify({"Error": str(e)}), 404
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    except Exception as e:
        return jsonify({"Error": str(e)}), 500


@bp_api.route("/recensioni/<int:id_recensione>", methods=["PUT"])
def modifica_recensione(id_recensione: int) -> Tuple[Response, int]:
    """PUT /recensioni/<id> — Aggiorna il commento di una recensione esistente."""
    try:
        dati = request.get_json(silent=True)
        if not isinstance(dati, dict):
            return jsonify({"Error": "Il corpo della richiesta deve essere un oggetto JSON."}), 400
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
    """DELETE /corrieri/<id> — Rimuove un corriere e tutte le sue recensioni."""
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
    """GET /corrieri/<id>/media — Media voti di un singolo corriere."""
    try:
        dati = media_voti(id_corriere)
        return jsonify({"Message": "Success", "Data": dati}), 200
    except LookupError as e:
        return jsonify({"Error": str(e)}), 404
    except Error as e:
        return jsonify({"Error": f"Errore database: {e}"}), 500
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
