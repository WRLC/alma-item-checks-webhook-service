"""Service class for Institution model"""
from sqlalchemy.orm import Session

from alma_item_checks_webhook_service.repos.institution_repo import InstitutionRepository
from alma_item_checks_webhook_service.models.institution import Institution


class InstitutionService:
    """Service class for Institution model"""
    def __init__(self, session: Session):
        self.repository = InstitutionRepository(session)

    def get_institution_by_code(self, code: str) -> Institution | None:
        """Get institution by code

        Args:
            code (str): The code of the institution
        Returns:
            Institution: The institution object
        """
        return self.repository.get_institution_by_code(code)
