from foldingos_api_core import get_db_dependency, make_session_factory

from app.core.config import settings

session_factory = make_session_factory(settings.database_url)
get_db = get_db_dependency(session_factory)
