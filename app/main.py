from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.models import AnalyzeResponse, PostMetadata
from app.services.apify_client import ApifyClient
from app.services.media_analysis import analyze_video
from app.services.sentiment import analyze_comments
from app.utils.files import ensure_dir, sanitize_handle

app = FastAPI(title="Instagram Latest Video Analyzer", default_response_class=ORJSONResponse)
apify_client = ApifyClient()


@app.get('/health')
async def health() -> dict:
    return {'status': 'ok'}


@app.get('/analyze', response_model=AnalyzeResponse)
async def analyze(handle: str = Query(..., description='Instagram handle pubblico')) -> AnalyzeResponse:
    try:
        clean_handle = sanitize_handle(handle)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workdir = ensure_dir(Path(settings.temp_dir) / clean_handle)

    try:
        reel = await apify_client.get_latest_reel(clean_handle)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Errore nel recupero reel da Apify: {exc}') from exc

    video_url = reel.get('downloadedVideo') or reel.get('videoUrl')
    post_url = reel.get('url')
    if not video_url:
        raise HTTPException(status_code=422, detail='Il reel trovato non espone un URL video scaricabile')
    if not post_url:
        raise HTTPException(status_code=422, detail='Il reel trovato non espone un URL del post')

    shortcode = reel.get('shortCode') or 'latest'
    video_path = workdir / f'{shortcode}.mp4'

    try:
        await apify_client.download_file(video_url, video_path)
        raw_comments = await apify_client.get_comments(post_url)
        comments, sentiment_summary = analyze_comments(raw_comments)
        video_analysis = analyze_video(video_path, workdir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Errore durante l'analisi del contenuto: {exc}") from exc

    post = PostMetadata(
        post_url=post_url,
        shortcode=reel.get('shortCode'),
        caption=reel.get('caption'),
        owner_username=reel.get('ownerUsername') or clean_handle,
        timestamp=reel.get('timestamp'),
        comments_count=reel.get('commentsCount'),
        likes_count=reel.get('likesCount'),
        video_url=reel.get('videoUrl'),
        downloaded_video_url=reel.get('downloadedVideo'),
    )

    return AnalyzeResponse(
        handle=clean_handle,
        post=post,
        comments=comments,
        sentiment_summary=sentiment_summary,
        video_analysis=video_analysis,
    )
