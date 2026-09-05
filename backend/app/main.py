import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from foldingos_api_core import OIDCSettings, OIDCVerifier, RPSettings, build_rp_auth, create_app

from app.api import chat, news
from app.core.config import settings
from app.services.feed_refresh import run_refresh_loop
from app.services.news_source import register
from app.services.rss_source import create_rss_source


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Block startup on the first feed fetch (fast) so no request ever sees
    # an empty feed; images warm in the background afterward (see
    # RssSource.refresh()) and app/services/feed_refresh.py takes over the
    # periodic re-fetch from here.
    await app.state.rss_source.refresh()
    worker = asyncio.create_task(run_refresh_loop(app.state.rss_source))
    try:
        yield
    finally:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass


def build_app():
    app = create_app(title="news.folding-os.com", allowed_origins=[])
    app.router.lifespan_context = _lifespan

    verifier = OIDCVerifier(
        OIDCSettings(
            issuer=settings.identity_issuer,
            client_id=settings.identity_client_id,
            client_secret=settings.identity_client_secret,
            audience=settings.identity_client_id,
        )
    )
    auth_router, require_user = build_rp_auth(
        RPSettings(
            issuer=settings.identity_issuer,
            client_id=settings.identity_client_id,
            client_secret=settings.identity_client_secret,
        ),
        verifier,
    )
    app.include_router(auth_router)
    app.include_router(news.router, dependencies=[Depends(require_user)])
    app.include_router(chat.router, dependencies=[Depends(require_user)])

    rss_source = create_rss_source()
    app.state.rss_source = rss_source
    register(rss_source)

    return app


app = build_app()
