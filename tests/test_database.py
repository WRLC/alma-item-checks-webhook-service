from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from alma_item_checks_webhook_service.database import DB_Engine, SessionMaker


def test_db_engine_is_engine():
    """Test that DB_Engine is a SQLAlchemy Engine instance."""
    assert isinstance(DB_Engine, Engine)


def test_session_maker_is_sessionmaker():
    """Test that SessionMaker is a sessionmaker instance."""
    assert isinstance(SessionMaker, sessionmaker)


def test_session_maker_creates_session():
    """Test that SessionMaker can create a session."""
    with SessionMaker() as session:
        assert isinstance(session, Session)
        assert session.bind == DB_Engine
