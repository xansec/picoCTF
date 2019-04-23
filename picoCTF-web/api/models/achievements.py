"""Achievement models."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Achievement():
    """
    An earnable achievement.

    Args:
        id(int): ID for this achievement
        name(str): display name
        score(int): point value
        event(str): on what event hook to process
        description(str): achievement description
        processor(str): path to the processor file
        hidden(bool): whether this achievement is hidden
        image(str): path to achievement image
        smallimage(str): path to achievement thumbnail
        disabled(bool): whether this achievement is disabled
        multiple(bool): whether the achievement can be earned multiple times
    """

    id: int
    name: str
    score: int
    event: str
    description: str
    processor: str
    hidden: bool
    image: str
    smallimage: str
    disabled: bool
    multiple: bool


@dataclass
class EarnedAchievement():
    """
    An instance of an achievement earned by a player.

    Args:
        aid(int): ID of the achievement
        uid(int): ID of the user who earned the achievement
        timestamp(float): time the achievement was earned
        seen(bool): whether the user has seen the notification
    """

    aid: int
    uid: int
    timestamp: datetime
    seen: bool
