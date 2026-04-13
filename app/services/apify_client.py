from pathlib import Path

import httpx

from app.config import settings


class ApifyClient:
    def __init__(self) -> None:
        self.base_url = 'https://api.apify.com/v2'
        self.timeout = settings.request_timeout_seconds

    async def _run_actor(self, actor_id: str, payload: dict) -> list[dict]:
        url = f'{self.base_url}/acts/{actor_id}/run-sync-get-dataset-items'
        params = {
            'token': settings.apify_token,
            'timeout': settings.request_timeout_seconds,
            'memory': 2048,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else [data]

    async def get_latest_reel(self, handle: str) -> dict:
        payload = {
            'username': [handle],
            'resultsLimit': settings.apify_max_reels,
        }
        items = await self._run_actor(settings.apify_reel_actor_id, payload)
        videos = [item for item in items if str(item.get('type', '')).lower() == 'video']
        if not videos:
            raise RuntimeError('Nessun video trovato per il profilo richiesto')
        videos.sort(key=lambda item: item.get('timestamp') or '', reverse=True)
        return videos[0]

    async def get_comments(self, post_url: str) -> list[dict]:
        payload = {
            'directUrls': [post_url],
            'resultsLimit': settings.apify_max_comments,
        }
        return await self._run_actor(settings.apify_comments_actor_id, payload)

    async def download_file(self, url: str, destination: Path) -> Path:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            with destination.open('wb') as output_file:
                async with client.stream('GET', url) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        output_file.write(chunk)
        return destination
