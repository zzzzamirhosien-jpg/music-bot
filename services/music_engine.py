import asyncio
import os
import hashlib
from dataclasses import dataclass
from typing import List, Optional
from yt_dlp import YoutubeDL


@dataclass
class TrackResult:
    title: str
    artist: str
    duration: int
    source: str
    source_url: str
    thumbnail: str = ""
    track_id: str = ""

    def __post_init__(self):
        if not self.track_id:
            self.track_id = hashlib.md5(self.source_url.encode()).hexdigest()[:12]


class MusicEngine:
    def __init__(self, spotify_service=None):
        self.spotify = spotify_service

    async def search(self, query: str, source: str = "youtube", limit: int = 5) -> List[TrackResult]:
        if source == "spotify" and self.spotify:
            return await self._search_spotify(query, limit)
        elif source == "soundcloud":
            return await self._search_youtube(f"{query} site:soundcloud.com", limit)
        else:
            return await self._search_youtube(query, limit)

    async def _search_youtube(self, query: str, limit: int = 5) -> List[TrackResult]:
        def _do_search():
            ydl_opts = {
                "default_search": f"ytsearch{limit}",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "socket_timeout": 15,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if not info or "entries" not in info:
                    return []
                results = []
                for entry in info["entries"]:
                    if not entry:
                        continue
                    results.append(TrackResult(
                        title=entry.get("title", "Unknown"),
                        artist=entry.get("channel", entry.get("uploader", "Unknown")),
                        duration=entry.get("duration") or 0,
                        source="youtube",
                        source_url=entry.get("url", entry.get("webpage_url", "")),
                        thumbnail=entry.get("thumbnails", [{}])[-1].get("url", "") if entry.get("thumbnails") else "",
                        track_id=entry.get("id", ""),
                    ))
                return results

        return await asyncio.to_thread(_do_search)

    async def _search_spotify(self, query: str, limit: int = 5) -> List[TrackResult]:
        if not self.spotify:
            return await self._search_youtube(query, limit)

        try:
            spotify_results = await self.spotify.search(query, limit)
            results = []
            for track in spotify_results:
                yt_query = f"{track['title']} {track['artist']} official"
                yt_results = await self._search_youtube(yt_query, limit=1)
                if yt_results:
                    r = yt_results[0]
                    r.artist = track["artist"]
                    r.title = track["title"]
                    r.source = "spotify"
                    results.append(r)
            return results
        except Exception:
            return await self._search_youtube(query, limit)

    async def download_track(self, track: TrackResult, output_dir: str) -> Optional[str]:
        def _do_download():
            outtmpl = os.path.join(output_dir, f"{track.track_id}.%(ext)s")
            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }],
                "outtmpl": outtmpl,
                "quiet": True,
                "no_warnings": True,
                "max_filesize": 50 * 1024 * 1024,
                "socket_timeout": 30,
                "noplaylist": True,
                "extract_flat": False,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([track.source_url])

            mp3_path = os.path.join(output_dir, f"{track.track_id}.mp3")
            if os.path.exists(mp3_path):
                return mp3_path
            for f in os.listdir(output_dir):
                if f.startswith(track.track_id) and f.endswith((".mp3", ".m4a", ".webm")):
                    return os.path.join(output_dir, f)
            return None

        return await asyncio.to_thread(_do_download)
