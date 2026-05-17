import pytest
from unittest.mock import MagicMock, call

from src.exceptions import (
    InsufficientBalanceError,
    InvalidActionError,
    InvalidAmountError,
    UserNotFoundError,
)
from src.points_service import PointsService


class TestAwardPoints:
    def test_award_points_success(
        self, points_service, points_repository, user_repository, achievement_service
    ):
        # Arrange
        user_id = "user-1"
        action = "daily_login"
        amount = 50
        user_repository.exists.return_value = True
        achievement_service.is_valid_action.return_value = True
        points_repository.get_balance.return_value = 150

        # Act
        result = points_service.award_points(user_id, action, amount)

        # Assert
        assert result == 150
        points_repository.add_transaction.assert_called_once_with(
            user_id, action, amount, transaction_type="award"
        )
        achievement_service.on_points_awarded.assert_called_once_with(
            user_id, action, amount
        )

    def test_award_points_unknown_action_raises(
        self, points_service, user_repository, achievement_service, points_repository
    ):
        # Arrange
        user_repository.exists.return_value = True
        achievement_service.is_valid_action.return_value = False

        # Act / Assert
        with pytest.raises(InvalidActionError, match="Unknown action"):
            points_service.award_points("user-1", "invalid_action", 10)

        points_repository.add_transaction.assert_not_called()

    def test_award_points_negative_amount_raises(self, points_service, user_repository):
        # Arrange
        user_repository.exists.return_value = True

        # Act / Assert
        with pytest.raises(InvalidAmountError, match="greater than zero"):
            points_service.award_points("user-1", "daily_login", -5)

    def test_award_points_zero_amount_raises(self, points_service, user_repository):
        # Arrange
        user_repository.exists.return_value = True

        # Act / Assert
        with pytest.raises(InvalidAmountError):
            points_service.award_points("user-1", "daily_login", 0)

    def test_award_points_user_not_found_raises(
        self, points_service, user_repository, points_repository
    ):
        # Arrange
        user_repository.exists.return_value = False

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            points_service.award_points("missing-user", "daily_login", 10)

        points_repository.add_transaction.assert_not_called()

    def test_award_points_triggers_achievement_callback(
        self, points_service, user_repository, achievement_service, points_repository
    ):
        # Arrange
        user_repository.exists.return_value = True
        achievement_service.is_valid_action.return_value = True
        points_repository.get_balance.return_value = 100
        on_awarded = MagicMock()
        achievement_service.on_points_awarded = on_awarded

        # Act
        points_service.award_points("user-1", "complete_quiz", 25)

        # Assert
        on_awarded.assert_called_once_with("user-1", "complete_quiz", 25)


class TestRedeemPoints:
    def test_redeem_points_success(
        self, points_service, points_repository, user_repository
    ):
        # Arrange
        user_id = "user-1"
        amount = 30
        user_repository.exists.return_value = True
        points_repository.get_balance.side_effect = [100, 70]

        # Act
        result = points_service.redeem_points(user_id, amount)

        # Assert
        assert result == 70
        points_repository.add_transaction.assert_called_once_with(
            user_id, "redeem", -amount, transaction_type="redeem"
        )

    def test_redeem_points_insufficient_balance_raises(
        self, points_service, points_repository, user_repository
    ):
        # Arrange
        user_repository.exists.return_value = True
        points_repository.get_balance.return_value = 20

        # Act / Assert
        with pytest.raises(InsufficientBalanceError, match="Insufficient balance"):
            points_service.redeem_points("user-1", 50)

        points_repository.add_transaction.assert_not_called()

    def test_redeem_points_negative_amount_raises(self, points_service, user_repository):
        # Arrange
        user_repository.exists.return_value = True

        # Act / Assert
        with pytest.raises(InvalidAmountError):
            points_service.redeem_points("user-1", -10)

    def test_redeem_points_zero_amount_raises(self, points_service, user_repository):
        # Arrange
        user_repository.exists.return_value = True

        # Act / Assert
        with pytest.raises(InvalidAmountError):
            points_service.redeem_points("user-1", 0)

    def test_redeem_points_exact_balance_succeeds(
        self, points_service, points_repository, user_repository
    ):
        # Arrange
        user_repository.exists.return_value = True
        points_repository.get_balance.side_effect = [50, 0]

        # Act
        result = points_service.redeem_points("user-1", 50)

        # Assert
        assert result == 0
        points_repository.add_transaction.assert_called_once()

    def test_redeem_points_user_not_found_raises(
        self, points_service, user_repository, points_repository
    ):
        # Arrange
        user_repository.exists.return_value = False

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            points_service.redeem_points("ghost", 10)

        points_repository.add_transaction.assert_not_called()


class TestGetBalance:
    def test_get_balance_returns_repository_value(
        self, points_service, points_repository, user_repository
    ):
        # Arrange
        user_repository.exists.return_value = True
        points_repository.get_balance.return_value = 250

        # Act
        balance = points_service.get_balance("user-1")

        # Assert
        assert balance == 250
        points_repository.get_balance.assert_called_once_with("user-1")

    def test_get_balance_user_not_found_raises(self, points_service, user_repository):
        # Arrange
        user_repository.exists.return_value = False

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            points_service.get_balance("unknown")


class TestGetLevelByPoints:
    @pytest.mark.parametrize(
        "points,expected_level",
        [
            (0, "Bronze"),
            (99, "Bronze"),
            (100, "Silver"),
            (499, "Silver"),
            (500, "Gold"),
            (1999, "Gold"),
            (2000, "Platinum"),
            (10000, "Platinum"),
        ],
    )
    def test_get_level_by_points_thresholds(self, points_service, points, expected_level):
        # Arrange
        # (parametrized inputs)

        # Act
        level = points_service.get_level_by_points(points)

        # Assert
        assert level == expected_level

    def test_get_level_by_points_negative_raises(self, points_service):
        # Arrange
        negative_points = -1

        # Act / Assert
        with pytest.raises(InvalidAmountError):
            points_service.get_level_by_points(negative_points)


class TestGetPointsHistory:
    def test_get_points_history_returns_limited_entries(
        self, points_service, points_repository, user_repository
    ):
        # Arrange
        user_repository.exists.return_value = True
        expected_history = [
            {"action": "daily_login", "amount": 10},
            {"action": "complete_quiz", "amount": 50},
        ]
        points_repository.get_history.return_value = expected_history

        # Act
        history = points_service.get_points_history("user-1", limit=5)

        # Assert
        assert history == expected_history
        points_repository.get_history.assert_called_once_with("user-1", 5)

    def test_get_points_history_invalid_limit_raises(
        self, points_service, user_repository, points_repository
    ):
        # Arrange
        user_repository.exists.return_value = True

        # Act / Assert
        with pytest.raises(InvalidAmountError):
            points_service.get_points_history("user-1", limit=0)

        points_repository.get_history.assert_not_called()

    def test_get_points_history_user_not_found_raises(
        self, points_service, user_repository, points_repository
    ):
        # Arrange
        user_repository.exists.return_value = False

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            points_service.get_points_history("missing", limit=10)

        points_repository.get_history.assert_not_called()


class TestPointsServiceIntegrationWithMocks:
    def test_service_uses_stubbed_repositories(self):
        # Arrange
        points_repo = MagicMock()
        user_repo = MagicMock()
        achievement = MagicMock()
        user_repo.exists.return_value = True
        achievement.is_valid_action.return_value = True
        points_repo.get_balance.return_value = 0
        service = PointsService(points_repo, user_repo, achievement)

        # Act
        service.award_points("u1", "refer_friend", 100)

        # Assert
        assert points_repo.add_transaction.call_count == 1
        assert achievement.on_points_awarded.call_args == call("u1", "refer_friend", 100)

    def test_get_balance_does_not_call_achievement_service(
        self, points_service, user_repository, achievement_service, points_repository
    ):
        # Arrange
        user_repository.exists.return_value = True
        points_repository.get_balance.return_value = 42

        # Act
        points_service.get_balance("user-1")

        # Assert
        achievement_service.on_points_awarded.assert_not_called()
        achievement_service.is_valid_action.assert_not_called()
