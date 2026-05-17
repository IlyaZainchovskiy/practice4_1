from typing import Any

from src.achievement_service import AchievementService
from src.exceptions import (
    InsufficientBalanceError,
    InvalidActionError,
    InvalidAmountError,
    UserNotFoundError,
)
from src.repositories import PointsRepository, UserRepository

LEVEL_THRESHOLDS: list[tuple[int, str]] = [
    (2000, "Platinum"),
    (500, "Gold"),
    (100, "Silver"),
    (0, "Bronze"),
]


class PointsService:
    def __init__(
        self,
        points_repository: PointsRepository,
        user_repository: UserRepository,
        achievement_service: AchievementService,
    ) -> None:
        self._points_repository = points_repository
        self._user_repository = user_repository
        self._achievement_service = achievement_service

    def award_points(self, user_id: str, action: str, amount: int) -> int:
        self._ensure_user_exists(user_id)
        self._ensure_positive_amount(amount)
        if not self._achievement_service.is_valid_action(action):
            raise InvalidActionError(f"Unknown action: {action}")

        self._points_repository.add_transaction(
            user_id, action, amount, transaction_type="award"
        )
        self._achievement_service.on_points_awarded(user_id, action, amount)
        return self.get_balance(user_id)

    def redeem_points(self, user_id: str, amount: int) -> int:
        self._ensure_user_exists(user_id)
        self._ensure_positive_amount(amount)

        balance = self.get_balance(user_id)
        if balance < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance: have {balance}, need {amount}"
            )

        self._points_repository.add_transaction(
            user_id, "redeem", -amount, transaction_type="redeem"
        )
        return self.get_balance(user_id)

    def get_balance(self, user_id: str) -> int:
        self._ensure_user_exists(user_id)
        return self._points_repository.get_balance(user_id)

    def get_level_by_points(self, points: int) -> str:
        if points < 0:
            raise InvalidAmountError("Points cannot be negative for level calculation")

        for threshold, level in LEVEL_THRESHOLDS:
            if points >= threshold:
                return level
        raise RuntimeError("Level thresholds are misconfigured")

    def get_points_history(self, user_id: str, limit: int) -> list[dict[str, Any]]:
        self._ensure_user_exists(user_id)
        if limit <= 0:
            raise InvalidAmountError("History limit must be positive")
        return self._points_repository.get_history(user_id, limit)

    def _ensure_user_exists(self, user_id: str) -> None:
        if not self._user_repository.exists(user_id):
            raise UserNotFoundError(f"User not found: {user_id}")

    def _ensure_positive_amount(self, amount: int) -> None:
        if amount <= 0:
            raise InvalidAmountError("Amount must be greater than zero")
