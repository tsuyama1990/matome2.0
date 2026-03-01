
from src.services.base_service import BaseService


def test_base_service_initialization() -> None:
    service = BaseService()
    assert isinstance(service, BaseService)
