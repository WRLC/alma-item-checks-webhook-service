"""Test suite for InstitutionRepository"""
from alma_item_checks_webhook_service.database import DB_Engine, SessionMaker
from alma_item_checks_webhook_service.models.base import Base
from alma_item_checks_webhook_service.models.institution import Institution
from alma_item_checks_webhook_service.repos.institution_repo import InstitutionRepository


# noinspection PyUnusedLocal
def setup_module(module):
    """Create the table in the database and add a test institution."""
    Base.metadata.create_all(DB_Engine)
    with SessionMaker() as session:
        institution = Institution(
            name="Test University", code="TU", api_key="test_api_key"
        )
        session.add(institution)
        session.commit()


# noinspection PyUnusedLocal
def teardown_module(module):
    """Drop the table from the database."""
    Base.metadata.drop_all(DB_Engine)


def test_get_institution_by_code_found():
    """Test getting an institution by code when it exists."""
    with SessionMaker() as session:
        repo = InstitutionRepository(session)
        institution = repo.get_institution_by_code("TU")
        assert institution is not None
        assert institution.name == "Test University"
        assert institution.code == "TU"


def test_get_institution_by_code_not_found():
    """Test getting an institution by code when it does not exist."""
    with SessionMaker() as session:
        repo = InstitutionRepository(session)
        institution = repo.get_institution_by_code("NONEXISTENT")
        assert institution is None
