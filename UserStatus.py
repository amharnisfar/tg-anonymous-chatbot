from enum import Enum

class UserStatus(Enum):
    """
    Represents the possible states a user can be in within the bot.
    """
    IDLE = 0
    IN_SEARCH = 1
    COUPLED = 2
    PARTNER_LEFT = 3
