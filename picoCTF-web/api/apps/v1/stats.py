"""Endpoints for getting statistical reports."""
from flask import jsonify
from flask_restplus import Namespace, Resource

from .schemas import scoreboard_req, top_teams_score_progression_req
import api.stats

ns = Namespace('stats', 'Statistical aggregations and reports')


@ns.route('/registration')
class RegistrationStatus(Resource):
    """Get information on user, team, and group registrations."""

    def get(self):
        """Get information on user, team, and group registrations."""
        return jsonify(api.stats.get_registration_count())


@ns.route('/scoreboard')
class Scoreboard(Resource):
    """Retrieve the scoreboard."""

    # @block_before_competition
    @ns.response(200, 'Success')
    @ns.response(422, 'Competition has not started')
    @ns.expect(scoreboard_req)
    def get(self):
        """Retrieve the scoreboard."""
        pass


@ns.route('/top_teams/score_progression')
class TopTeamsScoreProgressions(Resource):
    """Get score progressions for the top n teams, optionally filtered."""

    @ns.expect(top_teams_score_progression_req)
    def get(self):
        """Get score progressions for the top n teams, optionally filtered."""
        req = top_teams_score_progression_req.parse_args(strict=True)
        return jsonify(api.stats.get_top_teams_score_progressions(
            req['limit'], req['include_ineligible'], req['gid']
        ))
