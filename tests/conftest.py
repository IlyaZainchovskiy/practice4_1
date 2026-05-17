import pytest
from unittest.mock import MagicMock

from src.points_service import PointsService


@pytest.fixture
def points_repository():
    return MagicMock()


@pytest.fixture
def user_repository():
    return MagicMock()


@pytest.fixture
def achievement_service():
    return MagicMock()


@pytest.fixture
def points_service(points_repository, user_repository, achievement_service):
    return PointsService(points_repository, user_repository, achievement_service)
