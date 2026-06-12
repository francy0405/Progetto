# Immagine dell'app Flask
FROM python:3.13-slim

# Output dei log non bufferizzato (utile per vedere subito i messaggi di Flask)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installo prima le dipendenze (sfrutta la cache di Docker se non cambiano)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copio il codice dell'applicazione
COPY main.py .
COPY src/ ./src/

EXPOSE 5000

CMD ["python", "main.py"]
