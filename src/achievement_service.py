from abc import ABC, abstractmethod


class AchievementService(ABC):
    @abstractmethod
    def is_valid_action(self, action: str) -> bool:
        pass

    @abstractmethod
    def on_points_awarded(self, user_id: str, action: str, amount: int) -> None:
        pass
