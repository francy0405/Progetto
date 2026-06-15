"""
=====================================================================
 main.py  —  IL PUNTO DI PARTENZA DEL PROGRAMMA
=====================================================================

Questo e' il file che si lancia per far partire tutto: quando scriviamo
"python main.py" nel terminale, l'applicazione nasce da qui. Il suo
compito, in fondo, e' molto semplice: prima prepara l'ambiente leggendo le
impostazioni segrete, e subito dopo accende il server web. Possiamo
immaginarlo come l'interruttore generale di casa, che non contiene nessun
elettrodomestico ma serve a dare corrente a tutto il resto.
"""

# La primissima cosa che facciamo, ancora prima di importare il resto del
# programma, e' leggere il file ".env" con load_dotenv. Cosi' tutte le nostre
# impostazioni segrete - la password del database, la porta, e cosi' via -
# finiscono nelle variabili d'ambiente. L'ordine non e' casuale: gli altri
# pezzi di codice hanno gia' bisogno di quei valori nel momento stesso in cui
# vengono caricati, quindi devono trovarli gia' pronti.
from dotenv import load_dotenv
load_dotenv()

import os

# Importiamo la "fabbrica" che costruisce l'applicazione Flask. La logica di
# costruzione vive in un altro file (src/app.py): qui ci limitiamo a usarla,
# tenendo questo file il piu' snello possibile.
from src.app import crea_app

# Su quale porta deve rispondere il server: proviamo a leggerla dalle
# impostazioni e, se non la troviamo, ripieghiamo sulla 5000.
PORTA = os.getenv("PORT", "5000")

# Costruiamo concretamente l'applicazione: da qui in poi "app" e' la nostra
# app Flask, pronta all'uso.
app = crea_app()


# Quest'ultima riga vuol dire "esegui il blocco qui sotto solo se ho lanciato
# direttamente questo file". Se invece main.py venisse importato da un altro
# file - come succede su un vero server di produzione - questa parte
# resterebbe spenta, lasciando l'avvio in mano al server.
if __name__ == "__main__":
    app.run(
        # "0.0.0.0" significa "accetta richieste da qualsiasi indirizzo": una
        # cosa indispensabile dentro Docker, altrimenti l'app non sarebbe
        # raggiungibile dall'esterno del contenitore.
        host=os.getenv("HOST", "0.0.0.0"),
        port=PORTA,
        # Con "debug" attivo, se sbagliamo qualcosa nel codice il server ce lo
        # mostra in chiaro e si riavvia da solo a ogni salvataggio: comodissimo
        # mentre sviluppiamo, ma in un sito vero andrebbe spento.
        debug=os.getenv("DEBUG", "True") == "True",
    )
