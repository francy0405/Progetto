"""Punto di avvio: carica l'ambiente e avvia il server di sviluppo Flask."""

from dotenv import load_dotenv
load_dotenv()

import os

from src.app import crea_app

PORTA = os.getenv("PORT", "5000")
app = crea_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=PORTA,
        debug=os.getenv("DEBUG", "True") == "True",
    )
