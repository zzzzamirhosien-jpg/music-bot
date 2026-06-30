import asyncio
from typing import List, Dict, Optional

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    HAS_SPOTIPY = True
except ImportError:
    HAS_SPOTIPY = False


class SpotifyService:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._sp = None

    def _get_client(self):
        if self._sp is None and HAS_SPOTIPY and self.client_id and self.client_secret:
            auth_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            self._sp = spotipy.Spotify(auth_manager=auth_manager)
        return self._sp

    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        sp = self._get_client()
        if sp is None:
            return []

        def _do_search():
            results = sp.search(q=query, type="track", limit=limit)
            tracks = []
            for item in results.get("tracks", {}).get("items", []):
                artists = ", ".join(a["name"] for a in item.get("artists", []))
                duration_ms = item.get("duration_ms", 0)
                tracks.append({
                    "title": item.get("name", "Unknown"),
                    "artist": artists or "Unknown",
                    "album": item.get("album", {}).get("name", ""),
                    "duration": duration_ms // 1000,
                    "spotify_url": item.get("external_urls", {}).get("spotify", ""),
                    "isrc": item.get("external_ids", {}).get("isrc", ""),
                })
            return tracks

        return await asyncio.to_thread(_do_search)

    @property
    def available(self) -> bool:
        return HAS_SPOTIPY and bool(self.client_id) and bool(self.client_secret)
