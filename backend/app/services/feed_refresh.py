"""Background job: re-fetch the RSS feeds (and warm their images) every
FEED_REFRESH_INTERVAL_SECONDS, so a visitor's request never waits on an
external feed/image fetch — see app/main.py's lifespan, which runs one
refresh synchronously at startup before spawning this loop.
"""

import asyncio
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def run_refresh_loop(rss_source) -> None:
    while True:
        await asyncio.sleep(settings.feed_refresh_interval_seconds)
        try:
            await rss_source.refresh()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Feed refresh: unexpected error, will retry next cycle")
