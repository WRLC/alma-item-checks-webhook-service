"""Test suite for InstitutionService"""
from unittest.mock import Mock

from alma_item_checks_webhook_service.models.institution import Institution
from alma_item_checks_webhook_service.services.institution_service import InstitutionService


def test_get_institution_by_code(mocker):
    """Test the get_institution_by_code method of the InstitutionService."""
    # given
    mock_session = Mock()
    mock_repo = Mock()
    mocker.patch(
        "alma_item_checks_webhook_service.services.institution_service.InstitutionRepository",
        return_value=mock_repo,
    )

    expected_institution = Institution(name="Test University", code="TU", api_key="test_api_key")
    mock_repo.get_institution_by_code.return_value = expected_institution

    service = InstitutionService(mock_session)

    # when
    institution = service.get_institution_by_code("TU")

    # then
    mock_repo.get_institution_by_code.assert_called_once_with("TU")
    assert institution == expected_institution


def test_get_institution_by_code_not_found(mocker):
    """Test getting an institution by code when it does not exist."""
    # given
    mock_session = Mock()
    mock_repo = Mock()
    mocker.patch(
        "alma_item_checks_webhook_service.services.institution_service.InstitutionRepository",
        return_value=mock_repo,
    )

    mock_repo.get_institution_by_code.return_value = None

    service = InstitutionService(mock_session)

    # when
    institution = service.get_institution_by_code("NONEXISTENT")

    # then
    mock_repo.get_institution_by_code.assert_called_once_with("NONEXISTENT")
    assert institution is None
