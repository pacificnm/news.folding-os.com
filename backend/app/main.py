from fastapi import Depends
from foldingos_api_core import OIDCSettings, OIDCVerifier, RPSettings, build_rp_auth, create_app

from app.api import news
from app.core.config import settings
from app.services.news_source import register
from app.services.rss_source import create_rss_source


def build_app():
    app = create_app(title="news.folding-os.com", allowed_origins=[])

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

    register(create_rss_source())

    return app


app = build_app()
