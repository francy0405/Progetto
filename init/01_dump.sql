-- =====================================================================
--  01_dump.sql  —  LO "STAMPO" INIZIALE DEL DATABASE
-- =====================================================================
--
--  COS'E': questo file e' una "fotografia" del database, generata in
--  automatico dallo strumento pg_dump di PostgreSQL. Contiene i comandi
--  per ricostruire da zero la struttura (le tabelle) e per ricaricare i
--  dati di esempio (gli 8 corrieri).
--
--  QUANDO VIENE USATO: Docker lo esegue UNA SOLA VOLTA, alla primissima
--  creazione del database (e' nella cartella "init" collegata in
--  docker-compose). In questo modo, appena acceso, il database e' gia'
--  pronto con tabelle e dati, senza doverli inserire a mano.
--
--  COSA TROVIAMO DENTRO (le parti che contano per la presentazione):
--    - la tabella "corrieri"   (chi fa le consegne)
--    - la tabella "recensioni" (i voti dei clienti)
--    - le "sequence", cioe' i contatori che generano gli id automatici
--    - i vincoli: chiave primaria, controllo sul voto (1-5) e la chiave
--      esterna che collega le recensioni ai corrieri (con cancellazione
--      a cascata).
--
--  NOTA: e' un file generato dalla macchina, quindi i commenti tecnici
--  "-- Name: ...; Type: ..." li scrive pg_dump da solo. I commenti
--  discorsivi (come questo) li abbiamo aggiunti noi come appunti.
-- =====================================================================

--
-- PostgreSQL database dump
--

\restrict gq1GQIYkZWdvSDo5Kqi0OEuDXWeoxrKIcG1tEkAi0BPCA1C1xI64ZwbbJkZVtOi

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: corrieri; Type: TABLE; Schema: public; Owner: -
--

-- APPUNTO: la tabella dei corrieri. Ogni riga e' un fattorino, con nome,
-- tipo di veicolo e quante consegne ha fatto in totale (parte da 0).
CREATE TABLE public.corrieri (
    id integer NOT NULL,
    nome character varying(120) NOT NULL,
    veicolo character varying(60) NOT NULL,
    consegne_totali integer DEFAULT 0 NOT NULL
);


--
-- Name: corrieri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.corrieri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: corrieri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.corrieri_id_seq OWNED BY public.corrieri.id;


--
-- Name: recensioni; Type: TABLE; Schema: public; Owner: -
--

-- APPUNTO: la tabella delle recensioni. Ogni riga e' il voto di un cliente
-- a un corriere. "id_corriere" dice a quale corriere si riferisce.
-- Il CONSTRAINT "chk_voto" e' una regola che il database fa rispettare da
-- solo: rifiuta qualsiasi voto che non sia compreso tra 1 e 5.
CREATE TABLE public.recensioni (
    id integer NOT NULL,
    id_corriere integer NOT NULL,
    nome_cliente character varying(120) NOT NULL,
    voto integer NOT NULL,
    commento character varying(500),
    CONSTRAINT chk_voto CHECK (((voto >= 1) AND (voto <= 5)))
);


--
-- Name: recensioni_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.recensioni_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recensioni_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.recensioni_id_seq OWNED BY public.recensioni.id;


--
-- Name: corrieri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.corrieri ALTER COLUMN id SET DEFAULT nextval('public.corrieri_id_seq'::regclass);


--
-- Name: recensioni id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recensioni ALTER COLUMN id SET DEFAULT nextval('public.recensioni_id_seq'::regclass);


--
-- Data for Name: corrieri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.corrieri (id, nome, veicolo, consegne_totali) FROM stdin;
1	Mario Rossi	Scooter	120
2	Anna Verdi	Bicicletta	85
3	Luca Bianchi	Auto	210
4	Giulia Esposito	Moto	64
5	Marco Ferrari	Furgone	340
6	Sara Conti	Scooter	150
7	Davide Greco	Bicicletta	47
8	Elena Marino	Auto	198
\.


--
-- Data for Name: recensioni; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.recensioni (id, id_corriere, nome_cliente, voto, commento) FROM stdin;
\.


--
-- Name: corrieri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.corrieri_id_seq', 8, true);


--
-- Name: recensioni_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.recensioni_id_seq', 1, false);


--
-- Name: corrieri corrieri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.corrieri
    ADD CONSTRAINT corrieri_pkey PRIMARY KEY (id);


--
-- Name: recensioni recensioni_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recensioni
    ADD CONSTRAINT recensioni_pkey PRIMARY KEY (id);


--
-- Name: recensioni fk_recensioni_corriere; Type: FK CONSTRAINT; Schema: public; Owner: -
--

-- APPUNTO: questo e' il collegamento (la "chiave esterna") tra le due tabelle.
-- Dice: ogni recensione DEVE riferirsi a un corriere che esiste davvero.
-- "ON DELETE CASCADE" = se cancello un corriere, spariscono in automatico
-- anche tutte le sue recensioni (niente recensioni "orfane").
ALTER TABLE ONLY public.recensioni
    ADD CONSTRAINT fk_recensioni_corriere FOREIGN KEY (id_corriere) REFERENCES public.corrieri(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict gq1GQIYkZWdvSDo5Kqi0OEuDXWeoxrKIcG1tEkAi0BPCA1C1xI64ZwbbJkZVtOi

