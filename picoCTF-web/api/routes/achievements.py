"""Routing functions for /api/achievements."""
from flask import Blueprint

import api.achievement
import api.user
from api.annotations import jsonify, require_login
from api.common import WebSuccess

blueprint = Blueprint("achievements_api", __name__)


@blueprint.route('', methods=['GET'])
@require_login
@jsonify
def get_achievements_hook():
    """Get the achievements of the currently logged in user."""
    tid = api.user.get_team()["tid"]
    achievements = api.achievement.get_earned_achievements_display(tid=tid)

    for achievement in achievements:
        # JB : Hack to temporarily fix achievements timestamp problem
        achievement["timestamp"] = None

    return WebSuccess(data=achievements)
