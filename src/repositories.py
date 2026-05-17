from abc import ABC, abstractmethod
from typing import Any


class PointsRepository(ABC):
    @abstractmethod
    def get_balance(self, user_id: str) -> int:
        pass

    @abstractmethod
    def add_transaction(
        self, user_id: str, action: str, amount: int, transaction_type: str
    ) -> None:
        pass

    @abstractmethod
    def get_history(self, user_id: str, limit: int) -> list[dict[str, Any]]:
        pass


class UserRepository(ABC):
    @abstractmethod
    def exists(self, user_id: str) -> bool:
        pass
