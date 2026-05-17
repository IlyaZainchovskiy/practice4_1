class PointsServiceError(Exception):
    """Base exception for points service errors."""


class UserNotFoundError(PointsServiceError):
    """Raised when the user does not exist."""


class InvalidActionError(PointsServiceError):
    """Raised when the action is not registered in the system."""


class InvalidAmountError(PointsServiceError):
    """Raised when amount is zero or negative."""


class InsufficientBalanceError(PointsServiceError):
    """Raised when redeem amount exceeds current balance."""
