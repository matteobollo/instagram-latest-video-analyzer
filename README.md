# Instagram Latest Video Analyzer

Backend containerizzato che riceve un handle Instagram pubblico, recupera via Apify l'ultimo video pubblicato, scarica il file in locale, raccoglie i commenti, classifica il sentiment e restituisce una risposta JSON via API HTTP.

## Obiettivo coperto

La soluzione implementa tutti i requisiti minimi richiesti:

- endpoint HTTP `GET`
- input tramite handle Instagram
- recupero dell'ultimo video via Apify
- download locale del video
- recupero dei commenti del post
- classificazione dei commenti in positivi, negativi e neutri
- analisi media con durata, BPM e trascrizione solo se viene rilevata una voce
- esecuzione tramite Docker
- configurazione tramite `.env`

## Scelte tecniche

- **FastAPI** per API REST semplici, typed e veloci da avviare
- **Apify** come unico punto di accesso al contenuto Instagram
- **httpx** per chiamate HTTP asincrone
- **ffprobe / ffmpeg** per probing e conversione audio
- **librosa** per BPM estimation
- **Whisper locale** per trascrizione del parlato
- **pydantic-settings** per gestione configurazione

## Architettura

```text
GET /analyze?handle=<instagram_handle>
        |
        v
FastAPI
        |
        +--> Apify reel actor -> ultimo contenuto video
        |
        +--> download locale MP4
        |
        +--> Apify comments actor -> commenti del post
        |
        +--> sentiment service -> positive / negative / neutral
        |
        +--> ffprobe -> durata video
        |
        +--> ffmpeg -> estrazione WAV
        |
        +--> librosa -> BPM
        |
        +--> voice detection euristica
        |
        +--> Whisper -> trascrizione se voce rilevata
        |
        +--> JSON finale
```

## Struttura progetto

```text
.
├── app/
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── services/
│   │   ├── apify_client.py
│   │   ├── media_analysis.py
│   │   └── sentiment.py
│   └── utils/
│       └── files.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Variabili ambiente

```env
APIFY_TOKEN=your_apify_token
APIFY_REEL_ACTOR_ID=apify~instagram-reel-scraper
APIFY_COMMENTS_ACTOR_ID=apify~instagram-comment-scraper
WHISPER_MODEL=base
PORT=8000
LOG_LEVEL=INFO
TEMP_DIR=/tmp/ig-video-analyzer
APIFY_MAX_REELS=10
APIFY_MAX_COMMENTS=100
REQUEST_TIMEOUT_SECONDS=120
```

## Avvio in Docker

```bash
docker compose up --build
```

L'API sarà disponibile su:

```text
http://localhost:8000
```

## Endpoint disponibili

### Health

```bash
curl http://localhost:8000/health
```

### Analyze

```bash
curl "http://localhost:8000/analyze?handle=nasa"
```

## Esempio risposta

```json
{
  "handle": "nasa",
  "source": "instagram",
  "status": "ok",
  "post": {
    "post_url": "https://www.instagram.com/p/.../",
    "shortcode": "ABC123",
    "caption": "...",
    "owner_username": "nasa",
    "timestamp": "2026-04-13T08:00:00.000Z",
    "comments_count": 125,
    "likes_count": 54321,
    "video_url": "https://...",
    "downloaded_video_url": "https://..."
  },
  "comments": [
    {
      "text": "Amazing!",
      "username": "user1",
      "likes_count": 3,
      "sentiment": "positive",
      "confidence": 0.70
    }
  ],
  "sentiment_summary": {
    "positive": 50,
    "negative": 8,
    "neutral": 42,
    "total": 100
  },
  "video_analysis": {
    "duration_seconds": 17.08,
    "bpm": 121.4,
    "bpm_detected": true,
    "transcript": {
      "voice_detected": true,
      "transcript": "...",
      "language": "en"
    }
  }
}
```

## Trade-off dichiarati

### 1. Sentiment rule-based

Per questa versione il sentiment usa una classificazione semplice a dizionario. È leggera, veloce e facile da leggere, ma in produzione la sostituirei con un classificatore più robusto multilingua.

### 2. Voice detection euristica

La rilevazione della voce usa segnali audio semplici come RMS e zero-crossing rate. È una baseline pragmatica, non una soluzione VAD avanzata.

### 3. Analisi sincrona

L'intera pipeline gira inline nella request HTTP. Per il test è perfetta perché rende facile valutare il flusso end-to-end, ma in produzione valuterei una coda asincrona.

### 4. Whisper locale

Ottimo per autonomia tecnica, ma aumenta peso del container e tempi di warm-up.

## Limiti noti

- alcuni reel potrebbero non esporre un URL video scaricabile stabile
- il BPM può essere poco attendibile su audio rumoroso o parlato puro
- il sentiment rule-based non è semantico e può sbagliare ironia o slang
- la latenza può crescere su video lunghi

## Miglioramenti futuri

- coda asincrona con Celery o Dramatiq
- cache risultati per handle e shortcode
- storage persistente di video e analisi
- sentiment multilingua con modello dedicato
- voice activity detection più robusta
- test automatici e GitHub Actions
