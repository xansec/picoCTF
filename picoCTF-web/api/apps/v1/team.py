"""Endpoints related to the current user's team."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.team
import api.user

ns = Namespace('team', description="Information about the current user's team")


@ns.route('/')
class Team(Resource):
    """Get the current user's team."""

    # @require_login
    def get(self):
        """Get information about the current user's team."""
        current_tid = api.user.get_user()['tid']
        return jsonify(api.team.get_team_information(current_tid))


# @TODO doesn't make sense to return score in both /team an /team/score
@ns.route('/score')
class Score(Resource):
    """Get the current user's team's score."""

    # @require_login
    def get(self):
        """Get your team's score."""
        current_tid = api.user.get_user()['tid']
        return jsonify({
            'score': api.stats.get_score(current_tid)
        })

