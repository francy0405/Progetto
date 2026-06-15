"""
=====================================================================
 main.py  —  IL PUNTO DI PARTENZA DEL PROGRAMMA
=====================================================================

Questo e' il file che si lancia per far partire tutto.
Quando scriviamo "python main.py" nel terminale, e' da qui che parte
l'applicazione. Il suo compito e' molto semplice: prima prepara
l'ambiente (legge le impostazioni segrete), poi accende il server web.

Pensa a questo file come all'interruttore generale della casa: non
contiene la logica vera e propria, serve solo ad accendere tutto.
"""

# "load_dotenv" legge il file ".env" e mette al suo interno tutte le
# nostre impostazioni segrete (password del database, porta, ecc.).
# Lo facciamo PER PRIMA COSA, prima ancora di importare il resto del
# programma, perche' gli altri pezzi di codice hanno gia' bisogno di
# quelle impostazioni nel momento in cui vengono caricati.
from dotenv import load_dotenv
load_dotenv()

import os

# Importiamo la "fabbrica" che costruisce l'applicazione Flask.
# La logica di costruzione sta in un altro file (src/app.py): qui ci
# limitiamo a usarla.
from src.app import crea_app

# Su quale porta deve rispondere il server.
# Proviamo a leggerla dalle impostazioni; se non c'e', usiamo la 5000.
PORTA = os.getenv("PORT", "5000")

# Costruiamo concretamente l'applicazione: e' la nostra app Flask pronta.
app = crea_app()


# Questa riga significa: "esegui il codice qui sotto SOLO se ho lanciato
# direttamente questo file". Se invece il file venisse importato da un
# altro (ad esempio in un server di produzione), questa parte resta spenta.
if __name__ == "__main__":
    app.run(
        # "0.0.0.0" vuol dire "accetta richieste da qualsiasi indirizzo":
        # serve soprattutto dentro Docker, per essere raggiungibili da fuori.
        host=os.getenv("HOST", "0.0.0.0"),
        port=PORTA,
        # "debug" attivo = se sbaglio qualcosa nel codice il server me lo
        # mostra in chiaro e si riavvia da solo quando salvo. Comodo mentre
        # sviluppiamo; in un sito vero andrebbe spento.
        debug=os.getenv("DEBUG", "True") == "True",
    )
