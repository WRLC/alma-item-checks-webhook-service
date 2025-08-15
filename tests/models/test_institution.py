"""Test suite for Institution model"""
from alma_item_checks_webhook_service.database import DB_Engine, SessionMaker
from alma_item_checks_webhook_service.models.base import Base
from alma_item_checks_webhook_service.models.institution import Institution


# noinspection PyUnusedLocal
def setup_module(module):
    """Create the table in the database."""
    Base.metadata.create_all(DB_Engine)


# noinspection PyUnusedLocal
def teardown_module(module):
    """Drop the table from the database."""
    Base.metadata.drop_all(DB_Engine)


def test_institution_creation():
    """Test that an Institution object can be created."""
    with SessionMaker() as session:
        institution = Institution(
            name="Test University", code="TU", api_key="test_api_key"
        )
        session.add(institution)
        session.commit()

        retrieved_institution = session.query(Institution).filter_by(code="TU").first()
        assert retrieved_institution is not None
        assert retrieved_institution.name == "Test University"
        assert retrieved_institution.api_key == "test_api_key"


def test_institution_repr():
    """Test the __repr__ method of the Institution model."""
    institution = Institution(
        name="Another University", code="AU", api_key="another_key"
    )
    assert repr(institution) == "<Institution(name='Another University', code='AU')>"
