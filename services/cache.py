import hashlib
import json
from typing import List
from services.music_engine import MusicEngine, TrackResult


def make_query_hash(query: str, source: str) -> str:
    normalized = f"{query.lower().strip()}:{source}"
    return hashlib.sha256(normalized.encode()).hexdigest()


async def get_or_search(
    engine: MusicEngine, db, query: str, source: str, ttl: int = 3600, limit: int = 5
) -> List[TrackResult]:
    query_hash = make_query_hash(query, source)

    cached = await db.get_cached(query_hash, source)
    if cached:
        return [TrackResult(**item) for item in cached]

    results = await engine.search(query, source, limit)

    if results:
        cache_data = [
            {
                "title": r.title,
                "artist": r.artist,
                "duration": r.duration,
                "source": r.source,
                "source_url": r.source_url,
                "thumbnail": r.thumbnail,
                "track_id": r.track_id,
            }
            for r in results
        ]
        await db.cache_results(query_hash, source, json.dumps(cache_data), ttl)

    return results
