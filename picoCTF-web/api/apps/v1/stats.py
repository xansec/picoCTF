"""Endpoints for getting statistical reports."""
import api
from api import block_before_competition, require_admin
from flask import jsonify
from flask_restplus import Namespace, Resource

from .schemas import scoreboard_search_req

ns = Namespace('stats', 'Statistical aggregations and reports')


@ns.route('/registration')
class RegistrationStatus(Resource):
    """Get information on user, team, and group registrations."""

    def get(self):
        """Get information on user, team, and group registrations."""
        return jsonify(api.stats.get_registration_count())


@ns.route('/scoreboard/search')
class ScoreboardPage(Resource):
    """Search team names and affiliation, return initial result scoreboard."""

    @block_before_competition
    @ns.response(200, 'Success')
    @ns.response(401, 'Must be logged in to retrieve groups board')
    @ns.response(422, 'Competition has not started')
    @ns.expect(scoreboard_search_req)
    def get(self):
        """Retrieve a page of a specific scoreboard."""
        req = scoreboard_search_req.parse_args(strict=True)
        # Strip chars: redis pattern wildcard and key delimiter
        pattern = req['pattern'].replace('*', '').replace('>', '')
        # At least 3 characters
        if len(pattern) < 3:
            return jsonify([])
        return jsonify(api.stats.search_scoreboard(
            board=req['board'], pattern=req['pattern'], page=req['page']
        ))


@ns.response(200, 'Success')
@ns.response(401, 'Not logged in')
@ns.response(403, 'Not authorized')
@ns.route('/submissions')
class SubmissionStatistics(Resource):
    """View submission statistics, broken down by problem."""

    @require_admin
    def get(self):
        """Get submission statistics, broken down by problem name."""
        return jsonify({
            p['name']: api.stats.get_problem_submission_stats(p['pid'])
            for p in api.problem.get_all_problems(show_disabled=True)
        })


@ns.response(200, 'Success')
@ns.response(401, 'Not logged in')
@ns.response(403, 'Not authorized')
@ns.route('/demographics')
class DemographicInformation(Resource):
    """Get demographic information used in analytics."""

    @require_admin
    def get(self):
        """Get demographic information used in analytics."""
        return jsonify(api.stats.get_demographic_data())
