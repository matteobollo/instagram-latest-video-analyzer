from pathlib import Path

import httpx

from app.config import settings


class ApifyClient:
    def __init__(self) -> None:
        """
        Initialize the Apify client.

        The client is initialized with the base URL of the Apify API
        and the timeout for requests.
        """
        self.base_url = 'https://api.apify.com/v2'
        """
        The timeout for requests in seconds.
        """
        self.timeout = settings.request_timeout_seconds

    async def _run_actor(self, actor_id: str, payload: dict) -> list[dict]:
        """
        Run an actor and return the result.

        The actor is run by making a POST request to the Apify API.
        The request is made with the given payload and the actor ID.
        The response is expected to be a JSON object.

        :param actor_id: The ID of the actor to run.
        :param payload: The payload to send to the actor.
        :return: The result of the actor run as a list of dictionaries.
        """
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
            # The response is expected to be a list of dictionaries.
            # If the response is not a list, wrap it in a list.
            return data if isinstance(data, list) else [data]

    async def get_latest_reel(self, handle: str) -> dict:
        """
        Get the latest reel of the given Instagram handle.

        The method runs the Apify reel actor and returns the latest reel found.
        If no reels are found, a RuntimeError is raised.

        :param handle: The Instagram handle to get the latest reel for.
        :return: The latest reel as a dictionary.
        :raises RuntimeError: If no reels are found.
        """
        payload = {
            'username': [handle],
            'resultsLimit': settings.apify_max_reels,
        }
        # Run the Apify reel actor and get the results.
        items = await self._run_actor(settings.apify_reel_actor_id, payload)
        # Filter the results to only include videos.
        videos = [item for item in items if str(item.get('type', '')).lower() == 'video']
        # If no videos are found, raise an error.
        if not videos:
            raise RuntimeError('Nessun video trovato per il profilo richiesto')
        # Sort the videos by timestamp in descending order.
        videos.sort(key=lambda item: item.get('timestamp') or '', reverse=True)
        # Return the latest video.
        return videos[0]

    async def get_comments(self, post_url: str) -> list[dict]:
        """
        Get the comments of the given Instagram post URL.

        The method runs the Apify comments actor and returns the comments found.
        The comments are expected to be a list of dictionaries.

        :param post_url: The Instagram post URL to get the comments for.
        :return: The comments found as a list of dictionaries.
        """
        payload = {
            # The direct URL of the post to get the comments for.
            'directUrls': [post_url],
            # The maximum number of comments to return.
            'resultsLimit': settings.apify_max_comments,
        }
        # Run the Apify comments actor and get the results.
        return await self._run_actor(settings.apify_comments_actor_id, payload)

    async def download_file(self, url: str, destination: Path) -> Path:
        """
        Download a file from a URL and save it to a destination.

        The method uses the `httpx` library to make a GET request to the URL
        and save the response to the destination.

        :param url: The URL of the file to download.
        :param destination: The path where the file should be saved.
        :return: The path where the file was saved.
        """
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            with destination.open('wb') as output_file:
                async with client.stream('GET', url) as response:
                    response.raise_for_status()
                    # Iterate over the response in chunks and write them to the output file.
                    async for chunk in response.aiter_bytes():
                        output_file.write(chunk)
        return destination
