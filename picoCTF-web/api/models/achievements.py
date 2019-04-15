"""Achievement models."""
from dataclasses import dataclass
import marshmallow.validate as validate
from marshmallow import Schema, fields, post_load


@dataclass
class Achievement():
    """
    An earnable achievement.

    Args:
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


class AchievementSchema(Schema):
    """Validation schema for :py:class:`Achievement`."""

    name = fields.Str(required=True)
    score = fields.Int(required=True, validate=validate.Range(min=0))
    event = fields.Str(required=True)
    description = fields.Str(required=True)
    processor = fields.Str(required=True)
    hidden = fields.Bool(required=True)
    image = fields.Str(required=True)
    smallimage = fields.Str(required=True)
    disabled = fields.Bool(required=True)
    multiple = fields.Bool(required=True)

    @post_load
    def make_achievement(self, data):
        """Return validated :py:class:`Achievement`s."""
        return Achievement(**data)
